from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import csv
from models.model import Documents, Country, Institution,City, Institution_type
from utils.connections import db
from io import StringIO
from flask import make_response

institutions_bp = Blueprint('institutions_bp', __name__)

@institutions_bp.route('/api/institutions', methods=['GET'])
def list_institutions():
    #try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        sort_field = request.args.get('sort_field', 'created_date')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Filters
        search = request.args.get('search', '').strip()
        institution_type = request.args.get('institution_type')
        country_id = request.args.get('country_id')
        city_id = request.args.get('city_id')
        
        # Base query with joins
        query = db.session.query(Institution)\
            .outerjoin(Institution_type, Institution.institution_type == Institution_type.id)\
            .outerjoin(Country, Institution.country_id == Country.id)\
            .outerjoin(City, Institution.city_id == City.id)\
            .add_columns(
                Institution.id,
                Institution.institution,
                Institution.created_date,
                Institution_type.institution_type.label('type_name'),
                Country.country.label('country_name'),
                City.city.label('city_name')
            )
        
        # Add document count
        doc_count_subquery = db.session.query(
            Documents.institution_id,
            func.count(Documents.id).label('documents_count')
        ).group_by(Documents.institution_id).subquery()
        
        query = query.outerjoin(
            doc_count_subquery,
            Institution.id == doc_count_subquery.c.institution_id
        ).add_columns(
            func.coalesce(doc_count_subquery.c.documents_count, 0).label('documents_count')
        )
        
        # Apply filters
        if search:
            query = query.filter(Institution.institution.ilike(f'%{search}%'))
        
        if institution_type:
            query = query.filter(Institution.institution_type == institution_type)
        
        if country_id:
            query = query.filter(Institution.country_id == country_id)
            
        if city_id:
            query = query.filter(Institution.city_id == city_id)
        
        # Apply sorting
        if sort_field == 'institution':
            sort_column = Institution.institution
        elif sort_field == 'type_name':
            sort_column = Institution_type.institution_type
        elif sort_field == 'country_name':
            sort_column = Country.country
        elif sort_field == 'city_name':
            sort_column = City.city
        else:
            sort_column = getattr(Institution, sort_field, Institution.created_date)
        
        if sort_direction == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Pagination
        total = query.count()
        institutions = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format results
        institutions_list = []
        for inst in institutions:
            institutions_list.append({
                'id': inst.id,
                'institution': inst.institution,
                'institution_type': inst.Institution.institution_type,
                'country_id': inst.Institution.country_id,
                'city_id': inst.Institution.city_id,
                'type_name': inst.type_name,
                'country_name': inst.country_name,
                'city_name': inst.city_name,
                'documents_count': inst.documents_count,
                'created_date': inst.created_date.isoformat() if inst.created_date else None
            })
        
        return jsonify({
            'institutions': institutions_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    #except Exception as e:
    #    return jsonify({'error': str(e)}), 500

@institutions_bp.route('/api/institutions', methods=['POST'])
def create_institution():
    #try:
        data = request.get_json()
        
        # Validation
        if not data.get('institution'):
            return jsonify({'error': 'Nombre de institución es requerido'}), 400
        
        # Create new institution
        institution = Institution(
            institution=data.get('institution'),
            institution_type=data.get('institution_type') if data.get('institution_type') else None,
            country_id=data.get('country_id') if data.get('country_id') else None,
            city_id=data.get('city_id') if data.get('city_id') else None,
            user_id=1  # Get from session/auth
        )
        
        db.session.add(institution)
        db.session.commit()
        
        return jsonify({'message': 'Institución creada exitosamente', 'id': institution.id}), 201
        
    #except Exception as e:
    #    db.session.rollback()
    #    return jsonify({'error': str(e)}), 500

@institutions_bp.route('/api/institutions/<int:institution_id>', methods=['GET'])
def get_institution(institution_id):
    try:
        institution = Institution.query.get_or_404(institution_id)
        
        return jsonify({
            'id': institution.id,
            'institution': institution.institution,
            'institution_type': institution.institution_type,
            'country_id': institution.country_id,
            'city_id': institution.city_id,
            'created_date': institution.created_date.isoformat() if institution.created_date else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@institutions_bp.route('/api/institutions/<int:institution_id>', methods=['PUT'])
def update_institution(institution_id):
    try:
        institution = Institution.query.get_or_404(institution_id)
        data = request.get_json()
        
        # Update fields
        if 'institution' in data:
            institution.institution = data['institution']
        if 'institution_type' in data:
            institution.institution_type = data['institution_type'] if data['institution_type'] else None
        if 'country_id' in data:
            institution.country_id = data['country_id'] if data['country_id'] else None
        if 'city_id' in data:
            institution.city_id = data['city_id'] if data['city_id'] else None
        
        db.session.commit()
        
        return jsonify({'message': 'Institución actualizada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@institutions_bp.route('/api/institutions/<int:institution_id>', methods=['DELETE'])
def delete_institution(institution_id):
    try:
        institution = Institution.query.get_or_404(institution_id)
        
        # Check if institution has documents
        doc_count = Documents.query.filter(Documents.institution_id == institution_id).count()
        if doc_count > 0:
            return jsonify({'error': f'No se puede eliminar la institución porque tiene {doc_count} documentos asociados'}), 400
        
        db.session.delete(institution)
        db.session.commit()
        
        return jsonify({'message': 'Institución eliminada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@institutions_bp.route('/api/institutions/stats', methods=['GET'])
def get_institutions_stats():
    try:
        # Total institutions
        total = Institution.query.count()
        
        # Institutions this month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = Institution.query.filter(Institution.created_date >= current_month).count()
        
        # Countries count
        countries = db.session.query(Institution.country_id).distinct().filter(Institution.country_id.isnot(None)).count()
        
        # Types count
        types = db.session.query(Institution.institution_type).distinct().filter(Institution.institution_type.isnot(None)).count()
        
        return jsonify({
            'total': total,
            'monthly': monthly,
            'countries': countries,
            'types': types
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@institutions_bp.route('/api/institutions/export', methods=['GET'])
def export_institutions():
    try:
        # Get all institutions with related data
        institutions = db.session.query(Institution)\
            .outerjoin(Institution_type, Institution.institution_type == Institution_type.id)\
            .outerjoin(Country, Institution.country_id == Country.id)\
            .outerjoin(City, Institution.city_id == City.id)\
            .add_columns(
                Institution.id,
                Institution.institution,
                Institution.created_date,
                Institution_type.institution_type.label('type_name'),
                Country.country.label('country_name'),
                City.city.label('city_name')
            ).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Institución', 'Tipo', 'Ciudad', 'País', 'Fecha Creación'
        ])
        
        # Data
        for inst in institutions:
            writer.writerow([
                inst.id,
                inst.institution or '',
                inst.type_name or '',
                inst.city_name or '',
                inst.country_name or '',
                inst.created_date.strftime('%Y-%m-%d %H:%M:%S') if inst.created_date else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=instituciones_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Institution Types endpoints
@institutions_bp.route('/api/institution-types', methods=['GET'])
def get_institution_types():
    try:
        types = Institution_type.query.all()
        return jsonify([{
            'id': t.id,
            'institution_type': t.institution_type
        } for t in types])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@institutions_bp.route('/api/institution-types', methods=['POST'])
def create_institution_type():
    try:
        data = request.get_json()
        
        if not data.get('institution_type'):
            return jsonify({'error': 'Tipo de institución es requerido'}), 400
        
        # Check if type already exists
        existing = Institution_type.query.filter(
            Institution_type.institution_type.ilike(data['institution_type'])
        ).first()
        
        if existing:
            return jsonify({'error': 'Este tipo de institución ya existe'}), 400
        
        institution_type = Institution_type(
            institution_type=data['institution_type'],
            user_id=1  # Get from session/auth
        )
        
        db.session.add(institution_type)
        db.session.commit()
        
        return jsonify({'message': 'Tipo de institución creado exitosamente', 'id': institution_type.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@institutions_bp.route('/api/institution-types/<int:type_id>', methods=['DELETE'])
def delete_institution_type(type_id):
    try:
        institution_type = Institution_type.query.get_or_404(type_id)
        
        # Check if type is being used
        usage_count = Institution.query.filter(Institution.institution_type == type_id).count()
        if usage_count > 0:
            return jsonify({'error': f'No se puede eliminar el tipo porque está siendo usado por {usage_count} instituciones'}), 400
        
        db.session.delete(institution_type)
        db.session.commit()
        
        return jsonify({'message': 'Tipo de institución eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Cities by country endpoint
@institutions_bp.route('/api/cities/<int:country_id>', methods=['GET'])
def get_cities_by_country(country_id):
    try:
        cities = City.query.join(Province_state).filter(
            Province_state.country_id == country_id
        ).all()
        
        return jsonify([{
            'id': c.id,
            'city': c.city
        } for c in cities])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500