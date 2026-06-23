from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import csv
from models.model import Service,Users_admin
from utils.connections import db
from io import StringIO
from flask import make_response
import bcrypt

settings_bp = Blueprint('settings_bp', __name__)

@settings_bp.route('/api/services', methods=['GET'])
def list_services():
    try:
        # Validar y corregir parámetros de paginación
        page = max(1, int(request.args.get('page', 1)))
        per_page = max(1, min(100, int(request.args.get('per_page', 20))))
        
        sort_field = request.args.get('sort_field', 'created_at')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Filters
        search = request.args.get('search', '').strip()
        date_from = request.args.get('date_from')
        service_type = request.args.get('service_type')
        is_active = request.args.get('is_active')
        is_monitored = request.args.get('is_monitored')
        
        # Base query with join to get user name
        query = db.session.query(Service).outerjoin(Users_admin, Service.created_by == Users_admin.id)
        
        # Apply filters
        if search:
            search_filter = or_(
                Service.name.ilike(f'%{search}%'),
                Service.display_name.ilike(f'%{search}%'),
                Service.host.ilike(f'%{search}%'),
                Service.service_type.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Service.created_at >= date_from_obj)
            except ValueError:
                return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
        
        if service_type:
            query = query.filter(Service.service_type == service_type)
            
        if is_active is not None:
            query = query.filter(Service.is_active == (is_active.lower() == 'true'))
            
        if is_monitored is not None:
            query = query.filter(Service.is_monitored == (is_monitored.lower() == 'true'))
        
        # Apply sorting
        if hasattr(Service, sort_field):
            sort_column = getattr(Service, sort_field)
        else:
            sort_column = Service.created_at
            
        if sort_direction.lower() == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Get total count before pagination
        total = query.count()
        
        # Calculate offset
        offset = max(0, (page - 1) * per_page)
        
        # Apply pagination
        services = query.offset(offset).limit(per_page).all()
        
        # Format results
        services_list = []
        for service in services:
            # Get creator name if exists
            creator_name = None
            if service.created_by:
                user = Users_admin.query.get(service.created_by)
                creator_name = user.username if user else None
            
            services_list.append({
                'id': service.id,
                'name': service.name,
                'display_name': service.display_name,
                'host': service.host,
                'port': service.port,
                'service_type': service.service_type,
                'endpoint': service.endpoint,
                'timeout': service.timeout,
                'icon': service.icon,
                'username': service.username,
                'is_active': service.is_active,
                'is_monitored': service.is_monitored,
                'created_at': service.created_at.isoformat() if service.created_at else None,
                'updated_at': service.updated_at.isoformat() if service.updated_at else None,
                'created_by': service.created_by,
                'creator_name': creator_name
            })
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return jsonify({
            'services': services_list,
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

@settings_bp.route('/api/services', methods=['POST'])
def create_service():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('name'):
            return jsonify({'error': 'Nombre del servicio es requerido'}), 400
        if not data.get('display_name'):
            return jsonify({'error': 'Nombre de visualización es requerido'}), 400
        if not data.get('host'):
            return jsonify({'error': 'Host es requerido'}), 400
        if not data.get('port'):
            return jsonify({'error': 'Puerto es requerido'}), 400
        if not data.get('service_type'):
            return jsonify({'error': 'Tipo de servicio es requerido'}), 400
        
        # Check if service name already exists
        existing_service = Service.query.filter_by(name=data.get('name')).first()
        if existing_service:
            return jsonify({'error': 'Ya existe un servicio con este nombre'}), 400
        
        # Encrypt password if provided
        password_encrypted = None
        if data.get('password'):
            password_encrypted = bcrypt.hashpw(data.get('password').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create new service
        service = Service(
            name=data.get('name'),
            display_name=data.get('display_name'),
            host=data.get('host'),
            port=int(data.get('port')),
            service_type=data.get('service_type'),
            endpoint=data.get('endpoint'),
            timeout=int(data.get('timeout', 5)),
            icon=data.get('icon', 'fas fa-server'),
            username=data.get('username'),
            password_encrypted=password_encrypted,
            extra_config=data.get('extra_config'),
            is_active=data.get('is_active', True),
            is_monitored=data.get('is_monitored', True),
            created_by=data.get('created_by')
        )
        
        db.session.add(service)
        db.session.commit()
        
        return jsonify({'message': 'Servicio creado exitosamente', 'id': service.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/services/<int:service_id>', methods=['GET'])
def get_service(service_id):
    try:
        service = Service.query.get_or_404(service_id)
        
        # Get creator name if exists
        creator_name = None
        if service.created_by:
            user = Users_admin.query.get(service.created_by)
            creator_name = user.username if user else None
        
        return jsonify({
            'id': service.id,
            'name': service.name,
            'display_name': service.display_name,
            'host': service.host,
            'port': service.port,
            'service_type': service.service_type,
            'endpoint': service.endpoint,
            'timeout': service.timeout,
            'icon': service.icon,
            'username': service.username,
            'is_active': service.is_active,
            'is_monitored': service.is_monitored,
            'extra_config': service.extra_config,
            'created_at': service.created_at.isoformat() if service.created_at else None,
            'updated_at': service.updated_at.isoformat() if service.updated_at else None,
            'created_by': service.created_by,
            'creator_name': creator_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/services/<int:service_id>', methods=['PUT'])
def update_service(service_id):
    try:
        service = Service.query.get_or_404(service_id)
        data = request.get_json()
        
        # Validation
        if not data.get('name'):
            return jsonify({'error': 'Nombre del servicio es requerido'}), 400
        if not data.get('display_name'):
            return jsonify({'error': 'Nombre de visualización es requerido'}), 400
        if not data.get('host'):
            return jsonify({'error': 'Host es requerido'}), 400
        if not data.get('port'):
            return jsonify({'error': 'Puerto es requerido'}), 400
        if not data.get('service_type'):
            return jsonify({'error': 'Tipo de servicio es requerido'}), 400
        
        # Check if service name already exists (excluding current service)
        existing_service = Service.query.filter(
            Service.name == data.get('name'),
            Service.id != service_id
        ).first()
        
        if existing_service:
            return jsonify({'error': 'Ya existe un servicio con este nombre'}), 400
        
        # Update password if provided
        if data.get('password'):
            service.password_encrypted = bcrypt.hashpw(data.get('password').encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update fields
        service.name = data.get('name')
        service.display_name = data.get('display_name')
        service.host = data.get('host')
        service.port = int(data.get('port'))
        service.service_type = data.get('service_type')
        service.endpoint = data.get('endpoint')
        service.timeout = int(data.get('timeout', 5))
        service.icon = data.get('icon', 'fas fa-server')
        service.username = data.get('username')
        service.extra_config = data.get('extra_config')
        service.is_active = data.get('is_active', True)
        service.is_monitored = data.get('is_monitored', True)
        service.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({'message': 'Servicio actualizado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/services/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    try:
        service = Service.query.get_or_404(service_id)
        
        # Check if service is being used in other tables
        # Add relationship checks here if needed
        
        db.session.delete(service)
        db.session.commit()
        
        return jsonify({'message': 'Servicio eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/services/stats', methods=['GET'])
def get_services_stats():
    try:
        # Total services
        total = Service.query.count()
        
        # Active services
        active = Service.query.filter_by(is_active=True).count()
        
        # Monitored services
        monitored = Service.query.filter_by(is_monitored=True).count()
        
        # Services this month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = Service.query.filter(Service.created_at >= current_month).count()
        
        # Most common service type
        most_common_type = db.session.query(
            Service.service_type,
            func.count(Service.id).label('count')
        ).group_by(Service.service_type).order_by(func.count(Service.id).desc()).first()
        
        return jsonify({
            'total': total,
            'active': active,
            'monitored': monitored,
            'monthly': monthly,
            'most_common_type': most_common_type.service_type if most_common_type else '-'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/services/export', methods=['GET'])
def export_services():
    try:
        # Get all services with user information
        services = db.session.query(Service).outerjoin(Users_admin, Service.created_by == Users_admin.id).order_by(Service.created_at.desc()).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Nombre', 'Nombre Display', 'Host', 'Puerto', 'Tipo', 'Endpoint', 
            'Timeout', 'Usuario', 'Activo', 'Monitoreado', 'Creado Por', 'Fecha Creación'
        ])
        
        # Data
        for service in services:
            creator_name = ''
            if service.created_by:
                user = Users_admin.query.get(service.created_by)
                creator_name = user.username if user else ''
            
            writer.writerow([
                service.id,
                service.name or '',
                service.display_name or '',
                service.host or '',
                service.port or '',
                service.service_type or '',
                service.endpoint or '',
                service.timeout or '',
                service.username or '',
                'Sí' if service.is_active else 'No',
                'Sí' if service.is_monitored else 'No',
                creator_name,
                service.created_at.strftime('%Y-%m-%d %H:%M:%S') if service.created_at else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=servicios_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/services/types', methods=['GET'])
def get_service_types():
    """Get unique service types for dropdown"""
    try:
        types = db.session.query(Service.service_type).distinct().filter(Service.service_type.isnot(None)).all()
        return jsonify([type_row.service_type for type_row in types])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/services/test/<int:service_id>', methods=['POST'])
def test_service_connection(service_id):
    """Test service connection"""
    try:
        service = Service.query.get_or_404(service_id)
        
        # Here you would implement the actual connection test
        # For now, we'll return a mock response
        import socket
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(service.timeout)
            result = sock.connect_ex((service.host, service.port))
            sock.close()
            
            if result == 0:
                return jsonify({'success': True, 'message': 'Conexión exitosa'})
            else:
                return jsonify({'success': False, 'message': 'No se pudo conectar al servicio'})
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error de conexión: {str(e)}'})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500