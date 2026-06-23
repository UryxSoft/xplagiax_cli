from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import csv
from models.model import Doctype  # Asumiendo que tienes este modelo
from utils.connections import db
from io import StringIO
from flask import make_response

doctype_bp = Blueprint('doctype_bp', __name__)

@doctype_bp.route('/api/doctypes', methods=['GET'])
def list_doctypes():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        sort_field = request.args.get('sort_field', 'created_date')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Filters
        search = request.args.get('search', '').strip()
        date_from = request.args.get('date_from')
        
        # Base query
        query = db.session.query(Doctype)
        
        # Apply filters
        if search:
            search_filter = Doctype.doctype.ilike(f'%{search}%')
            query = query.filter(search_filter)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Doctype.created_date >= date_from_obj)
        
        # Apply sorting
        sort_column = getattr(Doctype, sort_field, Doctype.created_date)
        if sort_direction == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Pagination
        total = query.count()
        doctypes = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format results
        doctypes_list = []
        for doctype in doctypes:
            doctypes_list.append({
                'id': doctype.id,
                'doctype': doctype.doctype,
                'user_id': doctype.user_id,
                'created_date': doctype.created_date.isoformat() if doctype.created_date else None
            })
        
        return jsonify({
            'doctypes': doctypes_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@doctype_bp.route('/api/doctypes', methods=['POST'])
def create_doctype():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('doctype'):
            return jsonify({'error': 'Tipo de documento es requerido'}), 400
        
        # Check if already exists
        existing = Doctype.query.filter_by(
            doctype=data.get('doctype')
        ).first()
        
        if existing:
            return jsonify({'error': 'Este tipo de documento ya existe'}), 400
        
        # Create new doctype
        doctype = Doctype(
            doctype=data.get('doctype'),
            user_id=1  # Get from session/auth - replace with actual user ID
        )
        
        db.session.add(doctype)
        db.session.commit()
        
        return jsonify({
            'message': 'Tipo de documento creado exitosamente', 
            'id': doctype.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@doctype_bp.route('/api/doctypes/<int:doctype_id>', methods=['GET'])
def get_doctype(doctype_id):
    try:
        doctype = Doctype.query.get_or_404(doctype_id)
        
        return jsonify({
            'id': doctype.id,
            'doctype': doctype.doctype,
            'user_id': doctype.user_id,
            'created_date': doctype.created_date.isoformat() if doctype.created_date else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@doctype_bp.route('/api/doctypes/<int:doctype_id>', methods=['PUT'])
def update_doctype(doctype_id):
    try:
        doctype = Doctype.query.get_or_404(doctype_id)
        data = request.get_json()
        
        # Validation
        if not data.get('doctype'):
            return jsonify({'error': 'Tipo de documento es requerido'}), 400
        
        # Check if name already exists (excluding current record)
        existing = Doctype.query.filter(
            and_(
                Doctype.doctype == data.get('doctype'),
                Doctype.id != doctype_id
            )
        ).first()
        
        if existing:
            return jsonify({'error': 'Este tipo de documento ya existe'}), 400
        
        # Update fields
        doctype.doctype = data.get('doctype')
        
        db.session.commit()
        
        return jsonify({'message': 'Tipo de documento actualizado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@doctype_bp.route('/api/doctypes/<int:doctype_id>', methods=['DELETE'])
def delete_doctype(doctype_id):
    try:
        doctype = Doctype.query.get_or_404(doctype_id)
        
        # Optional: Check if this doctype is being used by any documents
        # You might want to add a check here to prevent deletion if it's in use
        # Example:
        # from models.model import Document
        # documents_using_type = Document.query.filter_by(doctype_id=doctype_id).count()
        # if documents_using_type > 0:
        #     return jsonify({'error': f'No se puede eliminar. Hay {documents_using_type} documentos usando este tipo.'}), 400
        
        db.session.delete(doctype)
        db.session.commit()
        
        return jsonify({'message': 'Tipo de documento eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@doctype_bp.route('/api/doctypes/stats', methods=['GET'])
def get_doctypes_stats():
    try:
        # Total doctypes
        total = Doctype.query.count()
        
        # Doctypes created this month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = Doctype.query.filter(
            Doctype.created_date >= current_month
        ).count()
        
        # Active doctypes (all are considered active unless you have a status field)
        active = total
        
        return jsonify({
            'total': total,
            'monthly': monthly,
            'active': active
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@doctype_bp.route('/api/doctypes/export', methods=['GET'])
def export_doctypes():
    try:
        # Get all doctypes
        doctypes = Doctype.query.order_by(
            Doctype.created_date.desc()
        ).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Tipo de Documento', 'Usuario ID', 'Fecha Creación'
        ])
        
        # Data
        for doctype in doctypes:
            writer.writerow([
                doctype.id,
                doctype.doctype or '',
                doctype.user_id or '',
                doctype.created_date.strftime('%Y-%m-%d %H:%M:%S') if doctype.created_date else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=tipos_documento_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper endpoint to get all doctypes for dropdowns
@doctype_bp.route('/api/doctypes/dropdown', methods=['GET'])
def get_doctypes_dropdown():
    try:
        doctypes = Doctype.query.order_by(
            Doctype.doctype.asc()
        ).all()
        
        return jsonify([{
            'id': doctype.id,
            'doctype': doctype.doctype
        } for doctype in doctypes])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500