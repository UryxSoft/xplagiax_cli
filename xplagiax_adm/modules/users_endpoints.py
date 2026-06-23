from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime
import csv
from utils.connections import db
from models.model import Users, StoragePlan, StorageAddon, UserAddonSubscription, File, Folder,Institution,Country
from io import StringIO
from flask import make_response

users_bp = Blueprint('users_bp', __name__)

@users_bp.route('/api/users', methods=['GET'])
def list_users():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        sort_field = request.args.get('sort_field', 'created_at')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Filters
        search = request.args.get('search', '').strip()
        user_type = request.args.get('user_type')
        country = request.args.get('country')
        institution = request.args.get('institution')
        status = request.args.get('status')
        
        # Base query con JOINS
        query = db.session.query(
            Users,
            Institution.institution.label('institution_name'),
            Country.country.label('country_name')
        ).outerjoin(Institution, Users.institute == Institution.id
        ).outerjoin(Country, Users.country == Country.id)
        
        # Apply filters
        if search:
            query = query.filter(or_(
                Users.name.ilike(f'%{search}%'),
                Users.lastname.ilike(f'%{search}%'),
                Users.email.ilike(f'%{search}%'),
                Institution.institution.ilike(f'%{search}%'),  # Búsqueda por nombre de institución
                Country.country.ilike(f'%{search}%')            # Búsqueda por nombre de país
            ))
        
        if user_type:
            query = query.filter(Users.user_type == user_type)
            
        if country:
            query = query.filter(Country.country == country)  # Filtrar por nombre de país
            
        if institution:
            query = query.filter(Institution.institution == institution)  # Filtrar por nombre de institución
            
        if status == 'active':
            query = query.filter(Users.is_active == True)
        elif status == 'inactive':
            query = query.filter(Users.is_active == False)
        elif status == 'confirmed':
            query = query.filter(Users.confirmado == True)
        elif status == 'unconfirmed':
            query = query.filter(Users.confirmado == False)
        
        # Pagination
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format results - ahora usamos los nombres en lugar de los IDs
        users_list = []
        for user, institution_name, country_name in results:
            users_list.append({
                'id': user.id,
                'name': user.name,
                'lastname': user.lastname,
                'email': user.email,
                'institute': institution_name,  # Nombre de la institución
                'country': country_name,         # Nombre del país
                'user_type': user.user_type,
                'is_active': user.is_active,
                'confirmado': user.confirmado,
                'created_at': user.created_date.isoformat() if user.created_date else None,
                'storage_plan': user.storage_plan.name if user.storage_plan else None,
                'used_storage': user.used_storage_bytes,
                'total_storage': user.get_total_storage_limit_bytes(),
                'storage_percentage': user.get_storage_usage_percentage()
            })
        
        return jsonify({
            'users': users_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@users_bp.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        
        # Check for duplicate email
        existing_user = Users.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create user
        user = Users(
            email=data['email'],
            name=data.get('name', ''),
            lastname=data.get('lastname', ''),
            institute=data.get('institute', ''),
            country=data.get('country', ''),
            user_type=data.get('user_type'),
            is_active=data.get('is_active', True),
            confirmado=data.get('confirmado', False),
            storage_plan_id=data.get('storage_plan_id'),
            # Password should be hashed in real implementation
            _password_hash=data.get('password', '')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'id': user.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = Users.query.get_or_404(user_id)
        
        # Get user addons
        addons = []
        for subscription in user.addon_subscriptions:
            if subscription.is_active:
                addons.append({
                    'id': subscription.addon.id,
                    'name': subscription.addon.name,
                    'storage_mb': subscription.addon.storage_mb,
                    'expiry_date': subscription.expiry_date.isoformat() if subscription.expiry_date else None
                })
        
        # Get storage info
        storage_info = {
            'used': user.used_storage_bytes,
            'total': user.get_total_storage_limit_bytes(),
            'percentage': user.get_storage_usage_percentage()
        }
        
        return jsonify({
            'user': {
                'id': user.id,
                'name': user.name,
                'lastname': user.lastname,
                'email': user.email,
                'institute': user.institute,
                'country': user.country,
                'user_type': user.user_type,
                'is_active': user.is_active,
                'confirmado': user.confirmado,
                #'created_at': user.created_at.isoformat() if user.created_at else None,
                'storage_plan': user.storage_plan.name if user.storage_plan else None,
                'storage_plan_id': user.storage_plan_id
            },
            'addons': addons,
            'storage_info': storage_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    #try:
        user = Users.query.get_or_404(user_id)
        data = request.get_json()
        
        # Update fields
        if 'email' in data and data['email'] != user.email:
            # Check for duplicate
            if Users.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already exists'}), 400
            user.email = data['email']
        
        if 'name' in data:
            user.name = data['name']
        if 'lastname' in data:
            user.lastname = data['lastname']
        if 'institute' in data:
            user.institute = data['institute']
        if 'country' in data:
            user.country = data['country']
        if 'user_type' in data:
            user.user_type = data['user_type']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'confirmado' in data:
            user.confirmado = data['confirmado']
        if 'storage_plan_id' in data:
            user.storage_plan_id = data['storage_plan_id']
        if 'password' in data:
            # Password should be hashed
            user._password_hash = data['password']
        
        db.session.commit()
        
        return jsonify({'message': 'User updated successfully'})
        
    #except Exception as e:
    #    db.session.rollback()
    #    return jsonify({'error': str(e)}), 500

@users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = Users.query.get_or_404(user_id)
        
        # Check for dependencies
        if user.files or user.folders:
            return jsonify({'error': 'User has associated files or folders'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/api/users/stats', methods=['GET'])
def get_users_stats():
    try:
        # Total users
        total = Users.query.count()
        
        # Active users
        active = Users.query.filter_by(is_active=True).count()
        
        # Confirmed users
        confirmed = Users.query.filter_by(confirmado=True).count()
        
        # Users this month
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = Users.query.filter(Users.created_date >= start_of_month).count()
        
        return jsonify({
            'total': total,
            'active': active,
            'confirmed': confirmed,
            'monthly': monthly
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/api/users/export', methods=['GET'])
def export_users():
    try:
        users = Users.query.all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'ID', 'Nombre', 'Apellido', 'Email', 'Institución', 
            'País', 'Tipo Usuario', 'Activo', 'Confirmado', 'Fecha Registro'
        ])
        
        # Data
        for user in users:
            writer.writerow([
                user.id,
                user.name,
                user.lastname,
                user.email,
                user.institute,
                user.country,
                user.user_type,
                'Sí' if user.is_active else 'No',
                'Sí' if user.confirmado else 'No',
                user.created_at.strftime('%Y-%m-%d') if user.created_at else ''
            ])
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=usuarios.csv'
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/api/storage-plans', methods=['GET'])
def get_storage_plans():
    try:
        plans = StoragePlan.query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'storage_mb': p.base_storage_mb
        } for p in plans])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/api/storage-addons', methods=['GET'])
def get_storage_addons():
    try:
        addons = StorageAddon.query.all()
        return jsonify([{
            'id': a.id,
            'name': a.name,
            'storage_mb': a.storage_mb,
            'price': a.price_monthly_usd
        } for a in addons])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@users_bp.route('/api/institutions', methods=['GET'])
def get_institutions():
    try:
        institutions = Institution.query.all()
        return jsonify([{
            'id': a.id,
            'institution': a.institution,
        } for a in institutions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@users_bp.route('/api/countries', methods=['GET'])
def get_countries():
    try:
        countries = Country.query.all()
        return jsonify([{
            'id': a.id,
            'country': a.country,
        } for a in countries])
    except Exception as e:
        return jsonify({'error': str(e)}), 500