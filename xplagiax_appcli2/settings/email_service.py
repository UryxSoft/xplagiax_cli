# email_service.py - Servicio mejorado para manejar múltiples proveedores de email

from flask_mail import Mail, Message
from flask import current_app, render_template
import logging
import time

logger = logging.getLogger(__name__)

class EmailService:
    
    @staticmethod
    def get_email_config(provider='noreply'):
        """
        Obtiene la configuración de email según el proveedor
        Proveedores disponibles: 'noreply', 'billing', 'gmail'
        """
        configs = {
            'noreply': {
                'MAIL_SERVER': 'smtp.ionos.com',
                'MAIL_PORT': 587,
                'MAIL_USE_SSL': False,
                'MAIL_USE_TLS': True,
                'MAIL_USERNAME': 'noreply@XplagiaX.ca',
                'MAIL_PASSWORD': 'MYR1xkd2kqc_gat2hem',
                'MAIL_DEFAULT_SENDER': ('XplagiaX', 'noreply@XplagiaX.ca')
            },
            'billing': {
                'MAIL_SERVER': 'smtp.ionos.com',
                'MAIL_PORT': 587,
                'MAIL_USE_SSL': False,
                'MAIL_USE_TLS': True,
                'MAIL_USERNAME': 'billing@XplagiaX.com',
                'MAIL_PASSWORD': 'VNZ-twu!jgt5xwk1ybd',
                'MAIL_DEFAULT_SENDER': ('XplagiaX Billing', 'billing@XplagiaX.com')
            },
            'gmail': {
                'MAIL_SERVER': 'smtp.gmail.com',
                'MAIL_PORT': 465,
                'MAIL_USE_SSL': True,
                'MAIL_USE_TLS': False,
                'MAIL_USERNAME': 'XplagiaX@gmail.com',
                'MAIL_PASSWORD': 'akkv bxvl nmui sbws',
                'MAIL_DEFAULT_SENDER': ('XplagiaX Support', 'XplagiaX@gmail.com')
            }
        }
        return configs.get(provider, configs['noreply'])
    
    @staticmethod
    def send_email(subject, recipients, html_content, provider='noreply', fallback_provider='gmail', plain_content=None):
        """
        Envía email usando el proveedor especificado
        Si falla, intenta con el proveedor de respaldo
        
        Args:
            subject (str): Asunto del email
            recipients (list): Lista de destinatarios
            html_content (str): Contenido HTML del email
            provider (str): Proveedor principal ('noreply', 'billing', 'gmail')
            fallback_provider (str): Proveedor de respaldo
            plain_content (str): Contenido en texto plano (opcional)
        
        Returns:
            dict: {'success': bool, 'message': str, 'provider_used': str}
        """
        
        # Intentar con proveedor principal
        result = EmailService._try_send_email(subject, recipients, html_content, provider, plain_content)
        if result['success']:
            return result
        
        # Si falla, intentar con proveedor de respaldo
        logger.warning(f"Primary email provider '{provider}' failed: {result['message']}")
        logger.info(f"Trying fallback provider: {fallback_provider}")
        
        fallback_result = EmailService._try_send_email(subject, recipients, html_content, fallback_provider, plain_content)
        if fallback_result['success']:
            fallback_result['message'] += f" (fallback from {provider})"
            return fallback_result
        
        # Si ambos fallan
        return {
            'success': False,
            'message': f"Both providers failed. Primary: {result['message']}, Fallback: {fallback_result['message']}",
            'provider_used': None
        }
    
    @staticmethod
    def _try_send_email(subject, recipients, html_content, provider, plain_content=None):
        """
        Intenta enviar email con un proveedor específico
        """
        original_config = {}
        temp_mail = None
        
        try:
            config = EmailService.get_email_config(provider)
            
            # Crear instancia temporal de Mail
            temp_mail = Mail()
            
            # Backup de configuración original
            for key, value in config.items():
                original_config[key] = current_app.config.get(key)
                current_app.config[key] = value
            
            # Inicializar Mail con nueva configuración
            temp_mail.init_app(current_app)
            
            # Preparar lista de recipients
            if isinstance(recipients, str):
                recipients = [recipients]
            
            # Crear mensaje
            msg = Message(
                subject=subject,
                recipients=recipients,
                sender=config['MAIL_DEFAULT_SENDER']
            )
            
            # Agregar contenido
            msg.html = html_content
            if plain_content:
                msg.body = plain_content
            
            # Enviar email
            temp_mail.send(msg)
            
            logger.info(f"Email sent successfully using {provider} to {', '.join(recipients)}")
            
            return {
                'success': True,
                'message': f'Email sent successfully using {provider}',
                'provider_used': provider
            }
            
        except Exception as e:
            error_msg = f"Failed to send email with {provider}: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'message': error_msg,
                'provider_used': None
            }
            
        finally:
            # Restaurar configuración original
            for key, value in original_config.items():
                if value is not None:
                    current_app.config[key] = value
                else:
                    current_app.config.pop(key, None)


# Funciones de conveniencia para diferentes tipos de email
class EmailTemplates:
    
    @staticmethod
    def send_confirmation_email(user_email, confirm_url, user_name=None):
        """Envía email de confirmación de cuenta"""
        try:
            html_content = render_template('emails/confirm_email.html', 
                                            confirm_url=confirm_url, 
                                            user_name=user_name or user_email)
            
            return EmailService.send_email(
                subject='Confirm your XplagiaX account',
                recipients=[user_email],
                html_content=html_content,
                provider='noreply',  # Usar noreply para confirmaciones
                fallback_provider='gmail'
            )
        except Exception as e:
            logger.error(f"Error in send_confirmation_email: {str(e)}")
            return {
                'success': False,
                'message': f'Template error: {str(e)}',
                'provider_used': None
            }
    
    @staticmethod
    def send_billing_email(user_email, invoice_data, email_type='invoice'):
        """Envía emails relacionados con facturación"""
        try:
            subjects = {
                'invoice': 'Your XplagiaX Invoice',
                'payment_success': 'Payment Confirmation - XplagiaX',
                'payment_failed': 'Payment Failed - XplagiaX',
                'subscription_renewal': 'Subscription Renewal - XplagiaX',
                'subscription_cancelled': 'Subscription Cancelled - XplagiaX'
            }
            
            template_map = {
                'invoice': 'emails/billing/invoice.html',
                'payment_success': 'emails/billing/payment_success.html',
                'payment_failed': 'emails/billing/payment_failed.html',
                'subscription_renewal': 'emails/billing/subscription_renewal.html',
                'subscription_cancelled': 'emails/billing/subscription_cancelled.html'
            }
            
            html_content = render_template(
                template_map.get(email_type, 'emails/billing/generic.html'),
                **invoice_data
            )
            
            return EmailService.send_email(
                subject=subjects.get(email_type, 'XplagiaX Billing Notification'),
                recipients=[user_email],
                html_content=html_content,
                provider='billing',  # Usar billing para temas de facturación
                fallback_provider='noreply'
            )
        except Exception as e:
            logger.error(f"Error in send_billing_email: {str(e)}")
            return {
                'success': False,
                'message': f'Billing email template error: {str(e)}',
                'provider_used': None
            }
    
    @staticmethod
    def send_support_email(user_email, message, subject="Support Response"):
        """Envía emails de soporte"""
        try:
           # Si el message ya es HTML, usarlo directamente; si no, crear template básico
            if '<html>' in message.lower() or '<body>' in message.lower():
                html_content = message
            else:
                html_message = message.replace('\n', '<br>')
                html_content = f"""<html>
                <body>
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #333;">XplagiaX Support</h2>
                        <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px;">
                            {html_message}
                        </div>
                        <p style="color: #666; font-size: 12px; margin-top: 20px;">
                            This is an automated message from XplagiaX Support.
                        </p>
                    </div>
                </body>
                </html>"""
            
            return EmailService.send_email(
                subject=f"XplagiaX Support: {subject}",
                recipients=[user_email],
                html_content=html_content,
                provider='gmail',  # Usar Gmail para soporte (permite respuestas)
                fallback_provider='noreply'
            )
        except Exception as e:
            logger.error(f"Error in send_support_email: {str(e)}")
            return {
                'success': False,
                'message': f'Support email error: {str(e)}',
                'provider_used': None
            }
    
    @staticmethod
    def send_password_reset(user_email, reset_url, user_name=None):
        """Envía email de reset de contraseña"""
        try:
            html_content = render_template('emails/reset_password.html', 
                                         reset_url=reset_url, 
                                         user_name=user_name or user_email)
            
            return EmailService.send_email(
                subject='Reset your XplagiaX password',
                recipients=[user_email],
                html_content=html_content,
                provider='noreply',
                fallback_provider='gmail'
            )
        except Exception as e:
            logger.error(f"Error in send_password_reset: {str(e)}")
            return {
                'success': False,
                'message': f'Password reset template error: {str(e)}',
                'provider_used': None
            }

    @staticmethod
    def send_welcome_email(user_email, user_name=None):
        """Envía email de bienvenida después de la confirmación"""
        try:
            html_content = render_template('emails/welcome.html', 
                                         user_name=user_name or user_email)
            
            return EmailService.send_email(
                subject='Welcome to XplagiaX!',
                recipients=[user_email],
                html_content=html_content,
                provider='noreply',
                fallback_provider='gmail'
            )
        except Exception as e:
            logger.error(f"Error in send_welcome_email: {str(e)}")
            return {
                'success': False,
                'message': f'Welcome email template error: {str(e)}',
                'provider_used': None
            }

    @staticmethod
    def send_notification_email(user_email, notification_type, data, user_name=None):
        """Envía emails de notificación general"""
        try:
            notification_subjects = {
                'quota_warning': 'Storage Quota Warning - XplagiaX',
                'quota_exceeded': 'Storage Quota Exceeded - XplagiaX',
                'plan_upgrade': 'Plan Upgraded - XplagiaX',
                'plan_downgrade': 'Plan Changed - XplagiaX',
                'account_suspended': 'Account Suspended - XplagiaX',
                'account_reactivated': 'Account Reactivated - XplagiaX'
            }
            
            template_map = {
                'quota_warning': 'emails/notifications/quota_warning.html',
                'quota_exceeded': 'emails/notifications/quota_exceeded.html',
                'plan_upgrade': 'emails/notifications/plan_upgrade.html',
                'plan_downgrade': 'emails/notifications/plan_downgrade.html',
                'account_suspended': 'emails/notifications/account_suspended.html',
                'account_reactivated': 'emails/notifications/account_reactivated.html'
            }
            
            html_content = render_template(
                template_map.get(notification_type, 'emails/notifications/generic.html'),
                user_name=user_name or user_email,
                **data
            )
            
            return EmailService.send_email(
                subject=notification_subjects.get(notification_type, 'XplagiaX Notification'),
                recipients=[user_email],
                html_content=html_content,
                provider='noreply',
                fallback_provider='gmail'
            )
        except Exception as e:
            logger.error(f"Error in send_notification_email: {str(e)}")
            return {
                'success': False,
                'message': f'Notification email template error: {str(e)}',
                'provider_used': None
            }