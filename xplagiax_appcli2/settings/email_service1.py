# email_service.py - Servicio para manejar múltiples proveedores de email

from flask_mail import Mail, Message
from flask import current_app
import logging

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
                'MAIL_USERNAME': 'noreply@xplagiax.ca',
                'MAIL_PASSWORD': 'MYR1xkd2kqc_gat2hem',
                'MAIL_DEFAULT_SENDER': ('XPlagiax', 'noreply@xplagiax.ca')
            },
            'billing': {
                'MAIL_SERVER': 'smtp.ionos.com',
                'MAIL_PORT': 587,
                'MAIL_USE_SSL': False,
                'MAIL_USE_TLS': True,
                'MAIL_USERNAME': 'billing@xplagiax.com',
                'MAIL_PASSWORD': 'VNZ-twu!jgt5xwk1ybd',
                'MAIL_DEFAULT_SENDER': ('XPlagiax Billing', 'billing@xplagiax.com')
            },
            'gmail': {
                'MAIL_SERVER': 'smtp.gmail.com',
                'MAIL_PORT': 465,
                'MAIL_USE_SSL': True,
                'MAIL_USE_TLS': False,
                'MAIL_USERNAME': 'xplagiax@gmail.com',
                'MAIL_PASSWORD': 'akkv bxvl nmui sbws',
                'MAIL_DEFAULT_SENDER': ('XPlagiax Support', 'xplagiax@gmail.com')
            }
        }
        return configs.get(provider, configs['noreply'])
    
    @staticmethod
    def send_email(subject, recipients, html_content, provider='noreply', fallback_provider='gmail'):
        """
        Envía email usando el proveedor especificado
        Si falla, intenta con el proveedor de respaldo
        
        Args:
            subject (str): Asunto del email
            recipients (list): Lista de destinatarios
            html_content (str): Contenido HTML del email
            provider (str): Proveedor principal ('noreply', 'billing', 'gmail')
            fallback_provider (str): Proveedor de respaldo
        
        Returns:
            dict: {'success': bool, 'message': str, 'provider_used': str}
        """
        
        # Intentar con proveedor principal
        result = EmailService._try_send_email(subject, recipients, html_content, provider)
        if result['success']:
            return result
        
        # Si falla, intentar con proveedor de respaldo
        logger.warning(f"Primary email provider '{provider}' failed: {result['message']}")
        logger.info(f"Trying fallback provider: {fallback_provider}")
        
        fallback_result = EmailService._try_send_email(subject, recipients, html_content, fallback_provider)
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
    def _try_send_email(subject, recipients, html_content, provider):
        """
        Intenta enviar email con un proveedor específico
        """
        try:
            config = EmailService.get_email_config(provider)
            
            # Crear instancia temporal de Mail
            temp_mail = Mail()
            
            # Backup de configuración original
            original_config = {}
            for key, value in config.items():
                original_config[key] = current_app.config.get(key)
                current_app.config[key] = value
            
            # Inicializar Mail con nueva configuración
            temp_mail.init_app(current_app)
            
            # Crear mensaje
            msg = Message(
                subject=subject,
                recipients=recipients if isinstance(recipients, list) else [recipients],
                sender=config['MAIL_DEFAULT_SENDER']
            )
            msg.html = html_content
            
            # Enviar email
            temp_mail.send(msg)
            
            # Restaurar configuración original
            for key, value in original_config.items():
                if value is not None:
                    current_app.config[key] = value
                else:
                    current_app.config.pop(key, None)
            
            return {
                'success': True,
                'message': f'Email sent successfully using {provider}',
                'provider_used': provider
            }
            
        except Exception as e:
            # Restaurar configuración en caso de error
            for key, value in original_config.items():
                if value is not None:
                    current_app.config[key] = value
                else:
                    current_app.config.pop(key, None)
            
            error_msg = f"Failed to send email with {provider}: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'message': error_msg,
                'provider_used': None
            }

# Funciones de conveniencia para diferentes tipos de email
class EmailTemplates:
    
    @staticmethod
    def send_confirmation_email(user_email, confirm_url, user_name=None):
        """Envía email de confirmación de cuenta"""
        from flask import render_template
        
        html_content = render_template('emails/confirm.html', 
                                     confirm_url=confirm_url, 
                                     user_name=user_name or user_email)
        
        return EmailService.send_email(
            subject='Confirm your XPlagiax account',
            recipients=[user_email],
            html_content=html_content,
            provider='noreply',  # Usar noreply para confirmaciones
            fallback_provider='gmail'
        )
    
    @staticmethod
    def send_billing_email(user_email, invoice_data, email_type='invoice'):
        """Envía emails relacionados con facturación"""
        from flask import render_template
        
        subjects = {
            'invoice': 'Your XPlagiax Invoice',
            'payment_success': 'Payment Confirmation - XPlagiax',
            'payment_failed': 'Payment Failed - XPlagiax',
            'subscription_renewal': 'Subscription Renewal - XPlagiax',
            'subscription_cancelled': 'Subscription Cancelled - XPlagiax'
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
            subject=subjects.get(email_type, 'XPlagiax Billing Notification'),
            recipients=[user_email],
            html_content=html_content,
            provider='billing',  # Usar billing para temas de facturación
            fallback_provider='noreply'
        )
    
    @staticmethod
    def send_support_email(user_email, message, subject="Support Response"):
        """Envía emails de soporte"""
        
        return EmailService.send_email(
            subject=f"XPlagiax Support: {subject}",
            recipients=[user_email],
            html_content=message,
            provider='gmail',  # Usar Gmail para soporte (permite respuestas)
            fallback_provider='noreply'
        )
    
    @staticmethod
    def send_password_reset(user_email, reset_url, user_name=None):
        """Envía email de reset de contraseña"""
        from flask import render_template
        
        html_content = render_template('emails/password_reset.html', 
                                     reset_url=reset_url, 
                                     user_name=user_name or user_email)
        
        return EmailService.send_email(
            subject='Reset your XPlagiax password',
            recipients=[user_email],
            html_content=html_content,
            provider='noreply',
            fallback_provider='gmail'
        )