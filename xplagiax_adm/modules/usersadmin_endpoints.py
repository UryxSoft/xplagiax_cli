from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import csv
from io import StringIO
from flask import make_response
from models.model import Users_admin, SSHSession, SessionLog, FileTransfer
from utils.connections import db

usersadmin_bp = Blueprint('usersadmin_bp', __name__)

@usersadmin_bp.route('/api/users_admin', methods=['GET'])
def list_users():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        sort_field = request.args.get('sort_field', 'created_at')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Filters
        search = request.args.get('search', '').strip()
        role = request.args.get('role')
        is_active = request.args.get('is_active')
        
        # Base query
        query = Users_admin.query
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    Users_admin.username.ilike(f'%{search}%'),
                    Users_admin.email.ilike(f'%{search}%')
                )
            )
        
        if role:
            query = query.filter(Users_admin.role == role)
            
        if is_active:
            query = query.filter(Users_admin.is_active == (is_active.lower() == 'true'))
        
        # Apply sorting
        if sort_field == 'username':
            sort_column = Users_admin.username
        elif sort_field == 'email':
            sort_column = Users_admin.email
        elif sort_field == 'role':
            sort_column = Users_admin.role
        elif sort_field == 'last_login':
            sort_column = Users_admin.last_login_at
        else:
            sort_column = Users_admin.created_at
        
        if sort_direction == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Pagination
        total = query.count()
        users = query.paginate(page=page, per_page=per_page)
        
        # Format results
        users_list = [user.to_dict() for user in users.items]
        
        return jsonify({
            'users': users_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': users.pages
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@usersadmin_bp.route('/api/users_admin', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('username'):
            return jsonify({'error': 'Nombre de usuario es requerido'}), 400
        if not data.get('email'):
            return jsonify({'error': 'Email es requerido'}), 400
        if not data.get('password'):
            return jsonify({'error': 'Contraseña es requerida'}), 400
        if not data.get('role'):
            return jsonify({'error': 'Rol es requerido'}), 400
            
        # Check if username or email already exists
        existing_user = Users_admin.query.filter(
            or_(
                Users_admin.username == data['username'],
                Users_admin.email == data['email']
            )
        ).first()
        
        if existing_user:
            return jsonify({'error': 'El nombre de usuario o email ya existe'}), 400
        
        # Create new user
        user = Users_admin(
            username=data['username'],
            email=data['email'],
            role=data['role'],
            is_active=data.get('is_active', True)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuario creado exitosamente',
            'id': user.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@usersadmin_bp.route('/api/users_admin/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = Users_admin.query.get_or_404(user_id)
        return jsonify(user.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@usersadmin_bp.route('/api/users_admin/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        user = Users_admin.query.get_or_404(user_id)
        data = request.get_json()
        
        # Update fields
        if 'username' in data:
            # Check if new username is available
            existing = Users_admin.query.filter(
                Users_admin.username == data['username'],
                Users_admin.id != user_id
            ).first()
            if existing:
                return jsonify({'error': 'Este nombre de usuario ya está en uso'}), 400
            user.username = data['username']
            
        if 'email' in data:
            # Check if new email is available
            existing = Users_admin.query.filter(
                Users_admin.email == data['email'],
                Users_admin.id != user_id
            ).first()
            if existing:
                return jsonify({'error': 'Este email ya está en uso'}), 400
            user.email = data['email']
            
        if 'role' in data:
            user.role = data['role']
            
        if 'is_active' in data:
            user.is_active = data['is_active']
            
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({'message': 'Usuario actualizado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@usersadmin_bp.route('/api/users_admin/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = Users_admin.query.get_or_404(user_id)
        
        # SOLO VERIFICAR SESIONES ACTIVAS (corregido)
        session_count = SSHSession.query.filter(
            SSHSession.user_id == user_id,
            SSHSession.is_active == True  # Solo sesiones activas
        ).count()
        
        if session_count > 0:
            return jsonify({
                'error': f'No se puede eliminar el usuario porque tiene {session_count} sesiones activas'
            }), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'Usuario eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@usersadmin_bp.route('/api/users_admin/stats', methods=['GET'])
def get_users_stats():
    try:
        # Total users
        total = Users_admin.query.count()
        
        # Active users
        active = Users_admin.query.filter(
            Users_admin.is_active == True
        ).count()
        
        # Admin users
        admins = Users_admin.query.filter(
            Users_admin.role == 'admin'
        ).count()
        
        # Users this month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = Users_admin.query.filter(
            Users_admin.created_at >= current_month
        ).count()
        
        return jsonify({
            'total': total,
            'active': active,
            'admins': admins,
            'monthly': monthly
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@usersadmin_bp.route('/api/users_admin/export', methods=['GET'])
def export_users():
    try:
        # Get all users
        users = Users_admin.query.all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Usuario', 'Email', 'Rol', 'Estado', 'Fecha Creación', 'Último Login'
        ])
        
        # Data
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.role,
                'Activo' if user.is_active else 'Inactivo',
                user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                user.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if user.last_login_at else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=usuarios_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@usersadmin_bp.route('/api/users_admin/<int:user_id>/sessions', methods=['GET'])
def get_user_sessions(user_id):
    try:
        sessions = SSHSession.query.filter_by(user_id=user_id).all()
        return jsonify([session.to_dict() for session in sessions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@usersadmin_bp.route('/api/users_admin/<int:user_id>/reset_password', methods=['POST'])
def reset_user_password(user_id):
    try:
        data = request.get_json()
        new_password = data.get('password')
        
        if not new_password:
            return jsonify({'error': 'La nueva contraseña es requerida'}), 400
            
        user = Users_admin.query.get_or_404(user_id)
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'message': 'Contraseña actualizada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500