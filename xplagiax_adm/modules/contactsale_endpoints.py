from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models.model import ContactSale, ContactInteraction, Users_admin
from utils.connections import db
from sqlalchemy import func, desc, or_, and_
import json
from werkzeug.utils import secure_filename

contact_sale_bp = Blueprint('contact_sale_bp', __name__)

@contact_sale_bp.route('/')
@login_required
def index():
    """Renderizar página principal del CRM de contactos"""
    return render_template('contact_sale_admin.html')

@contact_sale_bp.route('/api/contacts')
@login_required
def get_contacts():
    """Obtener lista de contactos con filtros y paginación"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        status_filter = request.args.get('status', '')
        priority_filter = request.args.get('priority', '')
        service_filter = request.args.get('service', '')
        assigned_filter = request.args.get('assigned', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        source_filter = request.args.get('source', '')
        
        # Query base
        query = ContactSale.query
        
        # Filtros de búsqueda
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                or_(
                    ContactSale.first_name.ilike(search_term),
                    ContactSale.last_name.ilike(search_term),
                    ContactSale.email.ilike(search_term),
                    ContactSale.company_name.ilike(search_term),
                    ContactSale.phone.ilike(search_term)
                )
            )
        
        # Filtros específicos
        if status_filter:
            query = query.filter(ContactSale.status == status_filter)
            
        if priority_filter:
            query = query.filter(ContactSale.priority == priority_filter)
            
        if service_filter:
            query = query.filter(ContactSale.service_interest == service_filter)
            
        if assigned_filter:
            if assigned_filter == 'unassigned':
                query = query.filter(ContactSale.assigned_to.is_(None))
            else:
                query = query.filter(ContactSale.assigned_to == int(assigned_filter))
                
        if source_filter:
            query = query.filter(ContactSale.source == source_filter)
            
        # Filtros de fecha
        if date_from:
            query = query.filter(ContactSale.created_at >= datetime.fromisoformat(date_from))
            
        if date_to:
            query = query.filter(ContactSale.created_at <= datetime.fromisoformat(date_to))
        
        # Ordenar por fecha de creación (más recientes primero)
        query = query.order_by(desc(ContactSale.created_at))
        
        # Paginación
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        contacts = []
        for contact in pagination.items:
            contact_data = contact.to_dict()
            contact_data['days_since_created'] = contact.days_since_created
            contact_data['days_since_last_contact'] = contact.days_since_last_contact
            contact_data['is_overdue_followup'] = contact.is_overdue_followup
            contacts.append(contact_data)
        
        return jsonify({
            'status': 'success',
            'contacts': contacts,
            'pagination': {
                'current_page': pagination.page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@contact_sale_bp.route('/api/contact/<contact_id>')
@login_required
def get_contact_details(contact_id):
    """Obtener detalles completos de un contacto"""
    try:
        contact = ContactSale.query.filter_by(contact_id=contact_id).first()
        
        if not contact:
            return jsonify({
                'status': 'error',
                'message': 'Contacto no encontrado'
            }), 404
        
        # Obtener interacciones del contacto
        interactions = ContactInteraction.query.filter_by(
            contact_id=contact_id
        ).order_by(desc(ContactInteraction.created_at)).all()
        
        contact_data = contact.to_dict()
        contact_data['days_since_created'] = contact.days_since_created
        contact_data['days_since_last_contact'] = contact.days_since_last_contact
        contact_data['is_overdue_followup'] = contact.is_overdue_followup
        contact_data['interactions'] = [interaction.to_dict() for interaction in interactions]
        
        return jsonify({
            'status': 'success',
            'contact': contact_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@contact_sale_bp.route('/api/contact/<contact_id>', methods=['PUT'])
@login_required
def update_contact(contact_id):
    """Actualizar información de un contacto"""
    try:
        contact = ContactSale.query.filter_by(contact_id=contact_id).first()
        
        if not contact:
            return jsonify({
                'status': 'error',
                'message': 'Contacto no encontrado'
            }), 404
        
        data = request.get_json()
        
        # Campos actualizables
        updatable_fields = [
            'status', 'priority', 'assigned_to', 'lead_score', 'estimated_value',
            'last_contact_date', 'next_followup_date', 'contact_attempts',
            'internal_notes', 'tags'
        ]
        
        # Registrar cambios de estado
        old_status = contact.status
        
        for field in updatable_fields:
            if field in data:
                if field == 'last_contact_date' and data[field]:
                    setattr(contact, field, datetime.fromisoformat(data[field]))
                elif field == 'next_followup_date' and data[field]:
                    setattr(contact, field, datetime.fromisoformat(data[field]))
                elif field == 'assigned_to' and data[field] == '':
                    setattr(contact, field, None)
                else:
                    setattr(contact, field, data[field])
        
        # Actualizar timestamps
        contact.updated_at = datetime.utcnow()
        
        # Si cambió el estado, registrar fechas especiales
        if 'status' in data and data['status'] != old_status:
            if data['status'] in ['contacted', 'qualified', 'proposal']:
                if not contact.contacted_at:
                    contact.contacted_at = datetime.utcnow()
            elif data['status'] in ['closed_won', 'closed_lost']:
                contact.closed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Registrar la actualización como interacción
        if 'status' in data and data['status'] != old_status:
            interaction = ContactInteraction(
                contact_id=contact_id,
                user_id=current_user.id,
                interaction_type='status_change',
                subject=f'Estado cambiado de {old_status} a {data["status"]}',
                description=f'El estado del contacto fue actualizado por {current_user.username}',
                outcome='updated'
            )
            db.session.add(interaction)
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Contacto actualizado correctamente',
            'contact': contact.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@contact_sale_bp.route('/api/contact/<contact_id>/interaction', methods=['POST'])
@login_required
def add_interaction(contact_id):
    """Agregar una nueva interacción a un contacto"""
    try:
        contact = ContactSale.query.filter_by(contact_id=contact_id).first()
        
        if not contact:
            return jsonify({
                'status': 'error',
                'message': 'Contacto no encontrado'
            }), 404
        
        data = request.get_json()
        
        interaction = ContactInteraction(
            contact_id=contact_id,
            user_id=current_user.id,
            interaction_type=data.get('interaction_type', 'note'),
            subject=data.get('subject', ''),
            description=data.get('description', ''),
            outcome=data.get('outcome', ''),
            next_action=data.get('next_action', ''),
            duration_minutes=data.get('duration_minutes'),
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None
        )
        
        db.session.add(interaction)
        
        # Actualizar última fecha de contacto si es relevante
        if data.get('interaction_type') in ['email', 'call', 'meeting']:
            contact.last_contact_date = datetime.utcnow()
            contact.contact_attempts += 1
        
        # Actualizar próximo seguimiento si se especifica
        if data.get('next_followup_date'):
            contact.next_followup_date = datetime.fromisoformat(data['next_followup_date'])
        
        contact.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Interacción agregada correctamente',
            'interaction': interaction.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@contact_sale_bp.route('/api/stats')
@login_required
def get_contact_stats():
    """Obtener estadísticas generales del CRM"""
    #try:
    # Estadísticas básicas
    total_contacts = ContactSale.query.count()
    
    # Contactos por estado
    status_stats = db.session.query(
        ContactSale.status,
        func.count(ContactSale.id).label('count')
    ).group_by(ContactSale.status).all()
    
    # Contactos por prioridad
    priority_stats = db.session.query(
        ContactSale.priority,
        func.count(ContactSale.id).label('count')
    ).group_by(ContactSale.priority).all()
    
    # Contactos por servicio de interés
    service_stats = db.session.query(
        ContactSale.service_interest,
        func.count(ContactSale.id).label('count')
    ).group_by(ContactSale.service_interest).all()
    
    # Contactos por fuente
    source_stats = db.session.query(
        ContactSale.source,
        func.count(ContactSale.id).label('count')
    ).group_by(ContactSale.source).all()
    
    # Contactos recientes (últimos 30 días)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_contacts = ContactSale.query.filter(
        ContactSale.created_at >= thirty_days_ago
    ).count()
    
    # Contactos por mes (últimos 12 meses)
    #monthly_stats = db.session.query(
    #    func.date_trunc('month', ContactSale.created_at).label('month'),
    #    func.count(ContactSale.id).label('count')
    #).filter(
    #    ContactSale.created_at >= datetime.now() - timedelta(days=365)
    #).group_by(func.date_trunc('month', ContactSale.created_at)).all()
    

    monthly_stats = (
        db.session.query(
            func.date_format(ContactSale.created_at, '%Y-%m').label('month'),
            func.count(ContactSale.id).label('count')
        )
        .filter(ContactSale.created_at >=  datetime.now() - timedelta(days=365))
        .group_by(func.date_format(ContactSale.created_at, '%Y-%m'))
    )

    
    # Valor estimado total
    total_estimated_value = db.session.query(
        func.sum(ContactSale.estimated_value)
    ).filter(ContactSale.estimated_value.isnot(None)).scalar() or 0
    
    # Valor de deals cerrados ganados
    won_value = db.session.query(
        func.sum(ContactSale.estimated_value)
    ).filter(
        ContactSale.status == 'closed_won',
        ContactSale.estimated_value.isnot(None)
    ).scalar() or 0
    
    # Tasa de conversión
    total_closed = ContactSale.query.filter(
        ContactSale.status.in_(['closed_won', 'closed_lost'])
    ).count()
    
    won_deals = ContactSale.query.filter(
        ContactSale.status == 'closed_won'
    ).count()
    
    conversion_rate = (won_deals / total_closed * 100) if total_closed > 0 else 0
    
    # Contactos que requieren seguimiento
    overdue_followups = ContactSale.query.filter(
        ContactSale.next_followup_date < datetime.utcnow(),
        ContactSale.status.notin_(['closed_won', 'closed_lost'])
    ).count()
    
    # Contactos sin asignar
    unassigned_contacts = ContactSale.query.filter(
        ContactSale.assigned_to.is_(None),
        ContactSale.status != 'closed_lost'
    ).count()
    
    # Top usuarios por contactos asignados
    user_stats = db.session.query(
        Users_admin.username,
        func.count(ContactSale.id).label('contact_count')
    ).join(ContactSale, Users_admin.id == ContactSale.assigned_to)\
        .group_by(Users_admin.username)\
        .order_by(desc('contact_count')).limit(5).all()
    
    return jsonify({
        'status': 'success',
        'stats': {
            'total_contacts': total_contacts,
            'recent_contacts': recent_contacts,
            'total_estimated_value': total_estimated_value,
            'won_value': won_value,
            'conversion_rate': round(conversion_rate, 1),
            'overdue_followups': overdue_followups,
            'unassigned_contacts': unassigned_contacts,
            'status_distribution': [
                {'status': s.status, 'count': s.count} for s in status_stats
            ],
            'priority_distribution': [
                {'priority': p.priority, 'count': p.count} for p in priority_stats
            ],
            'service_distribution': [
                {'service': s.service_interest, 'count': s.count} for s in service_stats
            ],
            'source_distribution': [
                {'source': s.source or 'Direct', 'count': s.count} for s in source_stats
            ],
            'monthly_contacts': [
                {'month': str(m.month), 'count': m.count} for m in monthly_stats
            ],
            'top_users': [
                {'username': u.username, 'contact_count': u.contact_count} for u in user_stats
            ]
        }
    })
    
    #except Exception as e:
    #    return jsonify({
    #        'status': 'error',
    #        'message': str(e)
    #    }), 500

@contact_sale_bp.route('/api/users')
@login_required
def get_users():
    """Obtener lista de usuarios para asignación"""
    try:
        users = Users_admin.query.filter_by(is_active=True).all()
        
        return jsonify({
            'status': 'success',
            'users': [
                {'id': user.id, 'username': user.username, 'email': user.email}
                for user in users
            ]
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@contact_sale_bp.route('/api/contact/<contact_id>', methods=['DELETE'])
@login_required
def delete_contact(contact_id):
    """Eliminar un contacto"""
    try:
        contact = ContactSale.query.filter_by(contact_id=contact_id).first()
        
        if not contact:
            return jsonify({
                'status': 'error',
                'message': 'Contacto no encontrado'
            }), 404
        
        # Eliminar interacciones relacionadas
        ContactInteraction.query.filter_by(contact_id=contact_id).delete()
        
        # Eliminar contacto
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Contacto eliminado correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Endpoint público para el formulario de contacto
@contact_sale_bp.route('/api/public/contact', methods=['POST'])
def create_public_contact():
    """Crear un nuevo contacto desde el formulario público"""
    try:
        data = request.get_json()
        
        # Validaciones básicas
        required_fields = ['first_name', 'last_name', 'email', 'service_interest', 'message']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'El campo {field} es requerido'
                }), 400
        
        # Verificar si ya existe un contacto con este email
        existing_contact = ContactSale.query.filter_by(email=data['email']).first()
        if existing_contact:
            return jsonify({
                'status': 'error',
                'message': 'Ya existe un contacto con este email'
            }), 400
        
        # Obtener información del request
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr
        
        # Crear nuevo contacto
        contact = ContactSale(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            phone=data.get('phone', ''),
            company_name=data.get('company_name', ''),
            job_title=data.get('job_title', ''),
            company_size=data.get('company_size', ''),
            industry=data.get('industry', ''),
            website=data.get('website', ''),
            service_interest=data['service_interest'],
            budget_range=data.get('budget_range', ''),
            timeline=data.get('timeline', ''),
            message=data['message'],
            source=data.get('source', 'Website'),
            utm_source=data.get('utm_source', ''),
            utm_medium=data.get('utm_medium', ''),
            utm_campaign=data.get('utm_campaign', ''),
            referrer_url=data.get('referrer_url', ''),
            user_agent=user_agent,
            ip_address=ip_address,
            status='new',
            priority='medium'
        )
        
        # Calcular score del lead
        contact.calculate_lead_score()
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Contacto creado correctamente. Te contactaremos pronto.',
            'contact_id': contact.contact_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@contact_sale_bp.route('/api/export')
@login_required
def export_contacts():
    """Exportar contactos en formato CSV"""
    try:
        # Aplicar filtros si se proporcionan
        status_filter = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        query = ContactSale.query
        
        if status_filter:
            query = query.filter(ContactSale.status == status_filter)
            
        if date_from:
            query = query.filter(ContactSale.created_at >= datetime.fromisoformat(date_from))
            
        if date_to:
            query = query.filter(ContactSale.created_at <= datetime.fromisoformat(date_to))
        
        contacts = query.order_by(desc(ContactSale.created_at)).all()
        
        # Preparar datos para exportación
        export_data = []
        for contact in contacts:
            export_data.append({
                'ID': contact.contact_id,
                'Nombre': contact.full_name,
                'Email': contact.email,
                'Teléfono': contact.phone or '',
                'Empresa': contact.company_name or '',
                'Cargo': contact.job_title or '',
                'Servicio': contact.service_interest,
                'Presupuesto': contact.budget_range or '',
                'Timeline': contact.timeline or '',
                'Estado': contact.status,
                'Prioridad': contact.priority,
                'Score': contact.lead_score,
                'Valor Estimado': contact.estimated_value or '',
                'Fuente': contact.source or '',
                'Asignado': contact.assigned_user.username if contact.assigned_user else '',
                'Fecha Creación': contact.created_at.strftime('%Y-%m-%d %H:%M:%S') if contact.created_at else '',
                'Último Contacto': contact.last_contact_date.strftime('%Y-%m-%d %H:%M:%S') if contact.last_contact_date else '',
                'Próximo Seguimiento': contact.next_followup_date.strftime('%Y-%m-%d %H:%M:%S') if contact.next_followup_date else ''
            })
        
        return jsonify({
            'status': 'success',
            'export_data': export_data,
            'total_records': len(export_data)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@contact_sale_bp.errorhandler(404)
def not_found(error):
    """Manejo de errores 404"""
    return jsonify({
        'status': 'error',
        'message': 'Recurso no encontrado'
    }), 404

@contact_sale_bp.errorhandler(500)
def internal_error(error):
    """Manejo de errores 500"""
    return jsonify({
        'status': 'error',
        'message': 'Error interno del servidor'
    }), 500