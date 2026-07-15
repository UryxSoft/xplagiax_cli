# -*- encoding: utf-8 -*-
"""
Copyright (c) 2024 - present URYX TECHNOLOGIES SRL
"""
from flask import Blueprint, render_template, redirect, url_for
import logging

x_apps = Blueprint('x_apps', __name__)

# Configura el logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('x_apps')

@x_apps.route('/')
def index():
    return render_template('/auth/sign_users.html')
    #return render_template('/page/index.html')

@x_apps.route('/login')
def login():
    return render_template('/auth/sign_users.html')
    #return render_template('/auth/login.html')

@x_apps.route('/register')
def register():
    # auth/signup.html no existe (500 TemplateNotFound). El registro vive en
    # sign_users.html; ?mode=register activa el panel de registro (JS inline).
    return redirect(url_for('x_apps.login', mode='register'))

@x_apps.route('/reset_password')
def reset_password():
    return render_template('/auth/reset_password.html')

@x_apps.route('/forgot_password')
def forgot_password():
    return render_template('/auth/forgot_password.html')

########################

@x_apps.route('/pricing')
def plans_test():
    return render_template('/billing/plans.html')

##### ERRORS PAGES ####

# Error 400 - Bad Request
@x_apps.errorhandler(400)
def bad_request(_):
    return render_template("/error_page/400_error.html"), 400

# Error 401 - Unauthorized
@x_apps.errorhandler(401)
def unauthorized(_):
    return render_template("/error_page/401_error.html"), 401

# Error 403 - Forbidden
@x_apps.errorhandler(403)
def forbidden(_):
    return render_template("/error_page/403_error.html"), 403


# Error 403 - Forbidden
@x_apps.errorhandler(403)
def forbidden(_):
    return render_template("/error_page/403_error.html"), 403

# Error 500 - Internal Server Error
@x_apps.errorhandler(500)
def internal_server_error(_):
    return render_template("/error_page/500_error.html"), 500

# Error 501 - Not Implemented
@x_apps.errorhandler(501)
def not_implemented(_):
    return render_template("/error_page/501_error.html"), 501

# Error 502 - Bad Gateway
@x_apps.errorhandler(502)
def bad_gateway(_):
    return render_template("/error_page/502_error.html"), 502

# Error 503 - Service Unavailable
@x_apps.errorhandler(503)
def service_unavailable(_):
    return render_template("/error_page/503_error.html"), 503

# Error 504 - Gateway Timeout
@x_apps.errorhandler(504)
def gateway_timeout(_):
    return render_template("/error_page/504_error.html"), 504