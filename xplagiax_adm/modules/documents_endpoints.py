from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import csv
from models.model import Documents, Doctype, Country, Institution, Lenguage,DocumentAnalysis
from utils.connections import db
from io import StringIO
from flask import make_response

documents_bp = Blueprint('documents_bp', __name__)

@documents_bp.route('/api/documents', methods=['GET'])
def list_documents():
    #try:
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    sort_field = request.args.get('sort_field', 'created_date')
    sort_direction = request.args.get('sort_direction', 'desc')
    
    # Filters
    search = request.args.get('search', '').strip()
    doctype_id = request.args.get('doctype_id')
    country_id = request.args.get('country_id')
    institution_id = request.args.get('institution_id')
    lenguage_id = request.args.get('lenguage_id')
    date_from = request.args.get('date_from')
    
    # Base query with joins
    query = db.session.query(Documents)\
        .outerjoin(Doctype, Documents.doctype_id == Doctype.id)\
        .outerjoin(Country, Documents.country_id == Country.id)\
        .outerjoin(Institution, Documents.institution_id == Institution.id)\
        .outerjoin(Lenguage, Documents.lenguage_id == Lenguage.id)\
        .add_columns(
            Documents.id,
            Documents.title,
            Documents.author,
            Documents.content,
            Documents.rena,
            Documents.theme,
            Documents.created_date,
            Doctype.doctype.label('doctype_name'),
            Country.country.label('country_name'),
            Institution.institution.label('institution_name'),
            Lenguage.lenguage_name.label('language_name')
        )
    
    # Apply filters
    if search:
        search_filter = or_(
            Documents.title.ilike(f'%{search}%'),
            Documents.author.ilike(f'%{search}%'),
            Documents.content.ilike(f'%{search}%'),
            Documents.theme.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    if doctype_id:
        query = query.filter(Documents.doctype_id == doctype_id)
    
    if country_id:
        query = query.filter(Documents.country_id == country_id)
        
    if institution_id:
        query = query.filter(Documents.institution_id == institution_id)
        
    if lenguage_id:
        query = query.filter(Documents.lenguage_id == lenguage_id)
        
    if date_from:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(Documents.created_date >= date_from_obj)
    
    # Apply sorting
    sort_column = getattr(Documents, sort_field, Documents.created_date)
    if sort_direction == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Pagination
    total = query.count()
    documents = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Format results
    documents_list = []
    for doc in documents:
        documents_list.append({
            'id': doc.id,
            'title': doc.title,
            'author': doc.author,
            'content': doc.content[:200] + '...' if doc.content and len(doc.content) > 200 else doc.content,
            'rena': doc.rena,
            'theme': doc.theme,
            'doctype_id': doc.Documents.doctype_id,
            'country_id': doc.Documents.country_id,
            'institution_id': doc.Documents.institution_id,
            'lenguage_id': doc.Documents.lenguage_id,
            'doctype_name': doc.doctype_name,
            'country_name': doc.country_name,
            'institution_name': doc.institution_name,
            'language_name': doc.language_name,
            'created_date': doc.created_date.isoformat() if doc.created_date else None
        })
    
    return jsonify({
        'documents': documents_list,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })
        
    #except Exception as e:
    #    return jsonify({'error': str(e)}), 500

@documents_bp.route('/api/documents', methods=['POST'])
def create_document():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('title'):
            return jsonify({'error': 'Título es requerido'}), 400
        
        if not data.get('author'):
            return jsonify({'error': 'Autor es requerido'}), 400
        
        # Create new document
        document = Documents(
            title=data.get('title'),
            author=data.get('author'),
            content=data.get('content'),
            rena=data.get('rena'),
            theme=data.get('theme'),
            doctype_id=data.get('doctype_id') if data.get('doctype_id') else None,
            country_id=data.get('country_id') if data.get('country_id') else None,
            institution_id=data.get('institution_id') if data.get('institution_id') else None,
            lenguage_id=data.get('lenguage_id') if data.get('lenguage_id') else None,
            user_id=1  # Get from session/auth
        )
        
        db.session.add(document)
        db.session.commit()
        
        return jsonify({'message': 'Documento creado exitosamente', 'id': document.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/api/documents/<int:document_id>', methods=['GET'])
def get_document(document_id):
    try:
        document = Documents.query.get_or_404(document_id)
        
        return jsonify({
            'id': document.id,
            'title': document.title,
            'author': document.author,
            'content': document.content,
            'rena': document.rena,
            'theme': document.theme,
            'doctype_id': document.doctype_id,
            'country_id': document.country_id,
            'institution_id': document.institution_id,
            'lenguage_id': document.lenguage_id,
            'created_date': document.created_date.isoformat() if document.created_date else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/api/documents/<int:document_id>', methods=['PUT'])
def update_document(document_id):
    try:
        document = Documents.query.get_or_404(document_id)
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            document.title = data['title']
        if 'author' in data:
            document.author = data['author']
        if 'content' in data:
            document.content = data['content']
        if 'rena' in data:
            document.rena = data['rena']
        if 'theme' in data:
            document.theme = data['theme']
        if 'doctype_id' in data:
            document.doctype_id = data['doctype_id'] if data['doctype_id'] else None
        if 'country_id' in data:
            document.country_id = data['country_id'] if data['country_id'] else None
        if 'institution_id' in data:
            document.institution_id = data['institution_id'] if data['institution_id'] else None
        if 'lenguage_id' in data:
            document.lenguage_id = data['lenguage_id'] if data['lenguage_id'] else None
        
        db.session.commit()
        
        return jsonify({'message': 'Documento actualizado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/api/documents/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    try:
        document = Documents.query.get_or_404(document_id)
        
        # Delete related records if needed
        # array_shape records
        db.session.query(Documents).filter(Documents.doc_id == document_id).delete()
        
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({'message': 'Documento eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/api/documents/<int:document_id>/analyze', methods=['POST'])
def analyze_document(document_id):
    try:
        document = Documents.query.get_or_404(document_id)
        
        # Here you would implement your AI analysis logic
        # For now, just return success
        
        return jsonify({'message': 'Análisis iniciado exitosamente'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/api/documents/stats', methods=['GET'])
def get_documents_stats():
    try:
        # Total documents
        total = Documents.query.count()
        
        # Documents this month
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly = Documents.query.filter(Documents.created_date >= current_month).count()
        
        # Analyzed documents (assuming you have a way to track this)
        analyzed = db.session.query(Documents)\
            .join(DocumentAnalysis, Documents.id == DocumentAnalysis.user_id)\
            .count()
        
        # Total content size (approximate)
        total_size_result = db.session.query(func.sum(func.length(Documents.content)))\
            .filter(Documents.content.isnot(None)).scalar()
        total_size = total_size_result or 0
        
        return jsonify({
            'total': total,
            'monthly': monthly,
            'analyzed': analyzed,
            'total_size': total_size
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/api/documents/export', methods=['GET'])
def export_documents():
    try:
        # Get all documents with related data
        documents = db.session.query(Documents)\
            .outerjoin(Doctype, Documents.doctype_id == Doctype.id)\
            .outerjoin(Country, Documents.country_id == Country.id)\
            .outerjoin(Institution, Documents.institution_id == Institution.id)\
            .outerjoin(Lenguage, Documents.lenguage_id == Lenguage.id)\
            .add_columns(
                Documents.id,
                Documents.title,
                Documents.author,
                Documents.rena,
                Documents.theme,
                Documents.created_date,
                Doctype.doctype.label('doctype_name'),
                Country.country.label('country_name'),
                Institution.institution.label('institution_name'),
                Lenguage.lenguage_name.label('language_name')
            ).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Título', 'Autor', 'RENA', 'Tema', 'Tipo Documento',
            'País', 'Institución', 'Idioma', 'Fecha Creación'
        ])
        
        # Data
        for doc in documents:
            writer.writerow([
                doc.id,
                doc.title or '',
                doc.author or '',
                doc.rena or '',
                doc.theme or '',
                doc.doctype_name or '',
                doc.country_name or '',
                doc.institution_name or '',
                doc.language_name or '',
                doc.created_date.strftime('%Y-%m-%d %H:%M:%S') if doc.created_date else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=documentos_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper endpoints for dropdowns
@documents_bp.route('/api/doctypes', methods=['GET'])
def get_doctypes():
    try:
        doctypes = Doctype.query.all()
        return jsonify([{
            'id': dt.id,
            'doctype': dt.doctype
        } for dt in doctypes])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/api/countries', methods=['GET'])
def get_countries():
    try:
        countries = Country.query.all()
        return jsonify([{
            'id': c.id,
            'country': c.country
        } for c in countries])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/api/institutions', methods=['GET'])
def get_institutions():
    try:
        institutions = Institution.query.all()
        return jsonify([{
            'id': i.id,
            'institution': i.institution
        } for i in institutions])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/api/languages', methods=['GET'])
def get_languages():
    try:
        languages = Lenguage.query.all()
        return jsonify([{
            'id': l.id,
            'lenguage_name': l.lenguage_name
        } for l in languages])
    except Exception as e:
        return jsonify({'error': str(e)}), 500