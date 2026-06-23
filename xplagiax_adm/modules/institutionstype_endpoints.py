from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import csv
from models.model import Institution_type  # Asumiendo que tienes este modelo
from utils.connections import db
from io import StringIO
from flask import make_response

institution_types_bp = Blueprint('institution_types_bp', __name__)

@institution_types_bp.route('/api/institution_types', methods=['GET'])
def list_institution_types():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        sort_field = request.args.get('sort_field', 'created_date')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Filters
        search = request.args.get('search', '').strip()
        date_from = request.args.get('date_from')
        
        # Base query
        query = db.session.query(Institution_type)
        
        # Apply filters
        if search:
            search_filter = Institution_type.institution_type.ilike(f'%{search}%')
            query = query.filter(search_filter)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Institution_type.created_date >= date_from_obj)
        
        # Apply sorting
        sort_column = getattr(Institution_type, sort_field, Institution_type.created_date)
        if sort_direction == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Pagination
        total = query.count()
        institution_types = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format results
        institution_types_list = []
        for inst_type in institution_types:
            institution_types_list.append({
                'id': inst_type.id,
                'institution_type': inst_type.institution_type,
                'created_date': inst_type.created_date.isoformat() if inst_type.created_date else None
            })
        
        return jsonify({
            'institution_types': institution_types_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@institution_types_bp.route('/api/institution_types', methods=['POST'])
def create_institution_type():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('institution_type'):
            return jsonify({'error': 'Tipo de institución es requerido'}), 400
        
        # Check if already exists
        existing = Institution_type.query.filter_by(
            institution_type=data.get('institution_type')
        ).first()
        
        if existing:
            return jsonify({'error': 'Este tipo de institución ya existe'}), 400
        
        # Create new institution type
        institution_type = Institution_type(
            institution_type=data.get('institution_type')
            #user_id=1  # Get from session/auth - replace with actual user ID
        )
        
        db.session.add(institution_type)
        db.session.commit()
        
        return jsonify({
            'message': 'Tipo de institución creado exitosamente', 
            'id': institution_type.id
        }), 201
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@institution_types_bp.route('/api/institution_types/<int:institution_type_id>', methods=['GET'])
def get_institution_type(institution_type_id):
    try:
        institution_type = Institution_type.query.get_or_404(institution_type_id)
        
        return jsonify({
            'id': institution_type.id,
            'institution_type': institution_type.institution_type,
            'created_date': institution_type.created_date.isoformat() if institution_type.created_date else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@institution_types_bp.route('/api/institution_types/<int:institution_type_id>', methods=['PUT'])
def update_institution_type(institution_type_id):
    #try:
        institution_type = Institution_type.query.get_or_404(institution_type_id)
        data = request.get_json()
        
        # Validation
        if not data.get('institution_type'):
            return jsonify({'error': 'Tipo de institución es requerido'}), 400
        
        # Check if name already exists (excluding current record)
        existing = Institution_type.query.filter(
            and_(
                Institution_type.institution_type == data.get('institution_type'),
                Institution_type.id != institution_type_id
            )
        ).first()
        
        if existing:
            return jsonify({'error': 'Este tipo de institución ya existe'}), 400
        
        # Update fields
        institution_type.institution_type = data.get('institution_type')
        
        db.session.commit()
        
        return jsonify({'message': 'Tipo de institución actualizado exitosamente'})
        
    #except Exception as e:
    #    db.session.rollback()
    #    return jsonify({'error': str(e)}), 500

@institution_types_bp.route('/api/institution_types/<int:institution_type_id>', methods=['DELETE'])
def delete_institution_type(institution_type_id):
    try:
        institution_type = Institution_type.query.get_or_404(institution_type_id)
        
        # Optional: Check if this type is being used by any institutions
        # You might want to add a check here to prevent deletion if it's in use
        # Example:
        # from models.model import Institution
        # institutions_using_type = Institution.query.filter_by(type_id=institution_type_id).count()
        # if institutions_using_type > 0:
        #     return jsonify({'error': f'No se puede eliminar. Hay {institutions_using_type} instituciones usando este tipo.'}), 400
        
        db.session.delete(institution_type)
        db.session.commit()
        
        return jsonify({'message': 'Tipo de institución eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@institution_types_bp.route('/api/institution_types/stats', methods=['GET'])
def get_institution_types_stats():
    try:
        # Total institution types
        total = Institution_type.query.count()
        
        # Institution types created this month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = Institution_type.query.filter(
            Institution_type.created_date >= current_month
        ).count()
        
        # Active institution types (all are considered active unless you have a status field)
        active = total
        
        return jsonify({
            'total': total,
            'monthly': monthly,
            'active': active
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@institution_types_bp.route('/api/institution_types/export', methods=['GET'])
def export_institution_types():
    try:
        # Get all institution types
        institution_types = Institution_type.query.order_by(
            Institution_type.created_date.desc()
        ).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Tipo de Institución', 'Usuario ID', 'Fecha Creación'
        ])
        
        # Data
        for inst_type in institution_types:
            writer.writerow([
                inst_type.id,
                inst_type.institution_type or '',
                inst_type.user_id or '',
                inst_type.created_date.strftime('%Y-%m-%d %H:%M:%S') if inst_type.created_date else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=tipos_institucion_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper endpoint to get all institution types for dropdowns
@institution_types_bp.route('/api/institution_types/dropdown', methods=['GET'])
def get_institution_types_dropdown():
    try:
        institution_types = Institution_type.query.order_by(
            Institution_type.institution_type.asc()
        ).all()
        
        return jsonify([{
            'id': inst_type.id,
            'institution_type': inst_type.institution_type
        } for inst_type in institution_types])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500