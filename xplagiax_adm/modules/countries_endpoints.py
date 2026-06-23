from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import csv
from models.model import Country
from utils.connections import db
from io import StringIO
from flask import make_response

countries_bp = Blueprint('countries_bp', __name__)

@countries_bp.route('/api/countries', methods=['GET'])
def list_countries():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        sort_field = request.args.get('sort_field', 'created_date')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Filters
        search = request.args.get('search', '').strip()
        date_from = request.args.get('date_from')
        
        # Base query
        query = db.session.query(Country)
        
        # Apply filters
        if search:
            search_filter = Country.country.ilike(f'%{search}%')
            query = query.filter(search_filter)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Country.created_date >= date_from_obj)
        
        # Apply sorting
        sort_column = getattr(Country, sort_field, Country.created_date)
        if sort_direction == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Pagination
        total = query.count()
        countries = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format results
        countries_list = []
        for country in countries:
            countries_list.append({
                'id': country.id,
                'country': country.country,
                'created_date': country.created_date.isoformat() if country.created_date else None
            })
        
        return jsonify({
            'countries': countries_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@countries_bp.route('/api/countries', methods=['POST'])
def create_country():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('country'):
            return jsonify({'error': 'Nombre del país es requerido'}), 400
        
        # Check if country already exists
        existing_country = Country.query.filter_by(country=data.get('country')).first()
        if existing_country:
            return jsonify({'error': 'El país ya existe'}), 400
        
        # Create new country
        country = Country(
            country=data.get('country')
        )
        
        db.session.add(country)
        db.session.commit()
        
        return jsonify({'message': 'País creado exitosamente', 'id': country.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@countries_bp.route('/api/countries/<int:country_id>', methods=['GET'])
def get_country(country_id):
    try:
        country = Country.query.get_or_404(country_id)
        
        return jsonify({
            'id': country.id,
            'country': country.country,
            'created_date': country.created_date.isoformat() if country.created_date else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@countries_bp.route('/api/countries/<int:country_id>', methods=['PUT'])
def update_country(country_id):
    try:
        country = Country.query.get_or_404(country_id)
        data = request.get_json()
        
        # Validation
        if not data.get('country'):
            return jsonify({'error': 'Nombre del país es requerido'}), 400
        
        # Check if country name already exists (excluding current country)
        existing_country = Country.query.filter(
            Country.country == data.get('country'),
            Country.id != country_id
        ).first()
        
        if existing_country:
            return jsonify({'error': 'El nombre del país ya existe'}), 400
        
        # Update fields
        country.country = data.get('country')
        
        db.session.commit()
        
        return jsonify({'message': 'País actualizado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@countries_bp.route('/api/countries/<int:country_id>', methods=['DELETE'])
def delete_country(country_id):
    try:
        country = Country.query.get_or_404(country_id)
        
        # Check if country is being used in documents
        # Uncomment if you have the Documents model relationship
        # documents_count = db.session.query(Documents).filter(Documents.country_id == country_id).count()
        # if documents_count > 0:
        #     return jsonify({'error': 'No se puede eliminar el país: está siendo usado por documentos'}), 400
        
        db.session.delete(country)
        db.session.commit()
        
        return jsonify({'message': 'País eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@countries_bp.route('/api/countries/stats', methods=['GET'])
def get_countries_stats():
    try:
        # Total countries
        total = Country.query.count()
        
        # Countries this month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = Country.query.filter(Country.created_date >= current_month).count()
        
        # Countries by user (top 5)
        top_users = db.session.query(
            func.count(Country.id).label('count')
        ).order_by(func.count(Country.id).desc()).limit(5).all()
        
        return jsonify({
            'total': total,
            'monthly': monthly,
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@countries_bp.route('/api/countries/export', methods=['GET'])
def export_countries():
    try:
        # Get all countries
        countries = Country.query.order_by(Country.created_date.desc()).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'País', 'Usuario ID', 'Fecha Creación'
        ])
        
        # Data
        for country in countries:
            writer.writerow([
                country.id,
                country.country or '',
                country.user_id or '',
                country.created_date.strftime('%Y-%m-%d %H:%M:%S') if country.created_date else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=paises_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@countries_bp.route('/api/countries/search', methods=['GET'])
def search_countries():
    """Endpoint específico para búsqueda de países (usado en dropdowns)"""
    try:
        search = request.args.get('search', '').strip()
        limit = int(request.args.get('limit', 10))
        
        query = Country.query
        
        if search:
            query = query.filter(Country.country.ilike(f'%{search}%'))
        
        countries = query.order_by(Country.country.asc()).limit(limit).all()
        
        return jsonify([{
            'id': country.id,
            'country': country.country
        } for country in countries])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Helper endpoint to get all countries for dropdowns
@countries_bp.route('/api/countries/dropdown', methods=['GET'])
def get_institution_types_dropdown():
    try:
        countries = Country.query.order_by(
            Country.country.asc()
        ).all()
        
        return jsonify([{
            'id': inst_type.id,
            'country': inst_type.country
        } for inst_type in countries])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500