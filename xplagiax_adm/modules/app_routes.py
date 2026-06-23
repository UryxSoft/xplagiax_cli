# -*- encoding: utf-8 -*-
"""
Copyright (c) 2024 - present URYX TECHNOLOGIES SRL
"""
from flask import Blueprint, render_template,url_for,redirect,request
from flask_login import LoginManager,login_required, current_user, login_user, logout_user
from models.model import SSHSession, Users_admin
from datetime import timedelta
import logging

admx = Blueprint('admx',__name__)
# Configura el logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('admx')

@admx.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Verifica usuario y contraseña
        login_user(Users_admin, duration=timedelta(minutes=30))
        next_page = request.args.get('next')
        if next_page:
            return redirect(url_for('redirect_clean', target=next_page))  # redirect intermedio
        return redirect(url_for('admx.documents'))
    return render_template('auth.html')

@admx.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        # Verifica usuario y contraseña
        login_user(Users_admin, duration=timedelta(minutes=30))
        next_page = request.args.get('next')
        if next_page:
            return redirect(url_for('redirect_clean', target=next_page))  # redirect intermedio
        return redirect(url_for('admx.documents'))
    return render_template('auth.html')

@admx.route('/usersadmins')
@login_required
def usersadmins():
    return render_template('/menu_usuarios/admins_management.html')

@admx.route('/documents')
@login_required
def documents():
    return render_template('/menu_contenido/documents_management.html')

@admx.route('/doctype')
@login_required
def doctype():
    return render_template('/menu_contenido/doctype_management.html')

@admx.route('/institutions')
@login_required
def institutions():
    return render_template('/menu_contenido/institutions_management.html')

@admx.route('/institutionstype')
@login_required
def institutionstype():
    return render_template('/menu_contenido/institutionstype_management.html')

@admx.route('/countries')
@login_required
def countries():
    return render_template('/menu_contenido/countries_management.html')

@admx.route('/provinces')
@login_required
def provinces():
    return render_template('/menu_contenido/provinces_management.html')

@admx.route('/cities')
@login_required
def cities():
    return render_template('/menu_contenido/cities_management.html')

@admx.route('/languages')
@login_required
def languages():
    return render_template('/menu_contenido/languages_management.html')

@admx.route('/sessions')
@login_required
def sessions():
    return render_template('/menu_contenido/sessions_management.html')

@admx.route('/users')
@login_required
def users():
    return render_template('/menu_usuarios/users1_management.html')

@admx.route('/services')
@login_required
def services():
    return render_template('/menu_sistema/services_management.html')

@admx.route('/settings')
@login_required
def settings():
    return render_template('/menu_sistema/settings_management.html')

@admx.route('/dash')
@login_required
def dash():
    return render_template('/terminal/terminal_dash.html')

@admx.route('/ssh')
def ssh():
    return render_template('/terminal/terminal_ssh.html')

@admx.route('/terminal/<int:session_id>')
def terminal(session_id):
    session = SSHSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    return render_template('/terminal/terminal_enhanced.html', session=session)

@admx.route('/aianalysis')
@login_required
def aianalysis():
    return render_template('/menu_analisis/aianalisis_management.html')

@admx.route('/contactsales')
@login_required
def contactsales():
    return render_template('/menu_analisis/contactsales_management.html')

@admx.route('/reports')
@login_required
def reports():
    return render_template('/terminal/terminal_reports.html')

@admx.route('/feedback')
@login_required
def feedback():
    return render_template('/feedback_management.html')

@admx.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500
