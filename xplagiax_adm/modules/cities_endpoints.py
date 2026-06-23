from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import csv
from models.model import City, ProvinceState
from utils.connections import db
from io import StringIO
from flask import make_response

cities_bp = Blueprint('cities_bp', __name__)

@cities_bp.route('/api/cities', methods=['GET'])
def list_cities():
    try:
        # Validar y corregir parámetros de paginación
        page = max(1, int(request.args.get('page', 1)))  # Asegurar que page >= 1
        per_page = max(1, min(100, int(request.args.get('per_page', 20))))  # Limitar per_page entre 1 y 100
        
        sort_field = request.args.get('sort_field', 'created_date')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Filters
        search = request.args.get('search', '').strip()
        date_from = request.args.get('date_from')
        state_id = request.args.get('state_id')
        
        # Base query with join to get state name
        query = db.session.query(City).outerjoin(ProvinceState, City.state_id == ProvinceState.id)
        
        # Apply filters
        if search:
            search_filter = or_(
                City.city.ilike(f'%{search}%'),
                ProvinceState.province_state.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(City.created_date >= date_from_obj)
            except ValueError:
                return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
        
        if state_id:
            try:
                state_id = int(state_id)
                query = query.filter(City.state_id == state_id)
            except ValueError:
                return jsonify({'error': 'ID de estado inválido'}), 400
        
        # Apply sorting - validar que el campo existe
        if hasattr(City, sort_field):
            sort_column = getattr(City, sort_field)
        else:
            sort_column = City.created_date  # Campo por defecto
            
        if sort_direction.lower() == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Get total count before pagination
        total = query.count()
        
        # Calculate offset (asegurar que sea >= 0)
        offset = max(0, (page - 1) * per_page)
        
        # Apply pagination
        cities = query.offset(offset).limit(per_page).all()
        
        # Format results
        cities_list = []
        for city in cities:
            # Get state name if exists
            state_name = None
            if city.state_id:
                state = ProvinceState.query.get(city.state_id)
                state_name = state.province_state if state else None
            
            cities_list.append({
                'id': city.id,
                'city': city.city,
                'state_id': city.state_id,
                'state_name': state_name,
                'created_date': city.created_date.isoformat() if city.created_date else None
            })
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return jsonify({
            'cities': cities_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        })
        
    except ValueError as ve:
        return jsonify({'error': f'Parámetro inválido: {str(ve)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cities_bp.route('/api/cities', methods=['POST'])
def create_city():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('city'):
            return jsonify({'error': 'Nombre de la ciudad es requerido'}), 400
        
        # Check if city already exists in the same state
        existing_city = City.query.filter_by(
            city=data.get('city'),
            state_id=data.get('state_id')
        ).first()
        
        if existing_city:
            return jsonify({'error': 'La ciudad ya existe en este estado/provincia'}), 400
        
        # Validate state exists if provided
        if data.get('state_id'):
            state = ProvinceState.query.get(data.get('state_id'))
            if not state:
                return jsonify({'error': 'El estado/provincia especificado no existe'}), 400
        
        # Create new city
        city = City(
            city=data.get('city'),
            state_id=data.get('state_id'),
            user_id=data.get('user_id')
        )
        
        db.session.add(city)
        db.session.commit()
        
        return jsonify({'message': 'Ciudad creada exitosamente', 'id': city.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cities_bp.route('/api/cities/<int:city_id>', methods=['GET'])
def get_city(city_id):
    try:
        city = City.query.get_or_404(city_id)
        
        # Get state name if exists
        state_name = None
        if city.state_id:
            state = ProvinceState.query.get(city.state_id)
            state_name = state.province_state if state else None
        
        return jsonify({
            'id': city.id,
            'city': city.city,
            'state_id': city.state_id,
            'state_name': state_name,
            'user_id': city.user_id,
            'created_date': city.created_date.isoformat() if city.created_date else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cities_bp.route('/api/cities/<int:city_id>', methods=['PUT'])
def update_city(city_id):
    try:
        city = City.query.get_or_404(city_id)
        data = request.get_json()
        
        # Validation
        if not data.get('city'):
            return jsonify({'error': 'Nombre de la ciudad es requerido'}), 400
        
        # Check if city name already exists in the same state (excluding current city)
        existing_city = City.query.filter(
            City.city == data.get('city'),
            City.state_id == data.get('state_id'),
            City.id != city_id
        ).first()
        
        if existing_city:
            return jsonify({'error': 'El nombre de la ciudad ya existe en este estado/provincia'}), 400
        
        # Validate state exists if provided
        if data.get('state_id'):
            state = ProvinceState.query.get(data.get('state_id'))
            if not state:
                return jsonify({'error': 'El estado/provincia especificado no existe'}), 400
        
        # Update fields
        city.city = data.get('city')
        city.state_id = data.get('state_id')
        city.user_id = data.get('user_id')
        
        db.session.commit()
        
        return jsonify({'message': 'Ciudad actualizada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cities_bp.route('/api/cities/<int:city_id>', methods=['DELETE'])
def delete_city(city_id):
    try:
        city = City.query.get_or_404(city_id)
        
        # Check if city is being used in other tables
        # Uncomment if you have relationships
        # documents_count = db.session.query(Documents).filter(Documents.city_id == city_id).count()
        # if documents_count > 0:
        #     return jsonify({'error': 'No se puede eliminar la ciudad: está siendo usada por documentos'}), 400
        
        db.session.delete(city)
        db.session.commit()
        
        return jsonify({'message': 'Ciudad eliminada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@cities_bp.route('/api/cities/stats', methods=['GET'])
def get_cities_stats():
    try:
        # Total cities
        total = City.query.count()
        
        # Cities this month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = City.query.filter(City.created_date >= current_month).count()
        
        # Most recent city
        latest_city = City.query.order_by(City.created_date.desc()).first()
        latest_name = latest_city.city if latest_city else '-'
        
        return jsonify({
            'total': total,
            'monthly': monthly,
            'latest': latest_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cities_bp.route('/api/cities/export', methods=['GET'])
def export_cities():
    try:
        # Get all cities with state information
        cities = db.session.query(City).outerjoin(ProvinceState, City.state_id == ProvinceState.id).order_by(City.created_date.desc()).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Ciudad', 'Estado/Provincia', 'Usuario ID', 'Fecha Creación'
        ])
        
        # Data
        for city in cities:
            state_name = ''
            if city.state_id:
                state = ProvinceState.query.get(city.state_id)
                state_name = state.province_state if state else ''
            
            writer.writerow([
                city.id,
                city.city or '',
                state_name,
                city.user_id or '',
                city.created_date.strftime('%Y-%m-%d %H:%M:%S') if city.created_date else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=ciudades_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cities_bp.route('/api/cities/search', methods=['GET'])
def search_cities():
    """Endpoint específico para búsqueda de ciudades (usado en dropdowns)"""
    try:
        search = request.args.get('search', '').strip()
        state_id = request.args.get('state_id')
        limit = int(request.args.get('limit', 10))
        
        query = City.query
        
        if search:
            query = query.filter(City.city.ilike(f'%{search}%'))
        
        if state_id:
            query = query.filter(City.state_id == state_id)
        
        cities = query.order_by(City.city.asc()).limit(limit).all()
        
        return jsonify([{
            'id': city.id,
            'city': city.city,
            'state_id': city.state_id
        } for city in cities])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@cities_bp.route('/api/cities/dropdown', methods=['GET'])
def get_cities_dropdown():
    """Helper endpoint to get all cities for dropdowns"""
    try:
        state_id = request.args.get('state_id')
        
        query = City.query
        if state_id:
            query = query.filter(City.state_id == state_id)
        
        cities = query.order_by(City.city.asc()).all()
        
        return jsonify([{
            'id': city.id,
            'city': city.city,
            'state_id': city.state_id
        } for city in cities])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@cities_bp.route('/api/cities/dropdown/<int:country_id>', methods=['GET'])
def get_cities_by_country(country_id):
    """Get cities by country ID"""
    cities = City.query.join(ProvinceState, City.state_id == ProvinceState.id)\
                      .filter(ProvinceState.country_id == country_id)\
                      .order_by(City.city.asc()).all()
    
    return jsonify([{
        'id': city.id,
        'city': city.city
    } for city in cities])
    #except Exception as e:
    #    return jsonify({'error': str(e)}), 500