"""
Envío de correos del admin (activación / bienvenida) vía SMTP directo con la
config MAIL_* (env). Branding idéntico al email de share de appcli2
(paleta #064CDB, tarjeta blanca sobre #eef2f7). Nunca se envían contraseñas.
"""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

logger = logging.getLogger(__name__)

_B = {'primary': '#064CDB', 'ink': '#0f172a', 'muted': '#64748b', 'bg': '#f8fafc'}


def send_email(to_addr, subject, html):
    cfg = current_app.config
    msg = MIMEMultipart('alternative')
    sender_name, sender_addr = cfg['MAIL_DEFAULT_SENDER']
    msg['From'] = f'{sender_name} <{sender_addr}>'
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    try:
        if cfg.get('MAIL_USE_SSL'):
            with smtplib.SMTP_SSL(cfg['MAIL_SERVER'], cfg['MAIL_PORT'],
                                  context=ssl.create_default_context(), timeout=20) as s:
                s.login(cfg['MAIL_USERNAME'], cfg['MAIL_PASSWORD'])
                s.sendmail(sender_addr, [to_addr], msg.as_string())
        else:
            with smtplib.SMTP(cfg['MAIL_SERVER'], cfg['MAIL_PORT'], timeout=20) as s:
                if cfg.get('MAIL_USE_TLS'):
                    s.starttls(context=ssl.create_default_context())
                s.login(cfg['MAIL_USERNAME'], cfg['MAIL_PASSWORD'])
                s.sendmail(sender_addr, [to_addr], msg.as_string())
        return True
    except Exception:
        logger.exception('send_email failed to %s', to_addr)
        return False


def send_password_set_email(admin, subject='Set your XplagiaX Admin password'):
    """Emite el token single-use (core.tokens) y manda el link — nunca una
    contraseña. Cubre tanto alta de admin (hash placeholder) como forgot-password."""
    from flask import url_for
    from core import tokens as tk
    token = tk.make_password_reset_token(admin.id, admin.password_hash)
    url = url_for('auth_bp.reset_password_page', token=token, _external=True)
    hours = current_app.config.get('ADMIN_PWRESET_MAX_AGE_HOURS', 24)
    html = password_reset_email_html(admin.username, url, expires_hours=hours)
    return send_email(admin.email, subject, html)


def password_reset_email_html(name, reset_url, expires_hours=24):
    B = _B
    first = (name or '').strip() or 'there'
    return f"""
<div style="margin:0;padding:24px;background:#eef2f7;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e2e8f0;">
    <div style="background:{B['primary']};padding:22px 26px;">
      <div style="color:#ffffff;font-size:18px;font-weight:800;letter-spacing:.02em;">
        <span style="opacity:.85;">&times;</span>plagia<span style="opacity:.85;">&times;</span></div>
      <div style="color:rgba(255,255,255,.78);font-size:12px;margin-top:2px;">Admin Panel</div>
    </div>
    <div style="padding:26px;">
      <h2 style="margin:0 0 10px;font-size:18px;color:{B['ink']};">Hi, {first}</h2>
      <p style="margin:0 0 18px;font-size:13.5px;line-height:1.6;color:#334155;">
        Use the button below to set the password for your XplagiaX Admin account.</p>
      <div style="text-align:center;margin:22px 0;">
        <a href="{reset_url}"
           style="display:inline-block;background:{B['primary']};color:#ffffff;text-decoration:none;
                  font-size:14px;font-weight:700;padding:13px 30px;border-radius:10px;">
          Set my password</a>
      </div>
      <p style="margin:0;font-size:12px;line-height:1.6;color:{B['muted']};">
        This link expires in <b>{expires_hours} hours</b> and can be used only once.
        For your security, XplagiaX never sends passwords by email. If you didn't
        request this you can safely ignore this message — your account is unaffected.</p>
    </div>
    <div style="padding:14px 26px;background:{B['bg']};border-top:1px solid #e2e8f0;">
      <p style="margin:0;font-size:11px;color:{B['muted']};">
        Need help? Contact support · © XplagiaX — Confidential</p>
    </div>
  </div>
</div>"""


def activation_email_html(name, activation_url, plan, trial_days=None, expires_hours=72):
    B = _B
    first = (name or '').strip() or 'there'
    trial_line = (f'<p style="margin:0 0 6px;font-size:13.5px;color:#334155;">Your account starts with a '
                  f'<b>{int(trial_days)}-day trial</b> of the {plan} plan.</p>') if trial_days else ''
    return f"""
<div style="margin:0;padding:24px;background:#eef2f7;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e2e8f0;">
    <div style="background:{B['primary']};padding:22px 26px;">
      <div style="color:#ffffff;font-size:18px;font-weight:800;letter-spacing:.02em;">
        <span style="opacity:.85;">&times;</span>plagia<span style="opacity:.85;">&times;</span></div>
      <div style="color:rgba(255,255,255,.78);font-size:12px;margin-top:2px;">Academic Integrity Platform — AI TestPro · FinderX</div>
    </div>
    <div style="padding:26px;">
      <h2 style="margin:0 0 10px;font-size:18px;color:{B['ink']};">Welcome, {first}!</h2>
      <p style="margin:0 0 6px;font-size:13.5px;line-height:1.6;color:#334155;">
        An account has been created for you on <b>XplagiaX</b> — the platform for AI-content
        detection, plagiarism search and citation validation ({plan} plan).</p>
      {trial_line}
      <p style="margin:0 0 18px;font-size:13.5px;line-height:1.6;color:#334155;">
        To activate it, confirm your email and set your own password:</p>
      <div style="text-align:center;margin:22px 0;">
        <a href="{activation_url}"
           style="display:inline-block;background:{B['primary']};color:#ffffff;text-decoration:none;
                  font-size:14px;font-weight:700;padding:13px 30px;border-radius:10px;">
          Activate my account</a>
      </div>
      <p style="margin:0;font-size:12px;line-height:1.6;color:{B['muted']};">
        This link expires in <b>{expires_hours} hours</b> and can be used only once.
        For your security, XplagiaX never sends passwords by email — you will choose
        yours on the activation screen. If you didn't expect this invitation you can
        safely ignore this message.</p>
    </div>
    <div style="padding:14px 26px;background:{B['bg']};border-top:1px solid #e2e8f0;">
      <p style="margin:0;font-size:11px;color:{B['muted']};">
        Need help? Contact support · © XplagiaX — Confidential</p>
    </div>
  </div>
</div>"""
