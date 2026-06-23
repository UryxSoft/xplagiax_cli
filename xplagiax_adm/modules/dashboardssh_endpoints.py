from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
import psutil
from datetime import datetime, timedelta
from models.model import SSHSession, FileTransfer, SessionLog, Users_admin  # Agregado SessionLog
from utils.connections import db
from sqlalchemy import func

dashboardssh_bp = Blueprint('dashboardssh_bp', __name__)

@dashboardssh_bp.route('/')
@login_required
def index():
    """Renderizar página principal del dashboard de estadísticas"""
    return render_template('stats_dashboard.html')

@dashboardssh_bp.route('/api/stats')
@login_required
def get_stats():
    """Obtener estadísticas del sistema y usuario"""
    try:
        # Estadísticas del sistema
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Verificar si el disco existe antes de acceder
        try:
            disk = psutil.disk_usage('/')
        except:
            disk = None
        
        # Estadísticas del usuario - CORREGIDO: era SSHSession.query.all.count()
        total_sessions = SSHSession.query.filter_by(user_id=current_user.id).count()
        active_sessions = SSHSession.query.filter_by(user_id=current_user.id, is_active=True).count()
        
        # Transferencias recientes del usuario - CORREGIDO: agregando join con SSHSession
        recent_transfers = db.session.query(FileTransfer)\
            .join(SSHSession, FileTransfer.session_id == SSHSession.id)\
            .filter(SSHSession.user_id == current_user.id)\
            .order_by(FileTransfer.started_at.desc())\
            .limit(20).all()
        
        # Sesiones del usuario
        user_sessions = SSHSession.query.filter_by(
            user_id=current_user.id
        ).order_by(SSHSession.created_at.desc()).limit(15).all()
        
        # NUEVO: Estadísticas de comandos ejecutados (SessionLog)
        total_commands = db.session.query(SessionLog)\
            .join(SSHSession, SessionLog.session_id == SSHSession.id)\
            .filter(SSHSession.user_id == current_user.id)\
            .count()
            
        # NUEVO: Comandos recientes
        recent_commands = db.session.query(SessionLog)\
            .join(SSHSession, SessionLog.session_id == SSHSession.id)\
            .filter(SSHSession.user_id == current_user.id)\
            .order_by(SessionLog.timestamp.desc())\
            .limit(10).all()
        
        # NUEVO: Estadísticas de errores de comandos
        failed_commands = db.session.query(SessionLog)\
            .join(SSHSession, SessionLog.session_id == SSHSession.id)\
            .filter(
                SSHSession.user_id == current_user.id,
                SessionLog.exit_code != 0,
                SessionLog.exit_code.isnot(None)
            ).count()

        return jsonify({
            'status': 'success',
            'system': {
                'cpu': round(cpu_percent, 2),
                'memory': {
                    'percent': round(memory.percent, 2),
                    'used': memory.used,
                    'total': memory.total,
                    'available': memory.available
                },
                'disk': {
                    'percent': round((disk.used / disk.total) * 100, 2) if disk else 0,
                    'used': disk.used if disk else 0,
                    'total': disk.total if disk else 0,
                    'free': disk.free if disk else 0
                } if disk else None,
                'timestamp': datetime.now().isoformat()
            },
            'user': {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'total_commands': total_commands,  # NUEVO
                'failed_commands': failed_commands,  # NUEVO
                'command_success_rate': round(((total_commands - failed_commands) / total_commands * 100) if total_commands > 0 else 0, 2),  # NUEVO
                'recent_transfers': [transfer.to_dict() for transfer in recent_transfers],
                'sessions': [session.to_dict() for session in user_sessions],
                'recent_commands': [cmd.to_dict() for cmd in recent_commands]  # NUEVO
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@dashboardssh_bp.route('/api/system/detailed')
@login_required
def get_detailed_system_info():
    """Obtener información detallada del sistema"""
    try:
        # Información detallada del CPU
        cpu_info = {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'count_logical': psutil.cpu_count(logical=True),
            'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        # Información detallada de memoria
        memory_info = psutil.virtual_memory()._asdict()
        swap_info = psutil.swap_memory()._asdict()
        
        # Información de disco
        try:
            disk_info = psutil.disk_usage('/')._asdict()
        except:
            disk_info = None
        
        # Información de red
        try:
            net_info = psutil.net_io_counters()._asdict()
        except:
            net_info = None
        
        # Procesos principales
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] and pinfo['cpu_percent'] > 0:
                    processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Ordenar por CPU y tomar los top 10
        top_processes = sorted(processes, key=lambda x: x.get('cpu_percent', 0), reverse=True)[:10]
        
        return jsonify({
            'status': 'success',
            'system': {
                'cpu': cpu_info,
                'memory': memory_info,
                'swap': swap_info,
                'disk': disk_info,
                'network': net_info,
                'top_processes': top_processes,
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@dashboardssh_bp.route('/api/sessions/history')
@login_required
def get_sessions_history():
    """Obtener historial completo de sesiones del usuario"""
    try:
        sessions = SSHSession.query.filter_by(
            user_id=current_user.id
        ).order_by(SSHSession.created_at.desc()).all()
        
        return jsonify({
            'status': 'success',
            'sessions': [session.to_dict() for session in sessions],
            'total': len(sessions)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@dashboardssh_bp.route('/api/transfers/history')
@login_required
def get_transfers_history():
    """Obtener historial completo de transferencias del usuario"""
    try:
        # CORREGIDO: agregando join con SSHSession
        transfers = db.session.query(FileTransfer)\
            .join(SSHSession, FileTransfer.session_id == SSHSession.id)\
            .filter(SSHSession.user_id == current_user.id)\
            .order_by(FileTransfer.started_at.desc()).all()
        
        # Calcular estadísticas de transferencias
        total_transfers = len(transfers)
        successful_transfers = len([t for t in transfers if t.status == 'completed'])
        failed_transfers = len([t for t in transfers if t.status == 'failed'])
        total_size = sum([t.file_size for t in transfers if t.file_size])
        
        return jsonify({
            'status': 'success',
            'transfers': [transfer.to_dict() for transfer in transfers],
            'stats': {
                'total': total_transfers,
                'successful': successful_transfers,
                'failed': failed_transfers,
                'success_rate': round((successful_transfers / total_transfers * 100) if total_transfers > 0 else 0, 2),
                'total_size': total_size
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# NUEVO: Endpoint para historial de comandos
@dashboardssh_bp.route('/api/commands/history')
@login_required
def get_commands_history():
    """Obtener historial de comandos ejecutados por el usuario"""
    try:
        commands = db.session.query(SessionLog)\
            .join(SSHSession, SessionLog.session_id == SSHSession.id)\
            .filter(SSHSession.user_id == current_user.id)\
            .order_by(SessionLog.timestamp.desc()).all()
        
        # Estadísticas de comandos
        total_commands = len(commands)
        successful_commands = len([c for c in commands if c.exit_code == 0])
        failed_commands = len([c for c in commands if c.exit_code and c.exit_code != 0])
        
        # Comandos más utilizados
        command_counts = {}
        for cmd in commands:
            base_cmd = cmd.command.split()[0] if cmd.command else 'unknown'
            command_counts[base_cmd] = command_counts.get(base_cmd, 0) + 1
        
        top_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return jsonify({
            'status': 'success',
            'commands': [cmd.to_dict() for cmd in commands],
            'stats': {
                'total': total_commands,
                'successful': successful_commands,
                'failed': failed_commands,
                'success_rate': round((successful_commands / total_commands * 100) if total_commands > 0 else 0, 2),
                'top_commands': [{'command': cmd, 'count': count} for cmd, count in top_commands]
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@dashboardssh_bp.route('/api/user/dashboard')
@login_required
def get_user_dashboard():
    """Obtener datos completos del dashboard del usuario"""
    try:
        # Sesiones por estado
        sessions_by_status = db.session.query(
            SSHSession.is_active,
            func.count(SSHSession.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(SSHSession.is_active).all()
        
        # Transferencias por estado
        transfers_by_status = db.session.query(
            FileTransfer.status,
            func.count(FileTransfer.id).label('count')
        ).join(SSHSession, FileTransfer.session_id == SSHSession.id)\
         .filter(SSHSession.user_id == current_user.id)\
         .group_by(FileTransfer.status).all()
        
        # NUEVO: Comandos por día (últimos 30 días)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        daily_activity = db.session.query(
            func.date(SSHSession.created_at).label('date'),
            func.count(SSHSession.id).label('sessions'),
            func.count(SessionLog.id).label('commands')
        ).outerjoin(SessionLog, SSHSession.id == SessionLog.session_id)\
         .filter(
            SSHSession.user_id == current_user.id,
            SSHSession.created_at >= thirty_days_ago
        ).group_by(func.date(SSHSession.created_at)).all()
        
        # NUEVO: Actividad de comandos por estado de salida
        commands_by_exit_code = db.session.query(
            SessionLog.exit_code,
            func.count(SessionLog.id).label('count')
        ).join(SSHSession, SessionLog.session_id == SSHSession.id)\
         .filter(SSHSession.user_id == current_user.id)\
         .group_by(SessionLog.exit_code).all()
        
        return jsonify({
            'status': 'success',
            'user_stats': {
                'sessions_by_status': [
                    {'status': 'active' if s.is_active else 'inactive', 'count': s.count}
                    for s in sessions_by_status
                ],
                'transfers_by_status': [
                    {'status': t.status, 'count': t.count}
                    for t in transfers_by_status
                ],
                'commands_by_exit_code': [  # NUEVO
                    {'exit_code': c.exit_code, 'count': c.count}
                    for c in commands_by_exit_code
                ],
                'daily_activity': [
                    {
                        'date': str(d.date),
                        'sessions': d.sessions,
                        'commands': d.commands or 0  # NUEVO
                    }
                    for d in daily_activity
                ]
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@dashboardssh_bp.errorhandler(404)
def not_found(error):
    """Manejo de errores 404"""
    return jsonify({
        'status': 'error',
        'message': 'Recurso no encontrado'
    }), 404

@dashboardssh_bp.errorhandler(500)
def internal_error(error):
    """Manejo de errores 500"""
    return jsonify({
        'status': 'error',
        'message': 'Error interno del servidor'
    }), 500