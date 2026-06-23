from flask import Flask, request, jsonify, Blueprint, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, Enum as SQLEnum
from flask_login import current_user
from settings.connections import db
import os
import shutil
import threading
import time
from datetime import datetime, timedelta
import logging
from enum import Enum
import json
from modules.models.model import Users

x_cleanup = Blueprint('x_cleanup', __name__)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enums para estados
class CleanupStatus(Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class ConfigKey(Enum):
    AUTO_CLEANUP_ENABLED = "auto_cleanup_enabled"
    CLEANUP_DELAY_MINUTES = "cleanup_delay_minutes"
    DRY_RUN = "dry_run"
    PRESERVE_PATTERNS = "preserve_patterns"

# Modelos corregidos
class CleanupConfig(db.Model):
    __tablename__ = 'cleanup_config'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)
    config_value = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CleanupConfig {self.config_key}: {self.config_value}>'

class CleanupTask(db.Model):
    __tablename__ = 'cleanup_tasks'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    folder_path = db.Column(db.String(500), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    delay_minutes = db.Column(db.Integer, nullable=False)
    status = db.Column(SQLEnum('scheduled', 'completed', 'cancelled', 'failed', name='cleanup_status'), default='scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    executed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    dry_run = db.Column(db.Boolean, default=False)
    
    # Relación con Users
    user = db.relationship('Users', backref=db.backref('cleanup_tasks', lazy=True))
    
    def __repr__(self):
        return f'<CleanupTask {self.folder_path}: {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'folder_path': self.folder_path,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'delay_minutes': self.delay_minutes,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'error_message': self.error_message,
            'dry_run': self.dry_run
        }

class CleanupHistory(db.Model):
    __tablename__ = 'cleanup_history'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('cleanup_tasks.id'))
    folder_path = db.Column(db.String(500), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('Users', backref=db.backref('cleanup_history', lazy=True))
    task = db.relationship('CleanupTask', backref=db.backref('history', lazy=True))
    
    def __repr__(self):
        return f'<CleanupHistory {self.action}: {self.folder_path}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'task_id': self.task_id,
            'folder_path': self.folder_path,
            'action': self.action,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class FolderCleanupManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FolderCleanupManager, cls).__new__(cls)
            # Inicializar atributos aquí para asegurar que se ejecuten una sola vez
            cls._instance.cleanup_timers = {}
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Solo inicializar una vez
        if not getattr(self, '_initialized', False):
            if not hasattr(self, 'cleanup_timers'):
                self.cleanup_timers = {}
            self._initialized = True
    
    def _ensure_app_context(self):
        """Ensures we're working within an application context"""
        if not current_app:
            raise RuntimeError("This operation requires an active Flask application context")
    
    def _init_default_config(self):
        """Inicializa configuración por defecto si no existe"""
        self._ensure_app_context()
        
        try:
            default_configs = {
                ConfigKey.AUTO_CLEANUP_ENABLED.value: "false",
                ConfigKey.CLEANUP_DELAY_MINUTES.value: "60",
                ConfigKey.DRY_RUN.value: "false",
                ConfigKey.PRESERVE_PATTERNS.value: json.dumps([".log", ".config"])
            }
            
            for key, value in default_configs.items():
                existing = CleanupConfig.query.filter_by(config_key=key).first()
                if not existing:
                    config = CleanupConfig(config_key=key, config_value=value)
                    db.session.add(config)
            
            db.session.commit()
            logger.info("Configuración por defecto inicializada")
            
        except Exception as e:
            logger.error(f"Error inicializando configuración: {e}")
            db.session.rollback()
    
    def ensure_initialized(self):
        """Ensures the manager is properly initialized with default config"""
        if not hasattr(self, '_config_initialized'):
            self._init_default_config()
            self._config_initialized = True
    
    def get_config(self, key=None):
        """Obtiene configuración desde la base de datos"""
        self._ensure_app_context()
        self.ensure_initialized()
        
        try:
            if key:
                config = CleanupConfig.query.filter_by(config_key=key).first()
                if config:
                    # Convertir valores según el tipo
                    if key in [ConfigKey.AUTO_CLEANUP_ENABLED.value, ConfigKey.DRY_RUN.value]:
                        return config.config_value.lower() == 'true'
                    elif key == ConfigKey.CLEANUP_DELAY_MINUTES.value:
                        return int(config.config_value)
                    elif key == ConfigKey.PRESERVE_PATTERNS.value:
                        try:
                            return json.loads(config.config_value)
                        except:
                            return []
                    else:
                        return config.config_value
                return None
            else:
                # Obtener toda la configuración
                configs = CleanupConfig.query.all()
                result = {}
                for config in configs:
                    if config.config_key in [ConfigKey.AUTO_CLEANUP_ENABLED.value, ConfigKey.DRY_RUN.value]:
                        result[config.config_key] = config.config_value.lower() == 'true'
                    elif config.config_key == ConfigKey.CLEANUP_DELAY_MINUTES.value:
                        result[config.config_key] = int(config.config_value)
                    elif config.config_key == ConfigKey.PRESERVE_PATTERNS.value:
                        try:
                            result[config.config_key] = json.loads(config.config_value)
                        except:
                            result[config.config_key] = []
                    else:
                        result[config.config_key] = config.config_value
                return result
                
        except Exception as e:
            logger.error(f"Error obteniendo configuración: {e}")
            return None if key else {}
    
    def update_config(self, updates):
        """Actualiza configuración en la base de datos"""
        self._ensure_app_context()
        self.ensure_initialized()
        
        try:
            for key, value in updates.items():
                if key not in [e.value for e in ConfigKey]:
                    continue
                
                config = CleanupConfig.query.filter_by(config_key=key).first()
                
                # Convertir valor a string para almacenar
                if isinstance(value, bool):
                    str_value = str(value).lower()
                elif isinstance(value, (list, dict)):
                    str_value = json.dumps(value)
                else:
                    str_value = str(value)
                
                if config:
                    config.config_value = str_value
                    config.updated_at = datetime.utcnow()
                else:
                    config = CleanupConfig(config_key=key, config_value=str_value)
                    db.session.add(config)
            
            db.session.commit()
            logger.info(f"Configuración actualizada: {list(updates.keys())}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando configuración: {e}")
            db.session.rollback()
            return False
    
    def _resolve_path(self, folder_path):
        """Resuelve una ruta a su forma absoluta correcta"""
        try:
            # Si ya es absoluta y existe, devolverla
            if os.path.isabs(folder_path) and os.path.exists(folder_path):
                return folder_path
            
            # Si es absoluta pero no existe, intentar como relativa
            if os.path.isabs(folder_path):
                # Extraer la parte relativa común
                if 'xplagiax_appcli/' in folder_path:
                    relative_part = folder_path.split('xplagiax_appcli/')[-1]
                else:
                    relative_part = folder_path.lstrip('/')
            else:
                relative_part = folder_path.lstrip('/')
            
            # Construir ruta absoluta desde la raíz de la app
            app_root = current_app.root_path
            absolute_path = os.path.join(app_root, relative_part)
            return os.path.normpath(absolute_path)
        except Exception as e:
            logger.error(f"Error resolviendo ruta {folder_path}: {e}")
            return folder_path
    
    def _get_current_user_id(self):
        """Obtiene el ID del usuario actual"""
        try:
            if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                return current_user.id
            else:
                # Si no hay usuario autenticado, buscar el primer usuario como fallback
                first_user = Users.query.first()
                if first_user:
                    return first_user.id
                else:
                    raise RuntimeError("No hay usuarios disponibles en el sistema")
        except Exception as e:
            logger.error(f"Error obteniendo usuario actual: {e}")
            raise RuntimeError(f"Error de autenticación: {str(e)}")
    
    def schedule_cleanup(self, folder_path, delay_minutes=None, user_id=None):
        """Programa la eliminación de una carpeta"""
        self._ensure_app_context()
        self.ensure_initialized()
        
        try:
            if delay_minutes is None:
                delay_minutes = self.get_config(ConfigKey.CLEANUP_DELAY_MINUTES.value) or 60
            
            # Si no se proporciona user_id, usar el usuario actual
            if user_id is None:
                user_id = self._get_current_user_id()
            
            # Validar usuario
            user = Users.query.get(user_id)
            if not user:
                return False, f"Usuario con ID {user_id} no encontrado"
            
            # Resolver la ruta correcta
            resolved_path = self._resolve_path(folder_path)
            
            if not os.path.exists(resolved_path):
                return False, f"La carpeta {resolved_path} no existe. Ruta original: {folder_path}"
            
            # Cancelar tarea anterior si existe
            self._cancel_timer(resolved_path)
            
            # Crear tarea en base de datos
            scheduled_time = datetime.utcnow() + timedelta(minutes=delay_minutes)
            dry_run = self.get_config(ConfigKey.DRY_RUN.value) or False
            
            task = CleanupTask(
                folder_path=resolved_path,
                scheduled_time=scheduled_time,
                delay_minutes=delay_minutes,
                dry_run=dry_run,
                status=CleanupStatus.SCHEDULED.value,
                user_id=user_id
            )
            db.session.add(task)
            db.session.commit()
            
            # Crear entrada en historial
            history = CleanupHistory(
                task_id=task.id,
                folder_path=resolved_path,
                action='scheduled',
                details=f'Programada para {scheduled_time} (en {delay_minutes} minutos)',
                user_id=user_id
            )
            db.session.add(history)
            db.session.commit()
            
            # Programar timer
            timer = threading.Timer(delay_minutes * 60, self._execute_cleanup, [task.id])
            
            # Asegurar que cleanup_timers existe
            if not hasattr(self, 'cleanup_timers'):
                self.cleanup_timers = {}
                
            self.cleanup_timers[resolved_path] = {
                'timer': timer,
                'task_id': task.id
            }
            timer.start()
            
            logger.info(f"Limpieza programada para {resolved_path} (ID: {task.id}) a las {scheduled_time}")
            
            return True, f"Limpieza programada para {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}"
            
        except Exception as e:
            logger.error(f"Error programando limpieza: {e}")
            db.session.rollback()
            return False, f"Error interno: {str(e)}"
    
    def _execute_cleanup(self, task_id):
        """Ejecuta la limpieza de la carpeta"""
        # Note: This method runs in a separate thread, so it needs its own app context
        with current_app.app_context():
            try:
                task = CleanupTask.query.get(task_id)
                if not task:
                    logger.error(f"Tarea {task_id} no encontrada")
                    return
                
                folder_path = task.folder_path
                
                # Asegurar que cleanup_timers existe
                if not hasattr(self, 'cleanup_timers'):
                    self.cleanup_timers = {}
                
                # Remover timer de la lista activa
                if folder_path in self.cleanup_timers:
                    del self.cleanup_timers[folder_path]
                
                if task.dry_run:
                    # Modo simulación
                    task.status = CleanupStatus.COMPLETED.value
                    task.executed_at = datetime.utcnow()
                    
                    history = CleanupHistory(
                        task_id=task_id,
                        folder_path=folder_path,
                        action='executed',
                        details='[DRY RUN] Simulación de eliminación completada',
                        user_id=task.user_id
                    )
                    db.session.add(history)
                    db.session.commit()
                    
                    logger.info(f"[DRY RUN] Se eliminaría la carpeta: {folder_path}")
                    return
                
                if os.path.exists(folder_path):
                    # Eliminar carpeta
                    shutil.rmtree(folder_path)
                    
                    task.status = CleanupStatus.COMPLETED.value
                    task.executed_at = datetime.utcnow()
                    
                    history = CleanupHistory(
                        task_id=task_id,
                        folder_path=folder_path,
                        action='executed',
                        details='Carpeta eliminada exitosamente',
                        user_id=task.user_id
                    )
                    
                    logger.info(f"Carpeta eliminada exitosamente: {folder_path}")
                    
                else:
                    task.status = CleanupStatus.FAILED.value
                    task.executed_at = datetime.utcnow()
                    task.error_message = "La carpeta ya no existe"
                    
                    history = CleanupHistory(
                        task_id=task_id,
                        folder_path=folder_path,
                        action='failed',
                        details='La carpeta ya no existe',
                        user_id=task.user_id
                    )
                    
                    logger.warning(f"La carpeta ya no existe: {folder_path}")
                
                db.session.add(history)
                db.session.commit()
                    
            except Exception as e:
                logger.error(f"Error eliminando carpeta (tarea {task_id}): {e}")
                
                try:
                    task = CleanupTask.query.get(task_id)
                    if task:
                        task.status = CleanupStatus.FAILED.value
                        task.executed_at = datetime.utcnow()
                        task.error_message = str(e)
                        
                        history = CleanupHistory(
                            task_id=task_id,
                            folder_path=task.folder_path,
                            action='failed',
                            details=f'Error: {str(e)}',
                            user_id=task.user_id
                        )
                        db.session.add(history)
                        db.session.commit()
                except Exception as save_error:
                    logger.error(f"Error guardando fallo de tarea: {save_error}")
                    db.session.rollback()
    
    def cancel_cleanup(self, folder_path, user_id=None):
        """Cancela la limpieza programada de una carpeta"""
        self._ensure_app_context()
        
        try:
            # Si no se proporciona user_id, usar el usuario actual
            if user_id is None:
                user_id = self._get_current_user_id()
            
            # Validar usuario
            user = Users.query.get(user_id)
            if not user:
                return False, f"Usuario con ID {user_id} no encontrado"
            
            # Resolver la ruta
            resolved_path = self._resolve_path(folder_path)
            
            # Cancelar timer si existe
            cancelled_timer = self._cancel_timer(resolved_path)
            
            if cancelled_timer:
                task_id = cancelled_timer['task_id']
                
                # Actualizar tarea en base de datos
                task = CleanupTask.query.get(task_id)
                if task and task.status == CleanupStatus.SCHEDULED.value:
                    # Verificar que el usuario tiene permisos (si se proporciona user_id)
                    if user_id and task.user_id and task.user_id != user_id:
                        return False, "No tienes permisos para cancelar esta tarea"
                    
                    task.status = CleanupStatus.CANCELLED.value
                    
                    history = CleanupHistory(
                        task_id=task_id,
                        folder_path=resolved_path,
                        action='cancelled',
                        details='Cancelada por solicitud del usuario',
                        user_id=user_id or task.user_id
                    )
                    db.session.add(history)
                    db.session.commit()
                    
                    logger.info(f"Limpieza cancelada para: {resolved_path}")
                    return True, "Limpieza cancelada exitosamente"
            
            return False, "No hay limpieza programada para esta carpeta"
            
        except Exception as e:
            logger.error(f"Error cancelando limpieza: {e}")
            db.session.rollback()
            return False, f"Error interno: {str(e)}"
    
    def _cancel_timer(self, folder_path):
        """Cancela el timer para una carpeta específica"""
        # Asegurar que cleanup_timers existe
        if not hasattr(self, 'cleanup_timers'):
            self.cleanup_timers = {}
            
        if folder_path in self.cleanup_timers:
            timer_info = self.cleanup_timers[folder_path]
            timer_info['timer'].cancel()
            del self.cleanup_timers[folder_path]
            return timer_info
        return None
    
    def get_scheduled_cleanups(self, user_id=None):
        """Obtiene las limpiezas programadas"""
        self._ensure_app_context()
        
        try:
            query = CleanupTask.query.filter_by(status=CleanupStatus.SCHEDULED.value)
            
            # Si no se proporciona user_id, usar el usuario actual
            if user_id is None:
                user_id = self._get_current_user_id()
            
            # Filtrar por usuario
            user = Users.query.get(user_id)
            if not user:
                logger.warning(f"Usuario con ID {user_id} no encontrado")
                return []
            
            query = query.filter_by(user_id=user_id)
            
            scheduled_tasks = query.all()
            return [task.to_dict() for task in scheduled_tasks]
        except Exception as e:
            logger.error(f"Error obteniendo tareas programadas: {e}")
            return []
    
    def get_cleanup_history(self, limit=50, user_id=None):
        """Obtiene el historial de limpiezas"""
        self._ensure_app_context()
        
        try:
            query = CleanupHistory.query.order_by(CleanupHistory.timestamp.desc())
            
            # Si no se proporciona user_id, usar el usuario actual
            if user_id is None:
                user_id = self._get_current_user_id()
            
            # Filtrar por usuario
            user = Users.query.get(user_id)
            if not user:
                logger.warning(f"Usuario con ID {user_id} no encontrado")
                return []
            
            query = query.filter_by(user_id=user_id)
            
            history = query.limit(limit).all()
            return [entry.to_dict() for entry in history]
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []

# Global instance - will be lazily initialized
cleanup_manager = None

def get_cleanup_manager():
    """Factory function to get the cleanup manager instance"""
    global cleanup_manager
    if cleanup_manager is None:
        cleanup_manager = FolderCleanupManager()
        # Asegurar que los atributos estén inicializados
        if not hasattr(cleanup_manager, 'cleanup_timers'):
            cleanup_manager.cleanup_timers = {}
        if not hasattr(cleanup_manager, '_initialized'):
            cleanup_manager._initialized = True
    return cleanup_manager

@x_cleanup.route('/api/cleanup/schedule', methods=['POST'])
def schedule_folder_cleanup():
    """Programa la eliminación de una carpeta"""
    try:
        data = request.get_json()
        
        if not data or 'folder_path' not in data:
            return jsonify({
                'success': False,
                'message': 'folder_path es requerido'
            }), 400
        
        folder_path = data['folder_path']
        delay_minutes = data.get('delay_minutes')
        user_id = data.get('user_id')
        
        manager = get_cleanup_manager()
        
        success, message = manager.schedule_cleanup(folder_path, delay_minutes, user_id)
        
        if not success:
            if "no existe" in message:
                return jsonify({
                    'success': False,
                    'message': message,
                    'suggestion': f'Intenta usar la ruta relativa: {folder_path.split("xplagiax_appcli/")[-1] if "xplagiax_appcli/" in folder_path else folder_path.lstrip("/")}'
                }), 404
            else:
                return jsonify({
                    'success': False,
                    'message': message
                }), 400
        
        resolved_path = manager._resolve_path(folder_path)
        effective_user_id = user_id or manager._get_current_user_id()
        
        return jsonify({
            'success': success,
            'message': message,
            'folder_path': folder_path,
            'resolved_path': resolved_path,
            'delay_minutes': delay_minutes or manager.get_config(ConfigKey.CLEANUP_DELAY_MINUTES.value),
            'user_id': effective_user_id
        })
        
    except Exception as e:
        logger.error(f"Error programando limpieza: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@x_cleanup.route('/api/cleanup/cancel', methods=['POST'])
def cancel_folder_cleanup():
    """Cancela la limpieza programada de una carpeta"""
    try:
        data = request.get_json()
        
        if not data or 'folder_path' not in data:
            return jsonify({
                'success': False,
                'message': 'folder_path es requerido'
            }), 400
        
        folder_path = data['folder_path']
        user_id = data.get('user_id')
        
        manager = get_cleanup_manager()
        
        success, message = manager.cancel_cleanup(folder_path, user_id)
        
        resolved_path = manager._resolve_path(folder_path)
        effective_user_id = user_id or manager._get_current_user_id()
        
        return jsonify({
            'success': success,
            'message': message,
            'folder_path': folder_path,
            'resolved_path': resolved_path,
            'user_id': effective_user_id
        })
        
    except Exception as e:
        logger.error(f"Error cancelando limpieza: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@x_cleanup.route('/api/cleanup/status', methods=['GET'])
def get_cleanup_status():
    """Obtiene el estado de las limpiezas programadas"""
    try:
        user_id = request.args.get('user_id', type=int)
        
        manager = get_cleanup_manager()
        scheduled = manager.get_scheduled_cleanups(user_id)
        config = manager.get_config()
        
        effective_user_id = user_id or manager._get_current_user_id()
        
        return jsonify({
            'success': True,
            'scheduled_cleanups': scheduled,
            'config': config,
            'user_id': effective_user_id
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@x_cleanup.route('/api/cleanup/config', methods=['GET', 'POST'])
def manage_cleanup_config():
    """Obtiene o actualiza la configuración de limpieza"""
    try:
        manager = get_cleanup_manager()
        
        if request.method == 'GET':
            config = manager.get_config()
            return jsonify({
                'success': True,
                'config': config
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Datos de configuración requeridos'
                }), 400
            
            if manager.update_config(data):
                updated_config = manager.get_config()
                return jsonify({
                    'success': True,
                    'message': 'Configuración actualizada exitosamente',
                    'config': updated_config
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Error guardando configuración'
                }), 500
                
    except Exception as e:
        logger.error(f"Error manejando configuración: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@x_cleanup.route('/api/cleanup/history', methods=['GET'])
def get_cleanup_history():
    """Obtiene el historial de limpiezas"""
    try:
        limit = request.args.get('limit', 50, type=int)
        user_id = request.args.get('user_id', type=int)
        
        manager = get_cleanup_manager()
        history = manager.get_cleanup_history(limit, user_id)
        
        effective_user_id = user_id or manager._get_current_user_id()
        
        return jsonify({
            'success': True,
            'history': history,
            'user_id': effective_user_id
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500

@x_cleanup.route('/api/cleanup/immediate', methods=['POST'])
def immediate_cleanup():
    """Elimina una carpeta inmediatamente"""
    try:
        data = request.get_json()
        
        if not data or 'folder_path' not in data:
            return jsonify({
                'success': False,
                'message': 'folder_path es requerido'
            }), 400
        
        folder_path = data['folder_path']
        user_id = data.get('user_id')
        
        manager = get_cleanup_manager()
        
        # Si no se proporciona user_id, usar el usuario actual
        if user_id is None:
            user_id = manager._get_current_user_id()
        
        # Validar usuario
        user = Users.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': f'Usuario con ID {user_id} no encontrado'
            }), 404
        
        resolved_path = manager._resolve_path(folder_path)
        
        if not os.path.exists(resolved_path):
            return jsonify({
                'success': False,
                'message': f'La carpeta {resolved_path} no existe'
            }), 404
        
        # Crear tarea inmediata
        dry_run = manager.get_config(ConfigKey.DRY_RUN.value) or False
        
        task = CleanupTask(
            folder_path=resolved_path,
            scheduled_time=datetime.utcnow(),
            delay_minutes=0,
            dry_run=dry_run,
            status=CleanupStatus.SCHEDULED.value,
            user_id=user_id
        )
        db.session.add(task)
        db.session.commit()
        
        # Ejecutar inmediatamente
        manager._execute_cleanup(task.id)
        
        # Obtener resultado actualizado
        db.session.refresh(task)
        
        return jsonify({
            'success': task.status == CleanupStatus.COMPLETED.value,
            'message': task.error_message if task.status == CleanupStatus.FAILED.value else 'Eliminación completada',
            'folder_path': folder_path,
            'resolved_path': resolved_path,
            'task_id': task.id,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Error en limpieza inmediata: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500


# Funciones de utilidad para inicializar las tablas
def init_cleanup_system():
    """Inicializa completamente el sistema de limpieza"""
    try:
        with current_app.app_context():
            # Limpiar metadata existente para evitar conflictos
            if 'cleanup_config' in db.metadata.tables:
                db.metadata.remove(db.metadata.tables['cleanup_config'])
            if 'cleanup_tasks' in db.metadata.tables:
                db.metadata.remove(db.metadata.tables['cleanup_tasks'])
            if 'cleanup_history' in db.metadata.tables:
                db.metadata.remove(db.metadata.tables['cleanup_history'])
            
            # Crear las tablas si no existen
            db.create_all()
            
            # Inicializar el manager
            manager = get_cleanup_manager()
            
            # Asegurar que todos los atributos estén inicializados
            if not hasattr(manager, 'cleanup_timers'):
                manager.cleanup_timers = {}
            if not hasattr(manager, '_initialized'):
                manager._initialized = True
            if not hasattr(manager, '_config_initialized'):
                manager._config_initialized = False
            
            # Inicializar configuración por defecto
            manager.ensure_initialized()
            
            logger.info("Sistema de limpieza inicializado exitosamente")
            return True
    except Exception as e:
        logger.error(f"Error inicializando sistema de limpieza: {e}")
        return False

def create_cleanup_tables():
    """Crea las tablas necesarias para el sistema de limpieza"""
    return init_cleanup_system()


# Endpoint adicional para verificar rutas
@x_cleanup.route('/api/cleanup/verify-path', methods=['POST'])
def verify_folder_path():
    """Verifica si una ruta de carpeta existe"""
    try:
        data = request.get_json()
        
        if not data or 'folder_path' not in data:
            return jsonify({
                'success': False,
                'message': 'folder_path es requerido'
            }), 400
        
        folder_path = data['folder_path']
        manager = get_cleanup_manager()
        resolved_path = manager._resolve_path(folder_path)
        
        exists = os.path.exists(resolved_path)
        is_directory = os.path.isdir(resolved_path) if exists else False
        
        result = {
            'success': True,
            'exists': exists,
            'is_directory': is_directory,
            'original_path': folder_path,
            'resolved_path': resolved_path
        }
        
        if exists and is_directory:
            try:
                # Obtener información adicional de la carpeta
                stats = os.stat(resolved_path)
                file_count = len([f for f in os.listdir(resolved_path) if os.path.isfile(os.path.join(resolved_path, f))])
                dir_count = len([d for d in os.listdir(resolved_path) if os.path.isdir(os.path.join(resolved_path, d))])
                
                result.update({
                    'size_bytes': stats.st_size,
                    'modified_time': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    'file_count': file_count,
                    'directory_count': dir_count
                })
            except Exception as info_error:
                logger.warning(f"Error obteniendo información de carpeta: {info_error}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error verificando ruta: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500


# Endpoint para obtener estadísticas del sistema
@x_cleanup.route('/api/cleanup/stats', methods=['GET'])
def get_cleanup_stats():
    """Obtiene estadísticas del sistema de limpieza"""
    try:
        user_id = request.args.get('user_id', type=int)
        manager = get_cleanup_manager()
        
        # Si no se proporciona user_id, usar el usuario actual
        if user_id is None:
            user_id = manager._get_current_user_id()
        
        # Validar usuario
        user = Users.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': f'Usuario con ID {user_id} no encontrado'
            }), 404
        
        # Obtener estadísticas
        total_tasks = CleanupTask.query.filter_by(user_id=user_id).count()
        completed_tasks = CleanupTask.query.filter_by(
            user_id=user_id, 
            status=CleanupStatus.COMPLETED.value
        ).count()
        failed_tasks = CleanupTask.query.filter_by(
            user_id=user_id, 
            status=CleanupStatus.FAILED.value
        ).count()
        scheduled_tasks = CleanupTask.query.filter_by(
            user_id=user_id, 
            status=CleanupStatus.SCHEDULED.value
        ).count()
        cancelled_tasks = CleanupTask.query.filter_by(
            user_id=user_id, 
            status=CleanupStatus.CANCELLED.value
        ).count()
        
        # Tareas completadas hoy
        today = datetime.now().date()
        completed_today = CleanupTask.query.filter(
            CleanupTask.user_id == user_id,
            CleanupTask.status == CleanupStatus.COMPLETED.value,
            CleanupTask.executed_at >= today
        ).count()
        
        # Última actividad
        last_task = CleanupTask.query.filter_by(user_id=user_id).order_by(
            CleanupTask.created_at.desc()
        ).first()
        
        stats = {
            'success': True,
            'user_id': user_id,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'scheduled_tasks': scheduled_tasks,
            'cancelled_tasks': cancelled_tasks,
            'completed_today': completed_today,
            'success_rate': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2),
            'last_activity': last_task.created_at.isoformat() if last_task else None,
            'active_timers': len(getattr(manager, 'cleanup_timers', {}))
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500