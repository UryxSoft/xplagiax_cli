from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import csv
from models.model import ProvinceState, Country
from utils.connections import db
from io import StringIO
from flask import make_response

provinces_bp = Blueprint('provinces_bp', __name__)

@provinces_bp.route('/api/provinces', methods=['GET'])
def list_provinces():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 5))
        sort_field = request.args.get('sort_field', 'created_date')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Filters
        search = request.args.get('search', '').strip()
        country_id = request.args.get('country_id')
        date_from = request.args.get('date_from')
        
        # Base query with JOIN to get country name
        query = db.session.query(
            ProvinceState.id,
            ProvinceState.province_state,
            ProvinceState.country_id,
            ProvinceState.created_date,
            Country.country.label('country_name')
        ).outerjoin(Country, ProvinceState.country_id == Country.id)
        
        # Apply filters
        if search:
            search_filter = ProvinceState.province_state.ilike(f'%{search}%')
            query = query.filter(search_filter)
        
        if country_id:
            query = query.filter(ProvinceState.country_id == country_id)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(ProvinceState.created_date >= date_from_obj)
        
        # Apply sorting
        if sort_field == 'country_name':
            sort_column = Country.country
        else:
            sort_column = getattr(ProvinceState, sort_field, ProvinceState.created_date)
        
        if sort_direction == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Pagination
        total = query.count()
        provinces = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format results
        provinces_list = []
        for province in provinces:
            provinces_list.append({
                'id': province.id,
                'province_state': province.province_state,
                'country_id': province.country_id,
                'country_name': province.country_name,
                'created_date': province.created_date.isoformat() if province.created_date else None
            })
        
        return jsonify({
            'provinces': provinces_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@provinces_bp.route('/api/provinces', methods=['POST'])
def create_province():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('province_state'):
            return jsonify({'error': 'Nombre de provincia/estado es requerido'}), 400
        
        if not data.get('country_id'):
            return jsonify({'error': 'País es requerido'}), 400
        
        # Check if country exists
        country = Country.query.get(data.get('country_id'))
        if not country:
            return jsonify({'error': 'El país seleccionado no existe'}), 400
        
        # Check if province already exists for this country
        existing_province = ProvinceState.query.filter_by(
            province_state=data.get('province_state'),
            country_id=data.get('country_id')
        ).first()
        if existing_province:
            return jsonify({'error': 'La provincia/estado ya existe para este país'}), 400
        
        # Create new province
        province = ProvinceState(
            province_state=data.get('province_state'),
            country_id=data.get('country_id')
        )
        
        db.session.add(province)
        db.session.commit()
        
        return jsonify({'message': 'Provincia/estado creada exitosamente', 'id': province.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@provinces_bp.route('/api/provinces/<int:province_id>', methods=['GET'])
def get_province(province_id):
    try:
        # Query with JOIN to get country information
        province_data = db.session.query(
            ProvinceState.id,
            ProvinceState.province_state,
            ProvinceState.country_id,
            ProvinceState.created_date,
            Country.country.label('country_name')
        ).outerjoin(Country, ProvinceState.country_id == Country.id)\
         .filter(ProvinceState.id == province_id).first()
        
        if not province_data:
            return jsonify({'error': 'Provincia/estado no encontrada'}), 404
        
        return jsonify({
            'id': province_data.id,
            'province_state': province_data.province_state,
            'country_id': province_data.country_id,
            'country_name': province_data.country_name,
            'created_date': province_data.created_date.isoformat() if province_data.created_date else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@provinces_bp.route('/api/provinces/<int:province_id>', methods=['PUT'])
def update_province(province_id):
    try:
        province = ProvinceState.query.get_or_404(province_id)
        data = request.get_json()
        
        # Validation
        if not data.get('province_state'):
            return jsonify({'error': 'Nombre de provincia/estado es requerido'}), 400
        
        if not data.get('country_id'):
            return jsonify({'error': 'País es requerido'}), 400
        
        # Check if country exists
        country = Country.query.get(data.get('country_id'))
        if not country:
            return jsonify({'error': 'El país seleccionado no existe'}), 400
        
        # Check if province name already exists for this country (excluding current province)
        existing_province = ProvinceState.query.filter(
            ProvinceState.province_state == data.get('province_state'),
            ProvinceState.country_id == data.get('country_id'),
            ProvinceState.id != province_id
        ).first()
        
        if existing_province:
            return jsonify({'error': 'El nombre de la provincia/estado ya existe para este país'}), 400
        
        # Update fields
        province.province_state = data.get('province_state')
        province.country_id = data.get('country_id')
        if 'user_id' in data:
            province.user_id = data.get('user_id')
        
        db.session.commit()
        
        return jsonify({'message': 'Provincia/estado actualizada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@provinces_bp.route('/api/provinces/<int:province_id>', methods=['DELETE'])
def delete_province(province_id):
    try:
        province = ProvinceState.query.get_or_404(province_id)
        
        # Check if province is being used in other entities (uncomment if needed)
        # Example: documents, institutions, etc.
        # documents_count = db.session.query(Documents).filter(Documents.province_id == province_id).count()
        # if documents_count > 0:
        #     return jsonify({'error': 'No se puede eliminar la provincia/estado: está siendo usada por otros registros'}), 400
        
        db.session.delete(province)
        db.session.commit()
        
        return jsonify({'message': 'Provincia/estado eliminada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@provinces_bp.route('/api/provinces/stats', methods=['GET'])
def get_provinces_stats():
    try:
        # Total provinces
        total = ProvinceState.query.count()
        
        # Provinces this month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = ProvinceState.query.filter(ProvinceState.created_date >= current_month).count()
        
        # Provinces by country (top 5)
        top_countries = db.session.query(
            Country.country,
            func.count(ProvinceState.id).label('count')
        ).join(ProvinceState, Country.id == ProvinceState.country_id)\
         .group_by(Country.id, Country.country)\
         .order_by(func.count(ProvinceState.id).desc())\
         .limit(5).all()
        
        top_countries_data = [{'country': country, 'count': count} for country, count in top_countries]
        
        return jsonify({
            'total': total,
            'monthly': monthly,
            'top_countries': top_countries_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@provinces_bp.route('/api/provinces/export', methods=['GET'])
def export_provinces():
    try:
        # Get all provinces with country information
        provinces_data = db.session.query(
            ProvinceState.id,
            ProvinceState.province_state,
            ProvinceState.country_id,
            ProvinceState.created_date,
            Country.country.label('country_name')
        ).outerjoin(Country, ProvinceState.country_id == Country.id)\
         .order_by(ProvinceState.created_date.desc()).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Provincia/Estado', 'País ID', 'País', 'Usuario ID', 'Fecha Creación'
        ])
        
        # Data
        for province in provinces_data:
            writer.writerow([
                province.id,
                province.province_state or '',
                province.country_id or '',
                province.country_name or '',
                province.created_date.strftime('%Y-%m-%d %H:%M:%S') if province.created_date else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=provincias_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@provinces_bp.route('/api/provinces/search', methods=['GET'])
def search_provinces():
    """Endpoint específico para búsqueda de provincias/estados (usado en dropdowns)"""
    try:
        search = request.args.get('search', '').strip()
        country_id = request.args.get('country_id')
        limit = int(request.args.get('limit', 10))
        
        query = db.session.query(
            ProvinceState.id,
            ProvinceState.province_state,
            ProvinceState.country_id,
            Country.country.label('country_name')
        ).outerjoin(Country, ProvinceState.country_id == Country.id)
        
        if search:
            query = query.filter(ProvinceState.province_state.ilike(f'%{search}%'))
        
        if country_id:
            query = query.filter(ProvinceState.country_id == country_id)
        
        provinces = query.order_by(ProvinceState.province_state.asc()).limit(limit).all()
        
        return jsonify([{
            'id': province.id,
            'province_state': province.province_state,
            'country_id': province.country_id,
            'country_name': province.country_name
        } for province in provinces])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper endpoint to get provinces by country for dropdowns
@provinces_bp.route('/api/provinces/by-country/<int:country_id>', methods=['GET'])
def get_provinces_by_country(country_id):
    try:
        provinces = ProvinceState.query.filter_by(country_id=country_id)\
                                       .order_by(ProvinceState.province_state.asc()).all()
        
        return jsonify([{
            'id': province.id,
            'province_state': province.province_state,
            'country_id': province.country_id
        } for province in provinces])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper endpoint to get all provinces for dropdowns
@provinces_bp.route('/api/provinces/dropdown', methods=['GET'])
def get_provinces_dropdown():
    try:
        provinces_data = db.session.query(
            ProvinceState.id,
            ProvinceState.province_state,
            ProvinceState.country_id,
            Country.country.label('country_name')
        ).outerjoin(Country, ProvinceState.country_id == Country.id)\
         .order_by(ProvinceState.province_state.asc()).all()
        
        return jsonify([{
            'id': province.id,
            'province_state': province.province_state,
            'country_id': province.country_id,
            'country_name': province.country_name
        } for province in provinces_data])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500