import stripe
import paypalrestsdk
import json
from flask import Blueprint, request, jsonify, current_app, url_for, redirect, render_template
from settings.connections import db
from modules.models.model import Users, StoragePlan
from flask_login import login_required, current_user
import requests
from datetime import datetime, timedelta

billing_bp = Blueprint('billing_bp', __name__)

def get_paypal_client():
    """Configura y retorna el cliente de PayPal"""
    return paypalrestsdk.configure({
        'mode': current_app.config.get('PAYPAL_MODE', 'live'),
        'client_id': current_app.config.get('PAYPAL_CLIENT_ID'),
        'client_secret': current_app.config.get('PAYPAL_CLIENT_SECRET')
    })

def verify_stripe_signature(payload, signature, secret):
    """Verify Stripe webhook signature"""
    try:
        stripe.Webhook.construct_event(payload, signature, secret)
        return True
    except stripe.error.SignatureVerificationError:
        return False

@billing_bp.route('/plans')
def get_plans():
    """Get available plans with pricing - Public endpoint"""
    try:
        plans = StoragePlan.query.filter_by(is_active=True).order_by(StoragePlan.price_monthly_usd).all()
        
        plans_data = []
        for plan in plans:
            plan_data = {
                'id': plan.id,
                'name': plan.name,
                'description': plan.description,
                'storage_mb': plan.base_storage_mb,
                'trial_days': plan.trial_days,
                'price_monthly': plan.price_monthly_usd,
                'price_annual': plan.price_annual_usd,
                'stripe_price_monthly': plan.stripe_price_monthly,
                'stripe_price_annual': plan.stripe_price_annual,
                'paypal_plan_monthly': plan.paypal_plan_monthly,
                'paypal_plan_annual': plan.paypal_plan_annual
            }
            plans_data.append(plan_data)
        
        return jsonify({'plans': plans_data}), 200
        
    except Exception as e:
        current_app.logger.exception("Error loading plans")
        return jsonify({'error': 'Failed to load plans'}), 500


@billing_bp.route('/pricing')
@login_required
def pricing_page():
    """Render pricing page for logged-in users"""
    return render_template('billing/plans.html', user=current_user)


@billing_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        data = request.get_json()
        
        current_app.logger.info(f"Received data: {data}")
        
        if not data:
            current_app.logger.error("No JSON data received")
            return jsonify({'error': 'No se recibieron datos'}), 400
        
        price_id = data.get('price_id')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        current_app.logger.info(f"price_id: {price_id}, billing_cycle: {billing_cycle}")
        
        if not price_id:
            current_app.logger.error("price_id is missing")
            return jsonify({'error': 'price_id requerido'}), 400
        
        # Validate price_id belongs to a real plan
        # Check Stripe prices first, then PayPal plan IDs
        plan = StoragePlan.query.filter(
            (StoragePlan.stripe_price_monthly == price_id) | 
            (StoragePlan.stripe_price_annual == price_id) |
            (StoragePlan.paypal_plan_monthly == price_id) |
            (StoragePlan.paypal_plan_annual == price_id)
        ).first()
        
        if not plan:
            current_app.logger.error(f"No plan found for price_id: {price_id}")
            return jsonify({'error': 'Plan no válido'}), 400
        
        current_app.logger.info(f"Creating checkout for plan: {plan.name}")
        
        # Get the correct Stripe price ID from the plan
        if billing_cycle == 'annual':
            stripe_price = plan.stripe_price_annual
        else:
            stripe_price = plan.stripe_price_monthly
        
        current_app.logger.info(f"stripe_price for {plan.name}: '{stripe_price}' (type: {type(stripe_price)})")
        
        # If no Stripe price configured, use PayPal instead
        # Check for None, empty string, or 'null' string
        stripe_price_invalid = (
            stripe_price is None or 
            stripe_price == 'null' or 
            (isinstance(stripe_price, str) and stripe_price.strip() == '')
        )
        if stripe_price_invalid:
            # Check if PayPal is available for this plan
            paypal_plan = plan.paypal_plan_monthly if billing_cycle == 'monthly' else plan.paypal_plan_annual
            current_app.logger.info(f"PayPal plan for {plan.name}: '{paypal_plan}'")
            if paypal_plan and paypal_plan != 'null':
                current_app.logger.info(f"No Stripe price for {plan.name}, redirecting to PayPal")
                return jsonify({
                    'error': 'Este plan solo está disponible via PayPal',
                    'use_paypal': True,
                    'plan_name': plan.name
                }), 400
            else:
                return jsonify({'error': 'Plan no tiene método de pago configurado'}), 400
        
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=str(current_user.id),
            customer_email=current_user.email,
            line_items=[{
                'price': stripe_price,
                'quantity': 1
            }],
            mode='subscription',
            success_url=url_for('billing_bp.checkout_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('billing_bp.checkout_cancel', _external=True),
            metadata={
                'user_id': str(current_user.id),
                'plan_id': str(plan.id),
                'billing_cycle': billing_cycle
            },
            subscription_data={
                'metadata': {
                    'user_id': str(current_user.id),
                    'plan_id': str(plan.id),
                    'billing_cycle': billing_cycle
                }
            },
            allow_promotion_codes=True,
            billing_address_collection='required'
        )
        
        current_app.logger.info(f"Checkout session created: {checkout_session.id}")
        
        return jsonify({
            'id': checkout_session.id,
            'url': checkout_session.url
        })
        
    except stripe.error.StripeError as e:
        current_app.logger.exception(f"Stripe error: {str(e)}")
        return jsonify({'error': f'Error de pago: {str(e)}'}), 500
    except Exception as e:
        current_app.logger.exception(f"Checkout session error: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500


@billing_bp.route('/checkout-success')
@login_required
def checkout_success():
    session_id = request.args.get('session_id')
    
    if session_id:
        try:
            # Retrieve the session to get payment details
            session = stripe.checkout.Session.retrieve(session_id)
            
            return render_template('billing/success.html', 
                                 session=session,
                                 user=current_user)
        except Exception as e:
            current_app.logger.exception("Error retrieving checkout session")
    
    return render_template('billing/success.html', user=current_user)

@billing_bp.route('/checkout-cancel')
def checkout_cancel():
    return render_template('billing/cancel.html')

@billing_bp.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    
    if not endpoint_secret:
        current_app.logger.error("STRIPE_WEBHOOK_SECRET not configured")
        return jsonify({'error': 'Webhook not configured'}), 500
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        current_app.logger.error("Invalid payload in webhook")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        current_app.logger.error("Invalid signature in webhook")
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event
    try:
        if event['type'] == 'checkout.session.completed':
            handle_checkout_completed(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            handle_payment_failed(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_canceled(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'invoice.upcoming':
            handle_upcoming_invoice(event['data']['object'])
        else:
            current_app.logger.info(f"Unhandled event type: {event['type']}")
    
    except Exception as e:
        current_app.logger.exception(f"Error handling webhook event {event['type']}")
        return jsonify({'error': 'Webhook processing failed'}), 500

    return jsonify({'status': 'success'})

def handle_checkout_completed(session):
    """Handle successful checkout completion"""
    client_ref = session.get('client_reference_id')
    if not client_ref:
        current_app.logger.error("No client_reference_id in checkout session")
        return
    
    try:
        user = Users.query.get(int(client_ref))
        if not user:
            current_app.logger.error(f"User not found: {client_ref}")
            return
        
        # Get plan from metadata
        metadata = session.get('metadata', {})
        plan_id = metadata.get('plan_id')
        billing_cycle = metadata.get('billing_cycle', 'monthly')
        
        if plan_id:
            plan = StoragePlan.query.get(int(plan_id))
            if plan:
                user.storage_plan_id = plan.id
                user.user_type = plan.name
        
        # Handle subscription vs one-time payment
        if session['mode'] == 'subscription':
            subscription_id = session.get('subscription')
            user.start_subscription('stripe', subscription_id, 'active', billing_cycle)
        else:
            user.subscription_provider = 'stripe'
            user.subscription_id = session['payment_intent']
            user.subscription_status = 'paid'
            user.subscription_type = 'annual'
            user.subscription_starts_at = datetime.utcnow()
            user.subscription_ends_at = datetime.utcnow() + timedelta(days=365)
            user.is_on_trial = False
        
        db.session.add(user)
        db.session.commit()
        
        current_app.logger.info(f"User {user.email} subscription activated")
        
    except Exception as e:
        current_app.logger.exception("Error in handle_checkout_completed")
        db.session.rollback()

def handle_payment_succeeded(invoice):
    """Handle successful payment (for subscriptions)"""
    subscription_id = invoice.get('subscription')
    customer_id = invoice.get('customer')
    
    if not subscription_id:
        current_app.logger.warning(f"No subscription_id in invoice {invoice.get('id')}")
        return
    
    user = Users.query.filter_by(subscription_id=subscription_id).first()
    if user:
        subscription = stripe.Subscription.retrieve(subscription_id)
        user.subscription_status = 'active'
        user.subscription_ends_at = datetime.fromtimestamp(subscription.current_period_end)
        user.subscription_renewal_notified = False
        
        db.session.add(user)
        db.session.commit()
        current_app.logger.info(f"Payment succeeded for user {user.email}, amount: {invoice.get('amount_paid', 0)/100}")
    else:
        current_app.logger.error(f"User not found for subscription_id: {subscription_id}")

def handle_payment_failed(invoice):
    """Handle failed payment"""
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return
    
    user = Users.query.filter_by(subscription_id=subscription_id).first()
    if user:
        user.subscription_status = 'past_due'
        db.session.add(user)
        db.session.commit()
        current_app.logger.warning(f"Payment failed for user {user.email}")

def handle_subscription_canceled(subscription):
    """Handle subscription cancellation"""
    subscription_id = subscription.get('id')
    user = Users.query.filter_by(subscription_id=subscription_id).first()
    if user:
        user.cancel_subscription()
        db.session.add(user)
        db.session.commit()
        current_app.logger.info(f"Subscription canceled for user {user.email}")

def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    subscription_id = subscription.get('id')
    user = Users.query.filter_by(subscription_id=subscription_id).first()
    if user:
        user.subscription_status = subscription.get('status', user.subscription_status)
        db.session.add(user)
        db.session.commit()

def handle_upcoming_invoice(invoice):
    """Handle upcoming invoice (for renewal notifications)"""
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return
    
    user = Users.query.filter_by(subscription_id=subscription_id).first()
    if user and not user.subscription_renewal_notified:
        try:
            from flask_mail import Message
            from settings.connections import mail
            
            msg = Message(
                'Renovación próxima de tu suscripción',
                recipients=[user.email]
            )
            msg.html = render_template('emails/renewal_notice.html', user=user)
            mail.send(msg)
            
            user.subscription_renewal_notified = True
            db.session.add(user)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.exception("Failed to send renewal notice")

# ============================================
# PAYPAL ENDPOINTS
# ============================================

@billing_bp.route('/paypal/create-order', methods=['POST'])
@login_required
def paypal_create_order():
    """Crear orden de PayPal para suscripción usando la API moderna de Subscriptions"""
    try:
        data = request.get_json()
        plan_name = data.get('plan')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        current_app.logger.info(f"PayPal order request: plan={plan_name}, cycle={billing_cycle}")
        
        if not plan_name:
            return jsonify({'error': 'Plan requerido'}), 400
        
        plan = StoragePlan.query.filter_by(name=plan_name, is_active=True).first()
        if not plan:
            return jsonify({'error': 'Plan no encontrado'}), 400
        
        # Obtener el plan_id de PayPal según el ciclo
        paypal_plan_id = plan.paypal_plan_annual if billing_cycle == 'annual' else plan.paypal_plan_monthly
        
        if not paypal_plan_id or paypal_plan_id == 'null':
            return jsonify({'error': 'Plan de PayPal no configurado'}), 400

        # Obtener Credenciales de Config
        client_id = current_app.config.get('PAYPAL_CLIENT_ID')
        client_secret = current_app.config.get('PAYPAL_CLIENT_SECRET')
        mode = current_app.config.get('PAYPAL_MODE', 'sandbox')
        
        base_url = "https://api-m.paypal.com" if mode == 'live' else "https://api-m.sandbox.paypal.com"
        
        # 1. Obtener Access Token
        auth_response = requests.post(
            f"{base_url}/v1/oauth2/token",
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"}
        )
        
        if not auth_response.ok:
            current_app.logger.error(f"PayPal Auth Error: {auth_response.text}")
            return jsonify({'error': 'Error de autenticación con PayPal'}), 500
            
        access_token = auth_response.json()['access_token']
        
        # 2. Crear Suscripción (API v1/billing/subscriptions)
        sub_data = {
            "plan_id": paypal_plan_id,
            "application_context": {
                "brand_name": "XplagiaX",
                "user_action": "SUBSCRIBE_NOW",
                "return_url": url_for('billing_bp.paypal_return', _external=True),
                "cancel_url": url_for('billing_bp.checkout_cancel', _external=True)
            }
        }
        
        sub_response = requests.post(
            f"{base_url}/v1/billing/subscriptions",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Prefer": "return=representation"
            },
            json=sub_data
        )
        
        if sub_response.ok:
            result = sub_response.json()
            approval_url = next(link['href'] for link in result['links'] if link['rel'] == 'approve')
            
            # Guardar el ID de suscripción temporalmente si es necesario
            current_app.logger.info(f"Subscription created: {result['id']} for user {current_user.email}")
            
            return jsonify({
                'approval_url': approval_url,
                'subscription_id': result['id']
            }), 200
        else:
            current_app.logger.error(f"PayPal Subscription Error: {sub_response.text}")
            error_detail = sub_response.json().get('details', [{}])[0].get('issue', 'Unknown error')
            return jsonify({'error': f'Error PayPal: {error_detail}'}), 500
            
    except Exception as e:
        current_app.logger.exception("Error en create-order PayPal")
        return jsonify({'error': str(e)}), 500


@billing_bp.route('/paypal/return')
@login_required
def paypal_return():
    """Manejar el retorno de PayPal después de aprobación de suscripción"""
    subscription_id = request.args.get('subscription_id')
    if not subscription_id:
        return redirect(url_for('billing_bp.checkout_cancel'))
        
    return render_template('billing/paypal_confirm.html', subscription_id=subscription_id)


@billing_bp.route('/paypal/confirm-subscription', methods=['POST'])
@login_required
def paypal_confirm_subscription():
    """Confirmar y activar la suscripción después del retorno"""
    try:
        data = request.get_json()
        subscription_id = data.get('subscription_id')
        
        if not subscription_id:
            return jsonify({'error': 'Subscription ID requerido'}), 400
            
        # 1. Obtener Access Token
        client_id = current_app.config.get('PAYPAL_CLIENT_ID')
        client_secret = current_app.config.get('PAYPAL_CLIENT_SECRET')
        mode = current_app.config.get('PAYPAL_MODE', 'sandbox')
        base_url = "https://api-m.paypal.com" if mode == 'live' else "https://api-m.sandbox.paypal.com"
        
        auth_response = requests.post(
            f"{base_url}/v1/oauth2/token",
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"}
        )
        access_token = auth_response.json()['access_token']
        
        # 2. Verificar estado de suscripción
        sub_response = requests.get(
            f"{base_url}/v1/billing/subscriptions/{subscription_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if sub_response.ok:
            sub_data = sub_response.json()
            plan_id = sub_data.get('plan_id')
            
            # Buscar el plan por el paypal_plan_id
            plan = StoragePlan.query.filter(
                (StoragePlan.paypal_plan_monthly == plan_id) | 
                (StoragePlan.paypal_plan_annual == plan_id)
            ).first()
            
            if not plan:
                return jsonify({'error': 'Plan no reconocido'}), 400
                
            # Activar suscripción en el sistema
            current_user.storage_plan_id = plan.id
            current_user.user_type = plan.name
            
            billing_cycle = 'annual' if plan.paypal_plan_annual == plan_id else 'monthly'
            
            current_user.start_subscription(
                provider='paypal',
                subscription_id=subscription_id,
                status='active',
                subscription_type=billing_cycle
            )
            
            db.session.add(current_user)
            db.session.commit()
            
            return jsonify({
                'message': 'Suscripción activada con éxito',
                'redirect': url_for('billing_bp.checkout_success', _external=True)
            })
        else:
            return jsonify({'error': 'No se pudo verificar la suscripción'}), 400
            
    except Exception as e:
        current_app.logger.exception("Error confirmando suscripción")
        return jsonify({'error': str(e)}), 500

@billing_bp.route('/paypal/execute-agreement', methods=['POST'])
@login_required
def paypal_execute_agreement():
    """Ejecutar acuerdo de suscripción después de aprobación del usuario"""
    try:
        data = request.get_json()
        token = data.get('token')
        plan_name = data.get('plan_name')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        if not token:
            return jsonify({'error': 'Token requerido'}), 400
        
        get_paypal_client()
        
        # Ejecutar el acuerdo
        billing_agreement = paypalrestsdk.BillingAgreement.execute(token)
        
        if billing_agreement:
            # Buscar el plan
            plan = StoragePlan.query.filter_by(name=plan_name, is_active=True).first()
            if not plan:
                return jsonify({'error': 'Plan no encontrado'}), 400
            
            # Actualizar usuario con la suscripción
            current_user.storage_plan_id = plan.id
            current_user.user_type = plan.name
            current_user.start_subscription(
                provider='paypal',
                subscription_id=billing_agreement.id,
                status='active',
                subscription_type=billing_cycle
            )
            
            db.session.add(current_user)
            db.session.commit()
            
            current_app.logger.info(f"PayPal subscription activated for {current_user.email}")
            
            return jsonify({
                'message': 'Suscripción activada exitosamente',
                'redirect': url_for('billing_bp.checkout_success', _external=True)
            }), 200
        else:
            current_app.logger.error(f"Error executing PayPal agreement: {billing_agreement.error if hasattr(billing_agreement, 'error') else 'Unknown'}")
            return jsonify({'error': 'Error ejecutando acuerdo PayPal'}), 500
            
    except Exception as e:
        current_app.logger.exception("Error ejecutando acuerdo PayPal")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@billing_bp.route('/paypal/webhook', methods=['POST'])
def paypal_webhook():
    """Manejar webhooks de PayPal"""
    try:
        get_paypal_client()
        
        # Obtener headers y payload
        transmission_id = request.headers.get('Paypal-Transmission-Id')
        timestamp = request.headers.get('Paypal-Transmission-Time')
        webhook_id = current_app.config.get('PAYPAL_WEBHOOK_ID')
        event_body = request.get_data().decode('utf-8')
        cert_url = request.headers.get('Paypal-Cert-Url')
        auth_algo = request.headers.get('Paypal-Auth-Algo')
        transmission_sig = request.headers.get('Paypal-Transmission-Sig')
        
        # Verificar webhook signature (comentar en desarrollo si no tienes webhook_id)
        if webhook_id:
            response = paypalrestsdk.WebhookEvent.verify(
                transmission_id,
                timestamp,
                webhook_id,
                event_body,
                cert_url,
                auth_algo,
                transmission_sig
            )
            if not response:
                current_app.logger.error("Firma de webhook PayPal inválida")
                return jsonify({'error': 'Invalid signature'}), 400
        
        event_data = json.loads(event_body)
        event_type = event_data.get('event_type')
        
        current_app.logger.info(f"PayPal webhook received: {event_type}")
        
        # Manejar diferentes tipos de eventos
        if event_type == 'BILLING.SUBSCRIPTION.ACTIVATED':
            handle_paypal_subscription_activated(event_data)
        elif event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            handle_paypal_subscription_cancelled(event_data)
        elif event_type == 'BILLING.SUBSCRIPTION.SUSPENDED':
            handle_paypal_subscription_suspended(event_data)
        elif event_type == 'PAYMENT.SALE.COMPLETED':
            handle_paypal_payment_completed(event_data)
        elif event_type == 'PAYMENT.SALE.REFUNDED':
            handle_paypal_payment_refunded(event_data)
        elif event_type == 'BILLING.SUBSCRIPTION.EXPIRED':
            handle_paypal_subscription_expired(event_data)
        elif event_type == 'BILLING.SUBSCRIPTION.PAYMENT.FAILED':
            handle_paypal_payment_failed(event_data)
        else:
            current_app.logger.info(f"Evento PayPal no manejado: {event_type}")
        
        return jsonify({'status': 'success'}), 200
            
    except Exception as e:
        current_app.logger.exception("Error en webhook PayPal")
        return jsonify({'error': str(e)}), 500

# Funciones helper para webhooks de PayPal
def handle_paypal_subscription_activated(event):
    """Activar suscripción cuando PayPal confirma"""
    resource = event.get('resource', {})
    agreement_id = resource.get('id')
    
    user = Users.query.filter_by(subscription_id=agreement_id, subscription_provider='paypal').first()
    if user:
        user.subscription_status = 'active'
        db.session.add(user)
        db.session.commit()
        current_app.logger.info(f"Suscripción PayPal activada para {user.email}")

def handle_paypal_subscription_cancelled(event):
    """Cancelar suscripción"""
    resource = event.get('resource', {})
    agreement_id = resource.get('id')
    
    user = Users.query.filter_by(subscription_id=agreement_id, subscription_provider='paypal').first()
    if user:
        user.cancel_subscription()
        db.session.add(user)
        db.session.commit()
        current_app.logger.info(f"Suscripción PayPal cancelada para {user.email}")

def handle_paypal_subscription_suspended(event):
    """Suspender suscripción por falta de pago"""
    resource = event.get('resource', {})
    agreement_id = resource.get('id')
    
    user = Users.query.filter_by(subscription_id=agreement_id, subscription_provider='paypal').first()
    if user:
        user.subscription_status = 'suspended'
        db.session.add(user)
        db.session.commit()
        current_app.logger.warning(f"Suscripción PayPal suspendida para {user.email}")

def handle_paypal_payment_completed(event):
    """Pago completado exitosamente"""
    resource = event.get('resource', {})
    agreement_id = resource.get('billing_agreement_id')
    
    if agreement_id:
        user = Users.query.filter_by(subscription_id=agreement_id, subscription_provider='paypal').first()
        if user:
            user.subscription_status = 'active'
            user.subscription_renewal_notified = False
            # Actualizar fecha de fin
            if user.subscription_type == 'annual':
                user.subscription_ends_at = datetime.utcnow() + timedelta(days=365)
            else:
                user.subscription_ends_at = datetime.utcnow() + timedelta(days=30)
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"Pago PayPal completado para {user.email}")

def handle_paypal_payment_refunded(event):
    """Pago reembolsado"""
    resource = event.get('resource', {})
    sale_id = resource.get('sale_id')
    current_app.logger.warning(f"Pago PayPal reembolsado: {sale_id}")

# ============================================
# CANCEL SUBSCRIPTION (STRIPE Y PAYPAL)
# ============================================

def handle_paypal_subscription_expired(event):
    resource = event.get('resource', {})
    sub_id = resource.get('id')
    user = Users.query.filter_by(subscription_id=sub_id, subscription_provider='paypal').first()
    if user:
        starter = StoragePlan.query.filter_by(name='Starter', is_active=True).first()
        user.subscription_status = 'expired'
        user.subscription_ends_at = datetime.utcnow()
        if starter:
            user.storage_plan_id = starter.id
        db.session.commit()
        current_app.logger.info('PayPal subscription expired user=%s', user.id)


def handle_paypal_payment_failed(event):
    resource = event.get('resource', {})
    sub_id = resource.get('id')
    user = Users.query.filter_by(subscription_id=sub_id, subscription_provider='paypal').first()
    if user:
        user.subscription_status = 'payment_failed'
        db.session.commit()
        current_app.logger.warning('PayPal payment failed user=%s sub=%s', user.id, sub_id)


@billing_bp.route('/paypal/get-plan', methods=['GET'])
@login_required
def paypal_get_plan():
    """Devuelve el paypal_plan_id para que el frontend lo use en createSubscription."""
    plan_name     = request.args.get('plan')
    billing_cycle = request.args.get('billing_cycle', 'monthly')
    if not plan_name:
        return jsonify({'error': 'Plan requerido'}), 400
    plan = StoragePlan.query.filter_by(name=plan_name, is_active=True).first()
    if not plan:
        return jsonify({'error': 'Plan no encontrado'}), 404
    plan_id = plan.paypal_plan_annual if billing_cycle == 'annual' else plan.paypal_plan_monthly
    if not plan_id:
        return jsonify({'error': 'PayPal no configurado para este plan/ciclo'}), 400
    return jsonify({
        'paypal_plan_id': plan_id,
        'plan_name':      plan.name,
        'billing_cycle':  billing_cycle,
        'amount':         plan.price_annual_usd if billing_cycle == 'annual' else plan.price_monthly_usd,
    })


@billing_bp.route('/paypal/subscription-confirm', methods=['POST'])
@login_required
def paypal_subscription_confirm():
    """Frontend llama esto después de que PayPal JS SDK aprueba la suscripción.
    Verifica con PayPal y activa el plan en BD.
    """
    data            = request.get_json() or {}
    subscription_id = data.get('subscription_id')
    plan_name       = data.get('plan')
    billing_cycle   = data.get('billing_cycle', 'monthly')

    if not subscription_id or not plan_name:
        return jsonify({'error': 'subscription_id y plan son obligatorios'}), 400

    plan = StoragePlan.query.filter_by(name=plan_name, is_active=True).first()
    if not plan:
        return jsonify({'error': 'Plan no encontrado'}), 404

    client_id     = current_app.config.get('PAYPAL_CLIENT_ID')
    client_secret = current_app.config.get('PAYPAL_CLIENT_SECRET')
    mode          = current_app.config.get('PAYPAL_MODE', 'live')
    base_url      = 'https://api-m.paypal.com' if mode == 'live' else 'https://api-m.sandbox.paypal.com'

    try:
        auth_resp = requests.post(
            f'{base_url}/v1/oauth2/token',
            auth=(client_id, client_secret),
            data={'grant_type': 'client_credentials'},
            timeout=10,
        )
        auth_resp.raise_for_status()
        token = auth_resp.json()['access_token']

        sub_resp = requests.get(
            f'{base_url}/v1/billing/subscriptions/{subscription_id}',
            headers={'Authorization': f'Bearer {token}'},
            timeout=10,
        )
        sub_resp.raise_for_status()
        sub = sub_resp.json()

        if sub.get('status') not in ('ACTIVE', 'APPROVED'):
            return jsonify({'error': f"Estado inesperado: {sub.get('status')}"}), 400

        expected_plan_id = plan.paypal_plan_annual if billing_cycle == 'annual' else plan.paypal_plan_monthly
        if sub.get('plan_id') != expected_plan_id:
            current_app.logger.warning(
                'PayPal plan_id mismatch: expected %s got %s user=%s',
                expected_plan_id, sub.get('plan_id'), current_user.id
            )
            return jsonify({'error': 'Plan ID no coincide'}), 400

        current_user.subscription_provider  = 'paypal'
        current_user.subscription_id        = subscription_id
        current_user.subscription_status    = 'active'
        current_user.subscription_type      = billing_cycle
        current_user.subscription_starts_at = datetime.utcnow()
        current_user.subscription_ends_at   = None
        current_user.storage_plan_id        = plan.id
        current_user.is_on_trial            = False
        db.session.commit()

        current_app.logger.info(
            'PayPal subscription activated: user=%s sub=%s plan=%s cycle=%s',
            current_user.id, subscription_id, plan_name, billing_cycle
        )
        return jsonify({'status': 'active', 'plan': plan_name, 'billing_cycle': billing_cycle})

    except Exception:
        current_app.logger.exception('PayPal subscription-confirm error user=%s', current_user.id)
        return jsonify({'error': 'Error verificando suscripción con PayPal'}), 500


def cancel_subscription_immediately(user):
    """Cancela la suscripción de `user` DE INMEDIATO (no al final del periodo).
    Usado por Delete Account — al borrar la cuenta no debe seguir cobrándose
    una suscripción de una cuenta que ya no existe. A diferencia de la ruta
    /cancel-subscription (cancel_at_period_end=True, graceful), esta llama
    stripe.Subscription.delete(...) directamente. Best-effort: un fallo aquí
    se registra pero NUNCA debe bloquear el borrado de la cuenta — un hipo del
    proveedor de pago no puede impedir que alguien ejerza su derecho a borrar
    sus datos. Devuelve (ok: bool, message: str).
    """
    if not user.subscription_id:
        return True, 'No active subscription.'

    try:
        if user.subscription_provider == 'stripe':
            stripe.Subscription.delete(user.subscription_id)
        elif user.subscription_provider == 'paypal':
            client_id = current_app.config.get('PAYPAL_CLIENT_ID')
            client_secret = current_app.config.get('PAYPAL_CLIENT_SECRET')
            mode = current_app.config.get('PAYPAL_MODE', 'sandbox')
            base_url = "https://api-m.paypal.com" if mode == 'live' else "https://api-m.sandbox.paypal.com"
            auth_response = requests.post(
                f"{base_url}/v1/oauth2/token",
                auth=(client_id, client_secret),
                data={"grant_type": "client_credentials"},
                timeout=10,
            )
            if not auth_response.ok:
                return False, 'PayPal authentication failed.'
            access_token = auth_response.json()['access_token']
            cancel_response = requests.post(
                f"{base_url}/v1/billing/subscriptions/{user.subscription_id}/cancel",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={"reason": "Account deleted"},
                timeout=10,
            )
            if cancel_response.status_code != 204:
                return False, f'PayPal cancellation returned {cancel_response.status_code}.'
        else:
            return True, 'Unknown subscription provider — nothing to cancel.'

        user.subscription_status = 'canceled'
        db.session.add(user)
        db.session.commit()
        return True, 'Subscription canceled immediately.'

    except Exception as exc:
        current_app.logger.exception("cancel_subscription_immediately failed for user=%s", user.id)
        return False, str(exc)


@billing_bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel current subscription"""
    if not current_user.subscription_id:
        return jsonify({'error': 'No tienes suscripción activa'}), 400
    
    if current_user.subscription_provider == 'stripe':
        try:
            stripe.Subscription.modify(
                current_user.subscription_id,
                cancel_at_period_end=True
            )
            
            current_user.subscription_status = 'canceled'
            db.session.add(current_user)
            db.session.commit()
            
            return jsonify({
                'message': 'Suscripción cancelada. Mantendrás el acceso hasta el final del período actual.'
            }), 200
            
        except stripe.error.StripeError as e:
            current_app.logger.exception("Stripe cancellation error")
            return jsonify({'error': f'Error cancelando suscripción: {str(e)}'}), 500
    
    elif current_user.subscription_provider == 'paypal':
        try:
            # 1. Obtener Access Token
            client_id = current_app.config.get('PAYPAL_CLIENT_ID')
            client_secret = current_app.config.get('PAYPAL_CLIENT_SECRET')
            mode = current_app.config.get('PAYPAL_MODE', 'sandbox')
            base_url = "https://api-m.paypal.com" if mode == 'live' else "https://api-m.sandbox.paypal.com"
            
            auth_response = requests.post(
                f"{base_url}/v1/oauth2/token",
                auth=(client_id, client_secret),
                data={"grant_type": "client_credentials"}
            )
            
            if not auth_response.ok:
                return jsonify({'error': 'Error de autenticación con PayPal'}), 500
                
            access_token = auth_response.json()['access_token']
            
            # 2. Cancelar Suscripción (API v1/billing/subscriptions/ID/cancel)
            cancel_response = requests.post(
                f"{base_url}/v1/billing/subscriptions/{current_user.subscription_id}/cancel",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={"reason": "Cancelado por el usuario"}
            )
            
            if cancel_response.status_code == 204: # Success with no content
                current_user.subscription_status = 'canceled'
                db.session.add(current_user)
                db.session.commit()
                
                return jsonify({
                    'message': 'Suscripción PayPal cancelada exitosamente'
                }), 200
            else:
                current_app.logger.error(f"Error cancelando PayPal: {cancel_response.text}")
                return jsonify({'error': 'Error cancelando suscripción PayPal'}), 500
                
        except Exception as e:
            current_app.logger.exception("PayPal cancellation error")
            return jsonify({'error': str(e)}), 500
    
    else:
        return jsonify({'error': 'Proveedor de suscripción no válido'}), 400

@billing_bp.route('/subscription-status')
@login_required
def subscription_status():
    """Get current subscription status"""
    return jsonify({
        'has_subscription': current_user.has_active_subscription(),
        'subscription_provider': current_user.subscription_provider,
        'subscription_status': current_user.subscription_status,
        'subscription_type': current_user.subscription_type,
        'subscription_starts_at': current_user.subscription_starts_at.isoformat() if current_user.subscription_starts_at else None,
        'subscription_ends_at': current_user.subscription_ends_at.isoformat() if current_user.subscription_ends_at else None,
        'is_on_trial': current_user.is_on_trial,
        'trial_ends_at': current_user.trial_ends_at.isoformat() if current_user.trial_ends_at else None,
        'can_access_premium': current_user.can_access_premium_features(),
        'user_type': current_user.user_type,
        'storage': {
            'used_bytes': current_user.used_storage_bytes,
            'total_bytes': current_user.get_total_storage_limit_bytes(),
            'percentage': current_user.get_storage_usage_percentage()
        }
    })

@billing_bp.route('/renew-annual', methods=['POST'])
@login_required
def renew_annual():
    """Renew annual subscription"""
    if current_user.subscription_type != 'annual':
        return jsonify({'error': 'Solo suscripciones anuales pueden renovarse'}), 400
    
    if not current_user.storage_plan:
        return jsonify({'error': 'Plan no encontrado'}), 400
    
    # Create new checkout session for renewal
    try:
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=current_user.id,
            customer_email=current_user.email,
            line_items=[{
                'price': current_user.storage_plan.stripe_price_annual,
                'quantity': 1
            }],
            mode='payment',
            success_url=url_for('billing_bp.checkout_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('billing_bp.checkout_cancel', _external=True),
            metadata={
                'user_id': current_user.id,
                'plan_id': current_user.storage_plan.id,
                'billing_cycle': 'annual',
                'is_renewal': 'true'
            }
        )
        
        return jsonify({
            'checkout_url': checkout_session.url
        })
        
    except Exception as e:
        current_app.logger.exception("Annual renewal error")
        return jsonify({'error': 'Error creando renovación'}), 500
