from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import csv
from models.model import Documents, Lenguage
from utils.connections import db
from io import StringIO
from flask import make_response

languages_bp = Blueprint('languages_bp', __name__)

@languages_bp.route('/api/languages', methods=['GET'])
def list_languages():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        sort_field = request.args.get('sort_field', 'created_date')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Filters
        search = request.args.get('search', '').strip()
        code = request.args.get('code', '').strip()
        
        # Base query
        query = db.session.query(Lenguage)
        
        # Add document count
        doc_count_subquery = db.session.query(
            Documents.lenguage_id,
            func.count(Documents.id).label('documents_count')
        ).group_by(Documents.lenguage_id).subquery()
        
        query = query.outerjoin(
            doc_count_subquery,
            Lenguage.id == doc_count_subquery.c.lenguage_id
        ).add_columns(
            Lenguage.id,
            Lenguage.lenguage_name,
            Lenguage.lenguage,
            Lenguage.created_date,
            func.coalesce(doc_count_subquery.c.documents_count, 0).label('documents_count')
        )
        
        # Apply filters
        if search:
            search_filter = or_(
                Lenguage.lenguage_name.ilike(f'%{search}%'),
                Lenguage.lenguage.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        if code:
            query = query.filter(Lenguage.lenguage.ilike(f'%{code}%'))
        
        # Apply sorting
        if sort_field == 'lenguage_name':
            sort_column = Lenguage.lenguage_name
        elif sort_field == 'lenguage':
            sort_column = Lenguage.lenguage
        else:
            sort_column = getattr(Lenguage, sort_field, Lenguage.created_date)
        
        if sort_direction == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Pagination
        total = query.count()
        languages = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format results
        languages_list = []
        for lang in languages:
            languages_list.append({
                'id': lang.id,
                'lenguage_name': lang.lenguage_name,
                'lenguage': lang.lenguage,
                'documents_count': lang.documents_count,
                'created_date': lang.created_date.isoformat() if lang.created_date else None
            })
        
        return jsonify({
            'languages': languages_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@languages_bp.route('/api/languages', methods=['POST'])
def create_language():
    #try:
    data = request.get_json()
    
    # Validation
    if not data.get('lenguage_name'):
        return jsonify({'error': 'Nombre del idioma es requerido'}), 400
    
    if not data.get('lenguage'):
        return jsonify({'error': 'Código del idioma es requerido'}), 400
    
    # Validate code length
    if len(data.get('lenguage', '')) != 2:
        return jsonify({'error': 'El código debe tener exactamente 2 caracteres'}), 400
    
    # Check if language code already exists
    existing_code = Lenguage.query.filter(
        Lenguage.lenguage.ilike(data['lenguage'])
    ).first()
    
    if existing_code:
        return jsonify({'error': 'Ya existe un idioma con este código'}), 400
    
    # Check if language name already exists
    existing_name = Lenguage.query.filter(
        Lenguage.lenguage_name.ilike(data['lenguage_name'])
    ).first()
    
    if existing_name:
        return jsonify({'error': 'Ya existe un idioma con este nombre'}), 400
    
    # Create new language
    language = Lenguage(
        lenguage_name=data.get('lenguage_name'),
        lenguage=data.get('lenguage').lower()
        #user_id=int(1)  # Get from session/auth
    )
    
    db.session.add(language)
    db.session.commit()
    
    return jsonify({'message': 'Idioma creado exitosamente', 'id': language.id}), 201
    
    #except Exception as e:
    #    db.session.rollback()
    #    return jsonify({'error': str(e)}), 500

@languages_bp.route('/api/languages/<int:language_id>', methods=['GET'])
def get_language(language_id):
    try:
        language = Lenguage.query.get_or_404(language_id)
        
        return jsonify({
            'id': language.id,
            'lenguage_name': language.lenguage_name,
            'lenguage': language.lenguage,
            'created_date': language.created_date.isoformat() if language.created_date else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@languages_bp.route('/api/languages/<int:language_id>', methods=['PUT'])
def update_language(language_id):
    try:
        language = Lenguage.query.get_or_404(language_id)
        data = request.get_json()
        
        # Validation
        if 'lenguage' in data:
            if len(data.get('lenguage', '')) != 2:
                return jsonify({'error': 'El código debe tener exactamente 2 caracteres'}), 400
            
            # Check if language code already exists (excluding current)
            existing_code = Lenguage.query.filter(
                and_(
                    Lenguage.lenguage.ilike(data['lenguage']),
                    Lenguage.id != language_id
                )
            ).first()
            
            if existing_code:
                return jsonify({'error': 'Ya existe un idioma con este código'}), 400
        
        if 'lenguage_name' in data:
            # Check if language name already exists (excluding current)
            existing_name = Lenguage.query.filter(
                and_(
                    Lenguage.lenguage_name.ilike(data['lenguage_name']),
                    Lenguage.id != language_id
                )
            ).first()
            
            if existing_name:
                return jsonify({'error': 'Ya existe un idioma con este nombre'}), 400
        
        # Update fields
        if 'lenguage_name' in data:
            language.lenguage_name = data['lenguage_name']
        if 'lenguage' in data:
            language.lenguage = data['lenguage'].lower()
        
        db.session.commit()
        
        return jsonify({'message': 'Idioma actualizado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@languages_bp.route('/api/languages/<int:language_id>', methods=['DELETE'])
def delete_language(language_id):
    try:
        language = Lenguage.query.get_or_404(language_id)
        
        # Check if language has documents
        doc_count = Documents.query.filter(Documents.lenguage_id == language_id).count()
        if doc_count > 0:
            return jsonify({'error': f'No se puede eliminar el idioma porque tiene {doc_count} documentos asociados'}), 400
        
        db.session.delete(language)
        db.session.commit()
        
        return jsonify({'message': 'Idioma eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@languages_bp.route('/api/languages/stats', methods=['GET'])
def get_languages_stats():
    try:
        # Total languages
        total = Lenguage.query.count()
        
        # Languages this month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = Lenguage.query.filter(Lenguage.created_date >= current_month).count()
        
        # Documents linked to languages
        documents_linked = db.session.query(Documents)\
            .filter(Documents.lenguage_id.isnot(None)).count()
        
        # Most used language
        most_used_result = db.session.query(
            Lenguage.lenguage_name,
            func.count(Documents.id).label('usage_count')
        ).join(Documents, Lenguage.id == Documents.lenguage_id)\
        .group_by(Lenguage.id, Lenguage.lenguage_name)\
        .order_by(func.count(Documents.id).desc())\
        .first()
        
        most_used = most_used_result.lenguage_name if most_used_result else '-'
        
        return jsonify({
            'total': total,
            'monthly': monthly,
            'documents_linked': documents_linked,
            'most_used': most_used
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@languages_bp.route('/api/languages/export', methods=['GET'])
def export_languages():
    try:
        # Get all languages with document counts
        languages = db.session.query(Lenguage)\
            .outerjoin(Documents, Lenguage.id == Documents.lenguage_id)\
            .add_columns(
                Lenguage.id,
                Lenguage.lenguage_name,
                Lenguage.lenguage,
                Lenguage.created_date,
                func.count(Documents.id).label('documents_count')
            )\
            .group_by(Lenguage.id, Lenguage.lenguage_name, Lenguage.lenguage, Lenguage.created_date)\
            .all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Nombre del Idioma', 'Código ISO', 'Documentos Asociados', 'Fecha Creación'
        ])
        
        # Data
        for lang in languages:
            writer.writerow([
                lang.id,
                lang.lenguage_name or '',
                lang.lenguage or '',
                lang.documents_count or 0,
                lang.created_date.strftime('%Y-%m-%d %H:%M:%S') if lang.created_date else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=idiomas_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500