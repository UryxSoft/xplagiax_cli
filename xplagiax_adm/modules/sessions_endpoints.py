from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from models.model import Users,SubmissionSession,SessionParticipant,StudentSubmission
from utils.connections import db
import csv
from io import StringIO
from flask import make_response

sessions_bp = Blueprint('sessions_bp', __name__)

@sessions_bp.route('/api/sessions', methods=['GET'])
def list_sessions():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        sort_field = request.args.get('sort_field', 'created_at')
        sort_direction = request.args.get('sort_direction', 'desc')
        
        # Filters
        search = request.args.get('search', '').strip()
        status = request.args.get('status')
        professor_id = request.args.get('professor_id')
        analysis_status = request.args.get('analysis_status')
        date_from = request.args.get('date_from')
        
        # Base query with joins
        query = db.session.query(SubmissionSession)\
            .outerjoin(Users, SubmissionSession.professor_id == Users.id)\
            .add_columns(
                SubmissionSession.id,
                SubmissionSession.name,
                SubmissionSession.start_date,
                SubmissionSession.end_date,
                SubmissionSession.analysis_started,
                SubmissionSession.analysis_completed,
                SubmissionSession.created_at,
                func.concat(Users.name, ' ', Users.lastname).label('professor_name')
            )
        
        # Add participants count
        participants_subquery = db.session.query(
            SessionParticipant.session_id,
            func.count(SessionParticipant.id).label('participants_count')
        ).group_by(SessionParticipant.session_id).subquery()
        
        query = query.outerjoin(
            participants_subquery,
            SubmissionSession.id == participants_subquery.c.session_id
        ).add_columns(
            func.coalesce(participants_subquery.c.participants_count, 0).label('participants_count')
        )
        
        # Add submissions count
        submissions_subquery = db.session.query(
            StudentSubmission.session_id,
            func.count(StudentSubmission.id).label('submissions_count')
        ).group_by(StudentSubmission.session_id).subquery()
        
        query = query.outerjoin(
            submissions_subquery,
            SubmissionSession.id == submissions_subquery.c.session_id
        ).add_columns(
            func.coalesce(submissions_subquery.c.submissions_count, 0).label('submissions_count')
        )
        
        # Apply filters
        if search:
            query = query.filter(SubmissionSession.name.ilike(f'%{search}%'))
        
        if professor_id:
            query = query.filter(SubmissionSession.professor_id == professor_id)
        
        if status:
            now = datetime.now()
            if status == 'upcoming':
                query = query.filter(SubmissionSession.start_date > now)
            elif status == 'active':
                query = query.filter(
                    and_(
                        SubmissionSession.start_date <= now,
                        SubmissionSession.end_date >= now
                    )
                )
            elif status == 'completed':
                query = query.filter(SubmissionSession.end_date < now)
            elif status == 'expired':
                query = query.filter(SubmissionSession.end_date < now)
        
        if analysis_status:
            if analysis_status == 'pending':
                query = query.filter(SubmissionSession.analysis_started == False)
            elif analysis_status == 'in_progress':
                query = query.filter(
                    and_(
                        SubmissionSession.analysis_started == True,
                        SubmissionSession.analysis_completed == False
                    )
                )
            elif analysis_status == 'completed':
                query = query.filter(SubmissionSession.analysis_completed == True)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(SubmissionSession.start_date >= date_from_obj)
        
        # Apply sorting
        if sort_field == 'name':
            sort_column = SubmissionSession.name
        elif sort_field == 'professor_name':
            sort_column = func.concat(Users.name, ' ', Users.lastname)
        elif sort_field == 'start_date':
            sort_column = SubmissionSession.start_date
        elif sort_field == 'end_date':
            sort_column = SubmissionSession.end_date
        else:
            sort_column = getattr(SubmissionSession, sort_field, SubmissionSession.created_at)
        
        if sort_direction == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Pagination
        total = query.count()
        sessions = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format results
        sessions_list = []
        for session in sessions:
            sessions_list.append({
                'id': session.id,
                'name': session.name,
                'professor_id': session.submission_sessions.professor_id,
                'professor_name': session.professor_name,
                'start_date': session.start_date.isoformat() if session.start_date else None,
                'end_date': session.end_date.isoformat() if session.end_date else None,
                'analysis_started': session.analysis_started,
                'analysis_completed': session.analysis_completed,
                'participants_count': session.participants_count,
                'submissions_count': session.submissions_count,
                'created_at': session.created_at.isoformat() if session.created_at else None
            })
        
        return jsonify({
            'sessions': sessions_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/api/sessions', methods=['POST'])
def create_session():
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('name'):
            return jsonify({'error': 'Nombre de la sesión es requerido'}), 400
        
        if not data.get('professor_id'):
            return jsonify({'error': 'Profesor es requerido'}), 400
        
        if not data.get('start_date') or not data.get('end_date'):
            return jsonify({'error': 'Fechas de inicio y fin son requeridas'}), 400
        
        # Parse dates
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        
        if start_date >= end_date:
            return jsonify({'error': 'La fecha de fin debe ser posterior a la fecha de inicio'}), 400
        
        # Create new session
        session = SubmissionSession(
            name=data.get('name'),
            professor_id=data.get('professor_id'),
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(session)
        db.session.flush()  # Get the ID
        
        # Add participants if provided
        participants_text = data.get('participants', '').strip()
        if participants_text:
            emails = [email.strip() for email in participants_text.split('\n') if email.strip()]
            
            for email in emails:
                if '@' in email:  # Basic email validation
                    participant = SessionParticipant(
                        session_id=session.id,
                        email=email,
                        access_token=generate_access_token()  # You need to implement this
                    )
                    db.session.add(participant)
        
        db.session.commit()
        
        return jsonify({'message': 'Sesión creada exitosamente', 'id': session.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/api/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    try:
        session = SubmissionSession.query.get_or_404(session_id)
        
        return jsonify({
            'id': session.id,
            'name': session.name,
            'professor_id': session.professor_id,
            'start_date': session.start_date.isoformat() if session.start_date else None,
            'end_date': session.end_date.isoformat() if session.end_date else None,
            'analysis_started': session.analysis_started,
            'analysis_completed': session.analysis_completed,
            'created_at': session.created_at.isoformat() if session.created_at else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/api/sessions/<int:session_id>', methods=['PUT'])
def update_session(session_id):
    try:
        session = SubmissionSession.query.get_or_404(session_id)
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            session.name = data['name']
        
        if 'professor_id' in data:
            session.professor_id = data['professor_id']
        
        if 'start_date' in data:
            session.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        
        if 'end_date' in data:
            session.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        
        # Validate dates
        if session.start_date >= session.end_date:
            return jsonify({'error': 'La fecha de fin debe ser posterior a la fecha de inicio'}), 400
        
        db.session.commit()
        
        return jsonify({'message': 'Sesión actualizada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/api/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        session = SubmissionSession.query.get_or_404(session_id)
        
        # Check if session has submissions
        submissions_count = StudentSubmission.query.filter(
            StudentSubmission.session_id == session_id
        ).count()
        
        if submissions_count > 0:
            return jsonify({'error': f'No se puede eliminar la sesión porque tiene {submissions_count} entregas'}), 400
        
        # Delete related participants first
        SessionParticipant.query.filter(
            SessionParticipant.session_id == session_id
        ).delete()
        
        db.session.delete(session)
        db.session.commit()
        
        return jsonify({'message': 'Sesión eliminada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/api/sessions/<int:session_id>/details', methods=['GET'])
def get_session_details(session_id):
    try:
        session = SubmissionSession.query.get_or_404(session_id)
        
        # Get professor info
        professor = Users.query.get(session.professor_id)
        
        # Get participants
        participants = db.session.query(SessionParticipant)\
            .filter(SessionParticipant.session_id == session_id)\
            .all()
        
        # Get submissions
        submissions = db.session.query(StudentSubmission)\
            .filter(StudentSubmission.session_id == session_id)\
            .all()
        
        return jsonify({
            'session': {
                'id': session.id,
                'name': session.name,
                'start_date': session.start_date.isoformat() if session.start_date else None,
                'end_date': session.end_date.isoformat() if session.end_date else None,
                'analysis_started': session.analysis_started,
                'analysis_completed': session.analysis_completed,
                'created_at': session.created_at.isoformat() if session.created_at else None
            },
            'professor': {
                'id': professor.id,
                'name': f"{professor.name} {professor.lastname}",
                'email': professor.email
            } if professor else None,
            'participants': [{
                'id': p.id,
                'email': p.email,
                'invitation_sent': p.invitation_sent,
                'reminder_sent': p.reminder_sent,
                'created_at': p.created_at.isoformat() if p.created_at else None
            } for p in participants],
            'submissions': [{
                'id': s.id,
                'email': s.email,
                'file_name': s.file_name,
                'file_size': s.file_size,
                'uploaded_at': s.uploaded_at.isoformat() if s.uploaded_at else None,
                'professor_comment': s.professor_comment
            } for s in submissions]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/api/sessions/<int:session_id>/analyze', methods=['POST'])
def start_session_analysis(session_id):
    try:
        session = SubmissionSession.query.get_or_404(session_id)
        
        # Check if session has submissions
        submissions_count = StudentSubmission.query.filter(
            StudentSubmission.session_id == session_id
        ).count()
        
        if submissions_count == 0:
            return jsonify({'error': 'No hay entregas para analizar en esta sesión'}), 400
        
        # Mark analysis as started
        session.analysis_started = True
        db.session.commit()
        
        # Here you would implement your analysis logic
        # For now, just return success
        
        return jsonify({'message': 'Análisis iniciado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/api/sessions/stats', methods=['GET'])
def get_sessions_stats():
    try:
        # Total sessions
        total = SubmissionSession.query.count()
        
        # Active sessions
        now = datetime.now()
        active = SubmissionSession.query.filter(
            and_(
                SubmissionSession.start_date <= now,
                SubmissionSession.end_date >= now
            )
        ).count()
        
        # Total participants
        participants = SessionParticipant.query.count()
        
        # Total submissions
        submissions = SubmissionSession.query.count()
        
        return jsonify({
            'total': total,
            'active': active,
            'participants': participants,
            'submissions': submissions
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sessions_bp.route('/api/sessions/export', methods=['GET'])
def export_sessions():
    try:
        # Get all sessions with related data
        sessions = db.session.query(SubmissionSession)\
            .outerjoin(Users, SubmissionSession.professor_id == Users.id)\
            .add_columns(
                SubmissionSession.id,
                SubmissionSession.name,
                SubmissionSession.start_date,
                SubmissionSession.end_date,
                SubmissionSession.analysis_started,
                SubmissionSession.analysis_completed,
                SubmissionSession.created_at,
                func.concat(Users.name, ' ', Users.lastname).label('professor_name')
            ).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow([
            'ID', 'Nombre', 'Profesor', 'Fecha Inicio', 'Fecha Fin',
            'Análisis Iniciado', 'Análisis Completado', 'Fecha Creación'
        ])
        
        # Data
        for session in sessions:
            writer.writerow([
                session.id,
                session.name or '',
                session.professor_name or '',
                session.start_date.strftime('%Y-%m-%d %H:%M:%S') if session.start_date else '',
                session.end_date.strftime('%Y-%m-%d %H:%M:%S') if session.end_date else '',
                'Sí' if session.analysis_started else 'No',
                'Sí' if session.analysis_completed else 'No',
                session.created_at.strftime('%Y-%m-%d %H:%M:%S') if session.created_at else ''
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=sesiones_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper endpoints
@sessions_bp.route('/api/professors', methods=['GET'])
def get_professors():
    try:
        professors = Users.query.filter(Users.is_professor == True).all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'lastname': p.lastname,
            'email': p.email
        } for p in professors])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_access_token():
    """Generate a unique access token for participants"""
    import secrets
    return secrets.token_urlsafe(32)