from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models.model import DocumentAnalysis, ClassifiedParagraph
from utils.connections import db
from sqlalchemy import func, desc
import json

document_analysis_bp = Blueprint('document_analysis_bp', __name__)

@document_analysis_bp.route('/')
@login_required
def index():
    """Renderizar página principal del análisis de documentos"""
    return render_template('document_analysis.html')

@document_analysis_bp.route('/api/analyses')
@login_required
def get_analyses():
    """Obtener lista de análisis del usuario"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        format_filter = request.args.get('format', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Query base
        query = DocumentAnalysis.query.filter_by(user_id=current_user.id)
        
        # Filtros
        if search:
            query = query.filter(
                (DocumentAnalysis.title.ilike(f'%{search}%')) |
                (DocumentAnalysis.author.ilike(f'%{search}%')) |
                (DocumentAnalysis.subject.ilike(f'%{search}%'))
            )
        
        if format_filter:
            query = query.filter(DocumentAnalysis.format == format_filter)
            
        if date_from:
            query = query.filter(DocumentAnalysis.analysis_date >= datetime.fromisoformat(date_from))
            
        if date_to:
            query = query.filter(DocumentAnalysis.analysis_date <= datetime.fromisoformat(date_to))
        
        # Ordenar por fecha más reciente
        query = query.order_by(desc(DocumentAnalysis.analysis_date))
        
        # Paginación
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        analyses = []
        for analysis in pagination.items:
            analyses.append({
                'id': analysis.id,
                'analysis_id': analysis.analysis_id,
                'title': analysis.title or 'Sin título',
                'author': analysis.author,
                'format': analysis.format,
                'pages': analysis.pages,
                'language': analysis.language,
                'analysis_date': analysis.analysis_date.isoformat() if analysis.analysis_date else None,
                'success': analysis.success,
                'total_paragraphs': analysis.total_paragraphs,
                'human_count': analysis.human_count,
                'ai_count': analysis.ai_count,
                'average_confidence': round(analysis.average_confidence, 2) if analysis.average_confidence else 0,
                'human_percentage': round((analysis.human_count / analysis.total_paragraphs * 100), 1) if analysis.total_paragraphs > 0 else 0,
                'ai_percentage': round((analysis.ai_count / analysis.total_paragraphs * 100), 1) if analysis.total_paragraphs > 0 else 0
            })
        
        return jsonify({
            'status': 'success',
            'analyses': analyses,
            'pagination': {
                'current_page': pagination.page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@document_analysis_bp.route('/api/analysis/<analysis_id>')
@login_required
def get_analysis_details(analysis_id):
    """Obtener detalles completos de un análisis"""
    try:
        analysis = DocumentAnalysis.query.filter_by(
            analysis_id=analysis_id,
            user_id=current_user.id
        ).first()
        
        if not analysis:
            return jsonify({
                'status': 'error',
                'message': 'Análisis no encontrado'
            }), 404
        
        # Estadísticas por página
        page_stats = db.session.query(
            ClassifiedParagraph.page_number,
            func.count(ClassifiedParagraph.id).label('total_paragraphs'),
            func.sum(func.cast(ClassifiedParagraph.is_human, db.Integer)).label('human_count'),
            func.avg(ClassifiedParagraph.final_confidence).label('avg_confidence')
        ).filter_by(analysis_id=analysis_id).group_by(
            ClassifiedParagraph.page_number
        ).order_by(ClassifiedParagraph.page_number).all()
        
        page_statistics = []
        for stat in page_stats:
            ai_count = stat.total_paragraphs - stat.human_count
            page_statistics.append({
                'page_number': stat.page_number,
                'total_paragraphs': stat.total_paragraphs,
                'human_count': stat.human_count,
                'ai_count': ai_count,
                'human_percentage': round((stat.human_count / stat.total_paragraphs * 100), 1),
                'ai_percentage': round((ai_count / stat.total_paragraphs * 100), 1),
                'avg_confidence': round(stat.avg_confidence, 2) if stat.avg_confidence else 0
            })
        
        # Modelos utilizados
        model_usage = db.session.query(
            ClassifiedParagraph.predicted_model,
            func.count(ClassifiedParagraph.id).label('usage_count')
        ).filter_by(analysis_id=analysis_id).filter(
            ClassifiedParagraph.predicted_model.isnot(None)
        ).group_by(ClassifiedParagraph.predicted_model).all()
        
        models = [{'model': m.predicted_model, 'count': m.usage_count} for m in model_usage]
        
        analysis_data = {
            'id': analysis.id,
            'analysis_id': analysis.analysis_id,
            'analysis_date': analysis.analysis_date.isoformat() if analysis.analysis_date else None,
            'title': analysis.title,
            'author': analysis.author,
            'creator': analysis.creator,
            'producer': analysis.producer,
            'subject': analysis.subject,
            'keywords': analysis.keywords,
            'format': analysis.format,
            'creation_date': analysis.creation_date,
            'mod_date': analysis.mod_date,
            'encryption': analysis.encryption,
            'trapped': analysis.trapped,
            'pages': analysis.pages,
            'language': analysis.language,
            'success': analysis.success,
            'total_paragraphs': analysis.total_paragraphs,
            'human_count': analysis.human_count,
            'ai_count': analysis.ai_count,
            'average_confidence': round(analysis.average_confidence, 2) if analysis.average_confidence else 0,
            'human_percentage': round((analysis.human_count / analysis.total_paragraphs * 100), 1) if analysis.total_paragraphs > 0 else 0,
            'ai_percentage': round((analysis.ai_count / analysis.total_paragraphs * 100), 1) if analysis.total_paragraphs > 0 else 0,
            'preview_success': analysis.preview_success,
            'preview_page_count': analysis.preview_page_count,
            'full_preview_path': analysis.full_preview_path,
            'preview_dir': analysis.preview_dir,
            'annotations': analysis.annotations,
            'images': analysis.images,
            'urls': analysis.urls,
            'preview_page_files': analysis.preview_page_files,
            'page_statistics': page_statistics,
            'models_used': models
        }
        
        return jsonify({
            'status': 'success',
            'analysis': analysis_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@document_analysis_bp.route('/api/analysis/<analysis_id>/paragraphs')
@login_required
def get_analysis_paragraphs(analysis_id):
    """Obtener párrafos clasificados de un análisis"""
    try:
        # Verificar que el análisis pertenece al usuario
        analysis = DocumentAnalysis.query.filter_by(
            analysis_id=analysis_id,
            user_id=current_user.id
        ).first()
        
        if not analysis:
            return jsonify({
                'status': 'error',
                'message': 'Análisis no encontrado'
            }), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        page_filter = request.args.get('page_number', type=int)
        classification_filter = request.args.get('classification', '')  # 'human' o 'ai'
        min_confidence = request.args.get('min_confidence', type=float)
        max_confidence = request.args.get('max_confidence', type=float)
        
        # Query base
        query = ClassifiedParagraph.query.filter_by(analysis_id=analysis_id)
        
        # Filtros
        if page_filter:
            query = query.filter(ClassifiedParagraph.page_number == page_filter)
            
        if classification_filter == 'human':
            query = query.filter(ClassifiedParagraph.is_human == True)
        elif classification_filter == 'ai':
            query = query.filter(ClassifiedParagraph.is_human == False)
            
        if min_confidence is not None:
            query = query.filter(ClassifiedParagraph.final_confidence >= min_confidence)
            
        if max_confidence is not None:
            query = query.filter(ClassifiedParagraph.final_confidence <= max_confidence)
        
        # Ordenar por página y párrafo
        query = query.order_by(
            ClassifiedParagraph.page_number,
            ClassifiedParagraph.paragraph_number
        )
        
        # Paginación
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        paragraphs = []
        for p in pagination.items:
            paragraphs.append({
                'id': p.id,
                'page_number': p.page_number,
                'paragraph_number': p.paragraph_number,
                'text': p.text,
                'is_human': p.is_human,
                'classification': 'Humano' if p.is_human else 'IA',
                'human_probability': round(p.human_probability, 3),
                'ai_probability': round(p.ai_probability, 3),
                'predicted_model': p.predicted_model,
                'model_scores': p.model_scores,
                'final_confidence': round(p.final_confidence, 3),
                'text_preview': p.text[:150] + '...' if len(p.text) > 150 else p.text
            })
        
        return jsonify({
            'status': 'success',
            'paragraphs': paragraphs,
            'pagination': {
                'current_page': pagination.page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@document_analysis_bp.route('/api/stats')
@login_required
def get_analysis_stats():
    """Obtener estadísticas generales de análisis"""
    try:
        # Estadísticas generales
        total_analyses = DocumentAnalysis.query.filter_by(user_id=current_user.id).count()
        successful_analyses = DocumentAnalysis.query.filter_by(
            user_id=current_user.id, success=True
        ).count()
        
        # Análisis recientes (últimos 30 días)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_analyses = DocumentAnalysis.query.filter(
            DocumentAnalysis.user_id == current_user.id,
            DocumentAnalysis.analysis_date >= thirty_days_ago
        ).count()
        
        # Estadísticas de párrafos
        total_paragraphs = db.session.query(func.sum(DocumentAnalysis.total_paragraphs)).filter_by(
            user_id=current_user.id
        ).scalar() or 0
        
        total_human = db.session.query(func.sum(DocumentAnalysis.human_count)).filter_by(
            user_id=current_user.id
        ).scalar() or 0
        
        total_ai = db.session.query(func.sum(DocumentAnalysis.ai_count)).filter_by(
            user_id=current_user.id
        ).scalar() or 0
        
        # Confianza promedio
        avg_confidence = db.session.query(func.avg(DocumentAnalysis.average_confidence)).filter_by(
            user_id=current_user.id
        ).scalar() or 0
        
        # Formatos más analizados
        format_stats = db.session.query(
            DocumentAnalysis.format,
            func.count(DocumentAnalysis.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(
            DocumentAnalysis.format
        ).order_by(desc('count')).limit(5).all()
        
        # Idiomas detectados
        language_stats = db.session.query(
            DocumentAnalysis.language,
            func.count(DocumentAnalysis.id).label('count')
        ).filter_by(user_id=current_user.id).filter(
            DocumentAnalysis.language.isnot(None)
        ).group_by(DocumentAnalysis.language).order_by(desc('count')).limit(5).all()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'total_analyses': total_analyses,
                'successful_analyses': successful_analyses,
                'recent_analyses': recent_analyses,
                'success_rate': round((successful_analyses / total_analyses * 100), 1) if total_analyses > 0 else 0,
                'total_paragraphs': total_paragraphs,
                'total_human': total_human,
                'total_ai': total_ai,
                'human_percentage': round((total_human / total_paragraphs * 100), 1) if total_paragraphs > 0 else 0,
                'ai_percentage': round((total_ai / total_paragraphs * 100), 1) if total_paragraphs > 0 else 0,
                'average_confidence': round(avg_confidence, 2) if avg_confidence else 0,
                'formats': [{'format': f.format, 'count': f.count} for f in format_stats],
                'languages': [{'language': l.language, 'count': l.count} for l in language_stats]
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@document_analysis_bp.route('/api/analysis/<analysis_id>/export')
@login_required
def export_analysis(analysis_id):
    """Exportar análisis en formato JSON"""
    try:
        analysis = DocumentAnalysis.query.filter_by(
            analysis_id=analysis_id,
            user_id=current_user.id
        ).first()
        
        if not analysis:
            return jsonify({
                'status': 'error',
                'message': 'Análisis no encontrado'
            }), 404
        
        # Obtener todos los párrafos
        paragraphs = ClassifiedParagraph.query.filter_by(
            analysis_id=analysis_id
        ).order_by(
            ClassifiedParagraph.page_number,
            ClassifiedParagraph.paragraph_number
        ).all()
        
        export_data = {
            'analysis_metadata': {
                'analysis_id': analysis.analysis_id,
                'title': analysis.title,
                'author': analysis.author,
                'analysis_date': analysis.analysis_date.isoformat() if analysis.analysis_date else None,
                'total_paragraphs': analysis.total_paragraphs,
                'human_count': analysis.human_count,
                'ai_count': analysis.ai_count,
                'average_confidence': analysis.average_confidence
            },
            'paragraphs': [
                {
                    'page': p.page_number,
                    'paragraph': p.paragraph_number,
                    'text': p.text,
                    'is_human': p.is_human,
                    'confidence': p.final_confidence,
                    'model': p.predicted_model
                } for p in paragraphs
            ]
        }
        
        return jsonify({
            'status': 'success',
            'export_data': export_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@document_analysis_bp.errorhandler(404)
def not_found(error):
    """Manejo de errores 404"""
    return jsonify({
        'status': 'error',
        'message': 'Recurso no encontrado'
    }), 404

@document_analysis_bp.errorhandler(500)
def internal_error(error):
    """Manejo de errores 500"""
    return jsonify({
        'status': 'error',
        'message': 'Error interno del servidor'
    }), 500