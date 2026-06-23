from flask import Blueprint, render_template, jsonify, request, make_response
from flask_login import login_required, current_user
from models.model import SessionLog, FileTransfer, SSHSession
from datetime import datetime
import csv
from io import StringIO

reports_bp = Blueprint('reports_bp', __name__)

@reports_bp.route('/')
@login_required
def index():
    return render_template('reports.html')

@reports_bp.route('/api/reports')
@login_required
def generate_report():
    report_type = request.args.get('type', 'activity')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    if report_type == 'activity':
        query = SessionLog.query.join(SSHSession).filter(SSHSession.user_id == current_user.id)
        
        if start:
            query = query.filter(SessionLog.timestamp >= start)
        if end:
            query = query.filter(SessionLog.timestamp <= end)
        
        logs = query.order_by(SessionLog.timestamp.desc()).all()
        
        report_data = [{
            'session_id': log.session_id,
            'command': log.command,
            'output': log.output[:100] + '...' if log.output and len(log.output) > 100 else log.output,
            'timestamp': log.timestamp.isoformat(),
            'execution_time': log.execution_time,
            'exit_code': log.exit_code
        } for log in logs]
        
        return jsonify(report_data)
    
    elif report_type == 'transfers':
        query = FileTransfer.query.join(SSHSession).filter(SSHSession.user_id == current_user.id)
        
        if start:
            query = query.filter(FileTransfer.started_at >= start)
        if end:
            query = query.filter(FileTransfer.started_at <= end)
        
        transfers = query.order_by(FileTransfer.started_at.desc()).all()
        
        report_data = [{
            'id': t.id,
            'filename': t.filename,
            'remote_path': t.remote_path,
            'transfer_type': t.transfer_type,
            'file_size': t.file_size,
            'status': t.status,
            'started_at': t.started_at.isoformat(),
            'completed_at': t.completed_at.isoformat() if t.completed_at else None
        } for t in transfers]
        
        return jsonify(report_data)
    
    elif report_type == 'security':
        # Usar SSHSession y SessionLog para crear eventos de seguridad
        query = SSHSession.query.filter(SSHSession.user_id == current_user.id)
        
        if start:
            query = query.filter(SSHSession.created_at >= start)
        if end:
            query = query.filter(SSHSession.created_at <= end)
        
        sessions = query.order_by(SSHSession.created_at.desc()).all()
        
        report_data = []
        
        for session in sessions:
            # Eventos de conexión
            if session.connected_at:
                if (not start or session.connected_at >= start) and (not end or session.connected_at <= end):
                    report_data.append({
                        'timestamp': session.connected_at.isoformat(),
                        'event_type': 'SSH_CONNECTION',
                        'username': current_user.username,
                        'ip_address': session.hostname,
                        'details': f"Conexión SSH establecida a {session.hostname}:{session.port} como {session.username}"
                    })
            
            # Eventos de actividad reciente
            if session.last_activity:
                if (not start or session.last_activity >= start) and (not end or session.last_activity <= end):
                    report_data.append({
                        'timestamp': session.last_activity.isoformat(),
                        'event_type': 'SSH_ACTIVITY',
                        'username': current_user.username,
                        'ip_address': session.hostname,
                        'details': f"Actividad detectada en sesión {session.name} ({session.hostname})"
                    })
            
            # Comandos que podrían ser considerados eventos de seguridad
            security_commands = SessionLog.query.filter(
                SessionLog.session_id == session.id,
                SessionLog.command.like('%sudo%') | 
                SessionLog.command.like('%su %') |
                SessionLog.command.like('%passwd%') |
                SessionLog.command.like('%chmod%') |
                SessionLog.command.like('%chown%')
            )
            
            if start:
                security_commands = security_commands.filter(SessionLog.timestamp >= start)
            if end:
                security_commands = security_commands.filter(SessionLog.timestamp <= end)
            
            for log in security_commands.all():
                report_data.append({
                    'timestamp': log.timestamp.isoformat(),
                    'event_type': 'SECURITY_COMMAND',
                    'username': current_user.username,
                    'ip_address': session.hostname,
                    'details': f"Comando de seguridad ejecutado: {log.command[:50]}..."
                })
        
        # Ordenar por timestamp descendente
        report_data.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify(report_data)
    
    return jsonify({'error': 'Invalid report type'}), 400

@reports_bp.route('/api/reports/export')
@login_required
def export_report():
    report_type = request.args.get('type', 'activity')
    format = request.args.get('format', 'csv')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    # Recrear la lógica de generate_report para obtener los datos
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    # Obtener los datos según el tipo de reporte
    if report_type == 'activity':
        query = SessionLog.query.join(SSHSession).filter(SSHSession.user_id == current_user.id)
        
        if start:
            query = query.filter(SessionLog.timestamp >= start)
        if end:
            query = query.filter(SessionLog.timestamp <= end)
        
        logs = query.order_by(SessionLog.timestamp.desc()).all()
        
        report_data = [{
            'session_id': log.session_id,
            'command': log.command,
            'output': log.output[:100] + '...' if log.output and len(log.output) > 100 else log.output,
            'timestamp': log.timestamp.isoformat(),
            'execution_time': log.execution_time,
            'exit_code': log.exit_code
        } for log in logs]
        
    elif report_type == 'transfers':
        query = FileTransfer.query.join(SSHSession).filter(SSHSession.user_id == current_user.id)
        
        if start:
            query = query.filter(FileTransfer.started_at >= start)
        if end:
            query = query.filter(FileTransfer.started_at <= end)
        
        transfers = query.order_by(FileTransfer.started_at.desc()).all()
        
        report_data = [{
            'id': t.id,
            'filename': t.filename,
            'remote_path': t.remote_path,
            'transfer_type': t.transfer_type,
            'file_size': t.file_size,
            'status': t.status,
            'started_at': t.started_at.isoformat(),
            'completed_at': t.completed_at.isoformat() if t.completed_at else None
        } for t in transfers]
        
    elif report_type == 'security':
        # Usar la misma lógica que en generate_report
        query = SSHSession.query.filter(SSHSession.user_id == current_user.id)
        
        if start:
            query = query.filter(SSHSession.created_at >= start)
        if end:
            query = query.filter(SSHSession.created_at <= end)
        
        sessions = query.order_by(SSHSession.created_at.desc()).all()
        
        report_data = []
        
        for session in sessions:
            if session.connected_at:
                if (not start or session.connected_at >= start) and (not end or session.connected_at <= end):
                    report_data.append({
                        'timestamp': session.connected_at.isoformat(),
                        'event_type': 'SSH_CONNECTION',
                        'username': current_user.username,
                        'ip_address': session.hostname,
                        'details': f"Conexión SSH establecida a {session.hostname}:{session.port} como {session.username}"
                    })
            
            if session.last_activity:
                if (not start or session.last_activity >= start) and (not end or session.last_activity <= end):
                    report_data.append({
                        'timestamp': session.last_activity.isoformat(),
                        'event_type': 'SSH_ACTIVITY',
                        'username': current_user.username,
                        'ip_address': session.hostname,
                        'details': f"Actividad detectada en sesión {session.name} ({session.hostname})"
                    })
        
        report_data.sort(key=lambda x: x['timestamp'], reverse=True)
    
    else:
        return jsonify({'error': 'Invalid report type'}), 400
    
    if format == 'csv':
        if report_type == 'activity':
            headers = ['Session ID', 'Command', 'Output', 'Timestamp', 'Execution Time', 'Exit Code']
        elif report_type == 'transfers':
            headers = ['ID', 'Filename', 'Remote Path', 'Type', 'Size', 'Status', 'Started At', 'Completed At']
        elif report_type == 'security':
            headers = ['Timestamp', 'Event Type', 'Username', 'IP Address', 'Details']
        
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(headers)
        
        for item in report_data:
            if report_type == 'activity':
                row = [
                    item['session_id'],
                    item['command'],
                    item['output'],
                    item['timestamp'],
                    item['execution_time'],
                    item['exit_code']
                ]
            elif report_type == 'transfers':
                row = [
                    item['id'],
                    item['filename'],
                    item['remote_path'],
                    item['transfer_type'],
                    item['file_size'],
                    item['status'],
                    item['started_at'],
                    item['completed_at'] or ''
                ]
            elif report_type == 'security':
                row = [
                    item['timestamp'],
                    item['event_type'],
                    item['username'],
                    item['ip_address'],
                    item['details']
                ]
            cw.writerow(row)
        
        output = si.getvalue()
        
        response = make_response(output)
        response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
    
    return jsonify({'error': 'Unsupported export format'}), 400