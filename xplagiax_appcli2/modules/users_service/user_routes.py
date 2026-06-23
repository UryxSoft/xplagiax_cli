"""
Copyright (c) 2024 - present URYX TECHNOLOGIES SRL
"""
import os
from flask import Blueprint, render_template, redirect, url_for, session, jsonify, flash, request, make_response
from flask_login import current_user, login_required
from settings.utilities import verify_token
from modules.models.model import Users, DocumentAnalysis, ClassifiedParagraph,UserPreference
from settings.forein import ComplementsGetter
from datetime import datetime, timedelta
from sqlalchemy import desc, func
import logging
from functools import wraps
from settings.connections import db 

x_users = Blueprint('x_users', __name__)

# Configura el logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('x_users')

# Inicializar MinioClient
from modules.bucket_service.seaweedfs_storage import SeaweedFSClient

# Configuración SeaweedFS
SEAWEEDFS_FILER_URL = os.environ.get('SEAWEEDFS_FILER_URL', 'http://localhost:8333')
SEAWEEDFS_MASTER_URL = os.environ.get('SEAWEEDFS_MASTER_URL', 'http://localhost:8333')
SEAWEEDFS_BUCKET = os.environ.get('SEAWEEDFS_BUCKET', 'xplagiax-users-documents')

# Crear instancia de SeaweedFSClient
minio_client = SeaweedFSClient(
    filer_url=SEAWEEDFS_FILER_URL,
    master_url=SEAWEEDFS_MASTER_URL,
    bucket_name=SEAWEEDFS_BUCKET
)

def block_starter(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type == 'Starter':
            # Si es Starter, no puede entrar a /documents
            return redirect(url_for('x_users.home'))
        return f(*args, **kwargs)
    return decorated_function

def get_user_data():
    """Obtiene los datos del usuario autenticado actual - VERSIÓN ROBUSTA"""
    from flask_login import current_user
    
    if not current_user or not current_user.is_authenticated:
        print("❌ get_user_data: Usuario no autenticado")
        return {
            'id': None,
            'email': '',
            'name': '',
            'lastname': '',
            'institute': '',
            'country': '',
            'user_type': ''
        }
    
    try:
        # ✅ MEJORAR CON COMPLEMENTOS SI ESTÁN DISPONIBLES
        try:
            getter = ComplementsGetter()
            getter.set_param('country_id', getattr(current_user, 'country', ''))
            getter.set_param('institute_id', getattr(current_user, 'institute', ''))
            results = getter.get_complements()
            institute_name = results.get('institute_name', '')
            country_name = results.get('country_name', '')
        except Exception as e:
            print(f"⚠️ Error obteniendo complementos: {e}")
            institute_name = getattr(current_user, 'institute', '') or ''
            country_name = getattr(current_user, 'country', '') or ''
        
        user_data = {
            'id': current_user.id,
            'email': current_user.email or '',
            'name': current_user.name or '',
            'lastname': getattr(current_user, 'lastname', '') or '',
            'avatar': getattr(current_user, 'avatar', '') or '',  # ✅ Agregar avatar
            'institute': institute_name,
            'country': country_name,
            'user_type': getattr(current_user, 'user_type', '') or 'Starter'
        }
        
        print(f"✅ get_user_data exitosa para usuario {user_data['email']}")
        return user_data
        
    except Exception as e:
        print(f"💥 Error en get_user_data: {e}")
        return {
            'id': None,
            'email': '',
            'name': '',
            'lastname': '',
            'institute': '',
            'country': '',
            'user_type': ''
        }

def verify_user_authenticated():
    """Función helper para verificar autenticación en todas las rutas"""
    from flask_login import current_user
    from flask import session as flask_session
    
    print(f"\n🔐 VERIFICACIÓN DE AUTENTICACIÓN:")
    print(f"  current_user: {current_user}")
    print(f"  is_authenticated: {current_user.is_authenticated}")
    print(f"  session keys: {list(flask_session.keys())}")
    print(f"  _user_id: {flask_session.get('_user_id', 'MISSING')}")
    
    if not current_user.is_authenticated:
        print("❌ Usuario NO autenticado")
        flash("Sesión expirada. Por favor, inicia sesión nuevamente.", "warning")
        return False
    
    print(f"✅ Usuario autenticado: {current_user.email}")
    return True

def update_user_activity():
    """Actualizar última actividad del usuario"""
    try:
        if current_user.is_authenticated:
            current_user.last_seen = datetime.utcnow()
            db.session.commit()
    except Exception as e:
        print(f"⚠️ Error actualizando last_seen: {e}")
        db.session.rollback()

# ✅ RUTAS CORREGIDAS CON MANEJO ROBUSTO

@x_users.route('/home')
@login_required
def home():
    """Ruta home con debug avanzado"""
    if not verify_user_authenticated():
        return redirect(url_for('x_apps.login'))
    
    try:
        user_data = get_user_data()
        if not user_data or not user_data.get('id'):
            flash("Error al cargar datos de usuario", "error")
            return redirect(url_for('x_apps.login'))
        
        update_user_activity()
        print("✅ Renderizando home.html exitosamente")
        return render_template('/user/home.html', user_data=user_data)
        
    except Exception as e:
        print(f"💥 Error en /home: {e}")
        flash("Error interno. Reinicia tu sesión.", "error")
        return redirect(url_for('x_apps.login'))

@x_users.route('/analysis_original')
@login_required
def analysis_original():
    """Ruta analysis mejorada"""
    if not verify_user_authenticated():
        return redirect(url_for('x_apps.login'))
    
    try:
        user_data = get_user_data()
        if not user_data or not user_data.get('id'):
            flash("Error al cargar datos de usuario", "error")
            return redirect(url_for('x_apps.login'))
        
        update_user_activity()
        return render_template('/user/analysis.html', user_data=user_data, module='analysis')
        
    except Exception as e:
        #print(f"💥 Error en /analysis: {e}")
        flash("Error interno. Reinicia tu sesión.", "error")
        return redirect(url_for('x_apps.login'))

@x_users.route('/analysiss')
@block_starter
@login_required
def analysis():
    """Ruta analysis mejorada"""
    #if not verify_user_authenticated():
    #    return redirect(url_for('x_apps.login'))
    
    #try:
    user_data = get_user_data()
    if not user_data or not user_data.get('id'):
        flash("Error al cargar datos de usuario", "error")
        return redirect(url_for('x_apps.login'))
    
    update_user_activity()
    return render_template('/user/analysis_smartinput.html', user_data=user_data, module='analysis')
        
    #except Exception as e:
        #print(f"💥 Error en /analysis: {e}")
    #    flash("Error interno. Reinicia tu sesión.", "error")
    #    return redirect(url_for('x_apps.login'))

@x_users.route('/analysis_results')
@login_required
def analysis_results():
    """Ruta analysis mejorada"""
    if not verify_user_authenticated():
        return redirect(url_for('x_apps.login'))
    
    try:
        user_data = get_user_data()
        if not user_data or not user_data.get('id'):
            flash("Error al cargar datos de usuario", "error")
            return redirect(url_for('x_apps.login'))
      
        return render_template('/user/results.html', user_data=user_data, module='results')
    except Exception as e:
        #print(f" Error en /analysis: {e}")
        flash("Error interno. Reinicia tu sesión.", "error")
        return redirect(url_for('x_apps.login'))

@x_users.route('/documents')
@block_starter
@login_required
def documents():
    """Ruta documents mejorada"""
    if not verify_user_authenticated():
        return redirect(url_for('x_apps.login'))
    
    try:
        user_data = get_user_data()
        if not user_data or not user_data.get('id'):
            flash("Error al cargar datos de usuario", "error")
            return redirect(url_for('x_apps.login'))
        
        update_user_activity()
        return render_template('/user/clean_html.html', user_data=user_data, module='documents')
        
    except Exception as e:
        print(f"💥 Error en /documentss: {e}")
        flash("Error interno. Reinicia tu sesión.", "error")
        return redirect(url_for('x_apps.login'))

@x_users.route('/cloudstorage')
@block_starter
@login_required
def cloudstorage():
    """Ruta cloudstorage mejorada"""
    if not verify_user_authenticated():
        return redirect(url_for('x_apps.login'))
    
    try:
        user_data = get_user_data()
        if not user_data or not user_data.get('id'):
            flash("Error al cargar datos de usuario", "error")
            return redirect(url_for('x_apps.login'))
        
        update_user_activity()
        return render_template('/user/integrations.html', user_data=user_data, module='cloudstorage')
        
    except Exception as e:
        print(f"💥 Error en /cloudstorage: {e}")
        flash("Error interno. Reinicia tu sesión.", "error")
        return redirect(url_for('x_apps.login'))

@x_users.route('/reviewstudio')
@block_starter
@login_required
def reviewstudio():
    """Ruta reviewstudio mejorada"""
    if not verify_user_authenticated():
        return redirect(url_for('x_apps.login'))
    
    try:
        user_data = get_user_data()
        if not user_data or not user_data.get('id'):
            flash("Error al cargar datos de usuario", "error")
            return redirect(url_for('x_apps.login'))
        
        update_user_activity()
        return render_template('/user/reviewstudio.html', user_data=user_data, module='reviewstudio')
        
    except Exception as e:
        print(f"💥 Error en /reviewstudio: {e}")
        flash("Error interno. Reinicia tu sesión.", "error")
        return redirect(url_for('x_apps.login'))

@x_users.route('/history')
@block_starter
@login_required
def history():
    """Ruta history mejorada"""
    if not verify_user_authenticated():
        return redirect(url_for('x_apps.login'))
    
    try:
        user_data = get_user_data()
        if not user_data or not user_data.get('id'):
            flash("Error al cargar datos de usuario", "error")
            return redirect(url_for('x_apps.login'))
        
        update_user_activity()
        return render_template('/user/history.html', user_data=user_data, module='history')
        
    except Exception as e:
        print(f"💥 Error en /history: {e}")
        flash("Error interno. Reinicia tu sesión.", "error")
        return redirect(url_for('x_apps.login'))

@x_users.route('/account')
@login_required
def account():
    """Ruta account — sólo se usa en modo embed (dentro del modal de Settings).
       Las visitas directas se redirigen al home."""
    if not verify_user_authenticated():
        return redirect(url_for('x_apps.login'))

    # Si no llega el parámetro embed=1, redirigir al home
    # (la pantalla completa de /account ya no existe; se usa el modal)
    if not request.args.get('embed'):
        return redirect(url_for('x_users.home'))

    try:
        user_data = get_user_data()
        if not user_data or not user_data.get('id'):
            flash("Error al cargar datos de usuario", "error")
            return redirect(url_for('x_apps.login'))

        update_user_activity()

        # Build set of connected storage provider keys from user.tokens JSON
        import json as _json
        try:
            raw = current_user.tokens or '{}'
            connected_providers = set(_json.loads(raw).keys())
        except Exception:
            connected_providers = set()

        is_on_trial = bool(getattr(current_user, 'is_on_trial', False))

        return render_template('/user/account.html', user_data=user_data,
                               connected_providers=connected_providers,
                               is_on_trial=is_on_trial,
                               module='account')

    except Exception as e:
        print(f"💥 Error en /account: {e}")
        flash("Error interno. Reinicia tu sesión.", "error")
        return redirect(url_for('x_apps.login'))

@x_users.route('/settings')
@block_starter
@login_required  #  AGREGAR login_required
def settings():
    """Ruta settings corregida - USAR FLASK-LOGIN EN LUGAR DE TOKEN"""
    if not verify_user_authenticated():
        return redirect(url_for('x_apps.login'))
    
    try:
        user_data = get_user_data()
        if not user_data or not user_data.get('id'):
            flash("Error al cargar datos de usuario", "error")
            return redirect(url_for('x_apps.login'))
        
        update_user_activity()
        return render_template('/user/settings.html', user_data=user_data, module='settings')
        
    except Exception as e:
        print(f"💥 Error en /settings: {e}")
        flash("Error interno. Reinicia tu sesión.", "error")
        return redirect(url_for('x_apps.login'))

@x_users.route('/helpcenter')
@login_required  #  AGREGAR login_required
def helpcenter():
    """Ruta helpcenter corregida - USAR FLASK-LOGIN EN LUGAR DE TOKEN"""
    if not verify_user_authenticated():
        return redirect(url_for('x_apps.login'))
    
    try:
        user_data = get_user_data()
        if not user_data or not user_data.get('id'):
            flash("Error al cargar datos de usuario", "error")
            return redirect(url_for('x_apps.login'))
        
        update_user_activity()
        return render_template('/user/helpcenter.html', user_data=user_data)
        
    except Exception as e:
        print(f"💥 Error en /helpcenter: {e}")
        flash("Error interno. Reinicia tu sesión.", "error")
        return redirect(url_for('x_apps.login'))

#  RUTAS API CORREGIDAS CON MANEJO ROBUSTO

@x_users.route('/historial')
@block_starter
@login_required
def historial():
    """Renderiza la página principal del historial"""
    if not verify_user_authenticated():
        return redirect(url_for('x_apps.login'))
    
    try:
        user_data = get_user_data()
        return render_template('historial.html', user_data=user_data)
    except Exception as e:
        print(f" Error en /historial: {e}")
        return redirect(url_for('x_apps.login'))

@x_users.route('/api/historial/data')
@login_required
def historial_data():
    """API para obtener datos del historial con filtros"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401

        user_id = current_user.id
        
        # Parámetros de filtro
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        status = request.args.get('estado')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 5))
        
        # Query base filtrado por usuario
        query = DocumentAnalysis.query.filter(DocumentAnalysis.user_id == user_id)

        # Filtros adicionales
        if fecha_inicio:
            try:
                fecha_inicio_dt = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
                query = query.filter(DocumentAnalysis.analysis_date >= fecha_inicio_dt)
            except ValueError:
                pass
                
        if fecha_fin:
            try:
                fecha_fin_dt = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
                query = query.filter(DocumentAnalysis.analysis_date <= fecha_fin_dt)
            except ValueError:
                pass
        
        # Ordenar por fecha más reciente
        query = query.order_by(desc(DocumentAnalysis.analysis_date))
        
        # Paginación
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        analyses = pagination.items
        
        # Formatear datos
        data = []
        for analysis in analyses:
            # CORRECCIÓN: ai_count YA ES UN PORCENTAJE, no una cantidad
            # Si ai_count = 88.888889, significa 88.89% de IA
            plagio_percentage = round(analysis.ai_count or 0, 2)
            
            # Determine status based on the percentage
            if plagio_percentage < 15:
                doc_status = "Approved"
            elif plagio_percentage < 35:
                doc_status = "Review"
            else:
                doc_status = "Plagiarism detected"

            # Filter by status if specified
            if status and status != 'all':
                if status == 'Approved' and doc_status != 'Approved':
                    continue
                elif status == 'Review' and doc_status != 'Review':
                    continue
                elif status == 'Plagiarism detected' and doc_status != 'Plagiarism detected':
                    continue

            data.append({
                'id': analysis.id,
                'analysis_id': analysis.analysis_id,
                'document': analysis.title or 'Untitled',
                'user_id': analysis.user_id,
                'date': analysis.analysis_date.strftime('%Y-%m-%d %H:%M') if analysis.analysis_date else '',
                'plagiarism_percentage': plagio_percentage,  # Already a percentage
                'status': doc_status,
                'total_paragraphs': analysis.total_paragraphs or 0,
                'ai_count': analysis.ai_count or 0,  # AI percentage
                'human_count': analysis.human_count or 0,  # Human percentage
                'confidence': round(analysis.average_confidence or 0, 2),
                'pages': analysis.pages or 0,
                'format': analysis.format or 'PDF'
            })

        
        return jsonify({
            'success': True,
            'data': data,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        print(f"💥 Error en /api/historial/data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@x_users.route('/api/historial/chart')
@login_required
def historial_chart():
    """API para datos del gráfico ECharts - CORREGIDO"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401

        user_id = current_user.id  # ✅ USAR current_user
        dias = int(request.args.get('dias', 30))
        fecha_limite = datetime.now() - timedelta(days=dias)

        # Datos por fecha para el usuario
        chart_data = db.session.query(
            func.date(DocumentAnalysis.analysis_date).label('fecha'),
            func.count(DocumentAnalysis.id).label('total_documentos'),
            func.avg(
                (DocumentAnalysis.ai_count * 100.0 /
                 func.nullif(DocumentAnalysis.total_paragraphs, 0))
            ).label('promedio_plagio')
        ).filter(
            DocumentAnalysis.analysis_date >= fecha_limite,
            DocumentAnalysis.user_id == user_id
        ).group_by(
            func.date(DocumentAnalysis.analysis_date)
        ).order_by('fecha').all()

        fechas = []
        documentos = []
        plagio_promedio = []

        for item in chart_data:
            fechas.append(item.fecha.strftime('%Y-%m-%d'))
            documentos.append(item.total_documentos)
            plagio_promedio.append(round(item.promedio_plagio or 0, 2))

        return jsonify({
            'success': True,
            'timeline': {
                'fechas': fechas,
                'documentos': documentos,
                'plagio_promedio': plagio_promedio
            }
        })

    except Exception as e:
        print(f"💥 Error en /api/historial/chart: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@x_users.route('/api/historial/stats')
@login_required
def historial_stats():
    """API para estadísticas generales del usuario"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401

        user_id = current_user.id
        ultimo_mes = datetime.now() - timedelta(days=30)

        # Total de documentos del usuario
        total_documentos = DocumentAnalysis.query.filter_by(user_id=user_id).count()

        # Documentos del último mes
        documentos_mes = DocumentAnalysis.query.filter(
            DocumentAnalysis.analysis_date >= ultimo_mes,
            DocumentAnalysis.user_id == user_id
        ).count()

        # ✅ CORRECCIÓN: Promedio de ai_count (que ya es porcentaje)
        promedio_plagio = db.session.query(
            func.avg(DocumentAnalysis.ai_count)
        ).filter_by(user_id=user_id).scalar() or 0

        estados = {
            'aprobados': 0,
            'revision': 0,
            'plagio': 0
        }

        analyses = DocumentAnalysis.query.filter_by(user_id=user_id).all()
        for analysis in analyses:
            # ✅ ai_count ya es porcentaje
            plagio_perc = analysis.ai_count or 0
            
            if plagio_perc < 15:
                estados['aprobados'] += 1
            elif plagio_perc < 35:
                estados['revision'] += 1
            else:
                estados['plagio'] += 1

        return jsonify({
            'success': True,
            'stats': {
                'total_documentos': total_documentos,
                'documentos_mes': documentos_mes,
                'promedio_plagio': round(promedio_plagio, 2),
                'estados': estados
            }
        })

    except Exception as e:
        print(f"💥 Error en /api/historial/stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@x_users.route('/api/history/analytics')
@login_required
def history_analytics():
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'No autenticado'}), 401

        uid   = current_user.id
        range_ = request.args.get('range', '30')
        now   = datetime.now()

        if range_ == 'today':
            date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_to   = now
            prev_from = date_from - timedelta(days=1)
            prev_to   = date_from
        elif range_ == 'custom':
            try:
                date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
                date_to   = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            except Exception:
                date_from = now - timedelta(days=30)
                date_to   = now
            delta = (date_to - date_from).days or 1
            prev_from = date_from - timedelta(days=delta)
            prev_to   = date_from
        else:
            days      = int(range_) if range_.isdigit() else 30
            date_from = now - timedelta(days=days)
            date_to   = now
            prev_from = date_from - timedelta(days=days)
            prev_to   = date_from

        analyses = DocumentAnalysis.query.filter(
            DocumentAnalysis.user_id == uid,
            DocumentAnalysis.analysis_date >= date_from,
            DocumentAnalysis.analysis_date <= date_to
        ).order_by(desc(DocumentAnalysis.analysis_date)).all()

        prev_analyses = DocumentAnalysis.query.filter(
            DocumentAnalysis.user_id == uid,
            DocumentAnalysis.analysis_date >= prev_from,
            DocumentAnalysis.analysis_date < prev_to
        ).all()

        def risk_level(ai_pct):
            if ai_pct >= 35: return 'crit'
            if ai_pct >= 15: return 'warn'
            return 'ok'

        total     = len(analyses)
        approved  = sum(1 for a in analyses if (a.ai_count or 0) < 15)
        revision  = sum(1 for a in analyses if 15 <= (a.ai_count or 0) < 35)
        high_risk = sum(1 for a in analyses if (a.ai_count or 0) >= 35)
        avg_ai    = (sum(a.ai_count or 0 for a in analyses) / total) if total else 0
        integrity = max(0.0, min(100.0, 100 - avg_ai))
        total_img = sum(len(a.images) if isinstance(a.images, list) else 0 for a in analyses)

        prev_total  = len(prev_analyses)
        prev_avg_ai = (sum(a.ai_count or 0 for a in prev_analyses) / prev_total) if prev_total else avg_ai
        avg_ai_trend    = round(avg_ai - prev_avg_ai, 1)
        integrity_trend = round((100 - avg_ai) - (100 - prev_avg_ai), 1)

        from collections import defaultdict
        day_map = defaultdict(list)
        for a in reversed(analyses):
            key = a.analysis_date.strftime('%Y-%m-%d')
            day_map[key].append(a.ai_count or 0)

        timeseries = [
            {
                'date':      d,
                'ai_pct':    round(sum(v)/len(v), 1),
                'count':     len(v),
                'integrity': round(100 - sum(v)/len(v), 1)
            }
            for d, v in sorted(day_map.items())
        ]

        sessions = []
        for a in analyses:
            ai_pct    = float(a.ai_count or 0)
            img_count = len(a.images) if isinstance(a.images, list) else 0
            integ     = max(0, 100 - int(ai_pct))
            sessions.append({
                'analysis_id': a.analysis_id,
                'title':       a.title or 'Sin título',
                'date':        a.analysis_date.strftime('%Y-%m-%d %H:%M'),
                'ai_pct':      ai_pct,
                'images':      img_count,
                'integrity':   integ,
                'risk':        risk_level(ai_pct),
                'pages':       a.pages,
                'paragraphs':  a.total_paragraphs,
                'confidence':  a.average_confidence
            })

        alerts = [
            s for s in sessions
            if s['risk'] == 'crit' or s['images'] >= 3
        ][:10]

        return jsonify({
            'success': True,
            'data': {
                'kpis': {
                    'total_analyses':  total,
                    'avg_ai_pct':      round(avg_ai, 1),
                    'avg_ai_trend':    avg_ai_trend,
                    'approved':        approved,
                    'revision':        revision,
                    'high_risk':       high_risk,
                    'total_images':    total_img,
                    'integrity_score': round(integrity, 1),
                    'integrity_trend': integrity_trend
                },
                'timeseries': timeseries,
                'alerts':     alerts,
                'sessions':   sessions
            }
        })

    except Exception as e:
        print(f"Error en /api/history/analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@x_users.route('/api/documento/<analysis_id>')
@login_required
def detalle_documento(analysis_id):
    """API para obtener detalles de un documento específico"""
    try:
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Usuario no autenticado'}), 401

        # VERIFICAR QUE EL DOCUMENTO PERTENECE AL USUARIO
        analysis = DocumentAnalysis.query.filter_by(
            analysis_id=analysis_id, 
            user_id=current_user.id
        ).first()
        
        if not analysis:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
        
        # Obtener párrafos clasificados
        paragraphs = ClassifiedParagraph.query.filter_by(
            analysis_id=analysis_id
        ).order_by(
            ClassifiedParagraph.page_number,
            ClassifiedParagraph.paragraph_number
        ).all()
        
        from collections import Counter
        import json

        # Construcción de paragraphs_data
        paragraphs_data = []
        model_usage_counter = Counter()
        
        # ✅ CORRECCIÓN: Contar párrafos reales, no porcentajes
        real_human_count = 0
        real_ai_count = 0

        for p in paragraphs:
            # Contar párrafos humanos/IA reales
            if p.is_human is not None:
                if p.is_human:
                    real_human_count += 1
                else:
                    real_ai_count += 1
            
            # Agregar el párrafo a la lista
            paragraphs_data.append({
                'page': p.page_number or 1,
                'paragraph': p.paragraph_number or 1,
                'text': p.text[:200] + '...' if p.text and len(p.text) > 200 else (p.text or ''),
                'is_human': p.is_human,
                'confidence': round(p.final_confidence or 0, 2),
                'human_prob': round(p.human_probability or 0, 2),
                'ai_prob': round(p.ai_probability or 0, 2),
                'model_scores': p.model_scores
            })
            
            # Contar el modelo con mayor score en este párrafo (solo si es IA)
            if not p.is_human and p.model_scores:
                try:
                    scores = p.model_scores
                    if isinstance(scores, str):
                        scores = json.loads(scores)
                    
                    if scores and isinstance(scores, dict):
                        top_model = max(scores.items(), key=lambda item: item[1])[0]
                        model_usage_counter[top_model] += 1
                except Exception as e:
                    print(f"⚠️ Error procesando model_scores para párrafo: {e}")
                    continue

        # Obtener modelo IA más usado
        most_used_model = model_usage_counter.most_common(1)[0][0] if model_usage_counter else None

        return jsonify({
            'success': True,
            'documento': {
                'title': analysis.title or 'Sin título',
                'author': analysis.author or '',
                'fecha': analysis.analysis_date.strftime('%Y-%m-%d %H:%M') if analysis.analysis_date else '',
                'pages': analysis.pages or 0,
                'format': analysis.format or 'PDF',
                'total_paragraphs': analysis.total_paragraphs or 0,
                'human_count': real_human_count,  # ✅ Conteo real
                'ai_count': real_ai_count,  # ✅ Conteo real
                'confidence': round(analysis.average_confidence or 0, 2),
                'most_used_ai_model': most_used_model,
                'paragraphs': paragraphs_data
            }
        })
        
    except Exception as e:
        print(f"💥 Error en /api/documento/{analysis_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

### WELCOME MODAL 
@x_users.route('/api/check-welcome-modal', methods=['GET'])
@login_required
def check_welcome_modal():
    """API: Verifica si se debe mostrar el modal de bienvenida"""
    try:
        # Buscar preferencia del usuario
        preference = UserPreference.query.filter_by(user_id=current_user.id).first()
        
        # Si no existe preferencia, crearla (usuario nuevo)
        if not preference:
            preference = UserPreference(
                user_id=current_user.id,
                show_welcome_modal=True
            )
            db.session.add(preference)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'show_modal': True,
                'message': 'New user, show modal',
                'user_id': current_user.id
            })
        
        return jsonify({
            'success': True,
            'show_modal': preference.show_welcome_modal,
            'last_updated': preference.updated_at.isoformat() if preference.updated_at else None
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@x_users.route('/api/dismiss-welcome-modal', methods=['POST'])
@login_required
def dismiss_welcome_modal():
    """API: Marca el modal como visto y no volver a mostrar"""
    try:
        data = request.get_json()
        dont_show_again = data.get('dont_show_again', False)
        
        # Buscar o crear preferencia
        preference = UserPreference.query.filter_by(user_id=current_user.id).first()
        
        if not preference:
            preference = UserPreference(user_id=current_user.id)
            db.session.add(preference)
        
        # Actualizar preferencia
        #if dont_show_again:
        #    preference.show_welcome_modal = False
        preference.show_welcome_modal = not dont_show_again
        preference.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Preference saved successfully',
            'show_modal': preference.show_welcome_modal,
            'dont_show_again': dont_show_again
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@x_users.route('/api/reset-welcome-modal', methods=['POST'])
@login_required
def reset_welcome_modal():
    """API: Resetea el modal para que se vuelva a mostrar (útil para testing)"""
    try:
        preference = UserPreference.query.filter_by(user_id=current_user.id).first()
        
        if preference:
            preference.show_welcome_modal = True
            preference.updated_at = datetime.utcnow()
            db.session.commit()
            message = 'Modal reset successfully'
        else:
            # Crear preferencia si no existe
            preference = UserPreference(
                user_id=current_user.id,
                show_welcome_modal=True
            )
            db.session.add(preference)
            db.session.commit()
            message = 'Preference created and modal activated'
        
        return jsonify({
            'success': True,
            'message': message
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
@x_users.route('/storage_info')
@login_required
def get_storage_info():
    """Get current user storage stats"""
    try:
        total = current_user.get_total_storage_limit_bytes()
        used = current_user.used_storage_bytes or 0
        
        # Get file stats from DB
        files_count = len(current_user.files) if hasattr(current_user, 'files') else 0
        
        # Calculate file type distribution
        file_types = {'PDF': 0, 'Word': 0, 'TXT': 0, 'EPUB': 0, 'PowerPoint': 0, 'Other': 0}
        if hasattr(current_user, 'files'):
            for file in current_user.files:
                ftype = 'Other'
                mtype = (file.mime_type or '').lower()
                fname = (file.original_filename or '').lower()
                
                if 'pdf' in mtype or fname.endswith('.pdf'): 
                    ftype = 'PDF'
                elif any(word in mtype for word in ['word', 'officedocument.wordprocessingml']) or any(fname.endswith(ext) for ext in ['.doc', '.docx']):
                    ftype = 'Word'
                elif 'text' in mtype or fname.endswith('.txt'):
                    ftype = 'TXT'
                elif 'epub' in mtype or fname.endswith('.epub'):
                    ftype = 'EPUB'
                elif any(word in mtype for word in ['powerpoint', 'presentation']) or any(fname.endswith(ext) for ext in ['.ppt', '.pptx']):
                    ftype = 'PowerPoint'
                
                file_types[ftype] += 1
        
        return jsonify({
            'total_storage': total,
            'used_storage': used,
            'plan_name': current_user.user_type or 'Starter',
            'files_count': files_count,
            'file_types': file_types
        })
    except Exception as e:
        print(f"Error getting storage info: {e}")
        return jsonify({'error': str(e)}), 500
