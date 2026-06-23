# ============================================
# CONFIGURACIÓN DE PAGOS - config.py
# ============================================

# STRIPE CONFIGURATION
STRIPE_PUBLISHABLE_KEY = 'pk_test_xxxxxxxxxxxxxxxxxxxxx'  # Clave pública de Stripe (Test/Live)
STRIPE_SECRET_KEY = 'sk_test_xxxxxxxxxxxxxxxxxxxxx'  # Clave secreta de Stripe (Test/Live)
STRIPE_WEBHOOK_SECRET = 'whsec_xxxxxxxxxxxxxxxxxxxxx'  # Secret del webhook de Stripe

# PAYPAL CONFIGURATION
PAYPAL_MODE = 'sandbox'  # 'sandbox' para desarrollo, 'live' para producción
PAYPAL_CLIENT_ID = 'AxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxZQ'  # Client ID de PayPal
PAYPAL_CLIENT_SECRET = 'ExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxGg'  # Secret de PayPal
PAYPAL_WEBHOOK_ID = '1WR12345678901234567890'  # ID del webhook de PayPal (opcional para sandbox)

# ============================================
# INSTRUCCIONES DE CONFIGURACIÓN
# ============================================

"""
STRIPE SETUP:
1. Ve a https://dashboard.stripe.com/
2. Copia tu Publishable Key y Secret Key desde "Developers > API keys"
3. Configura un webhook en "Developers > Webhooks":
   - URL: https://tudominio.com/billing_bp/stripe/webhook
   - Eventos a escuchar:
     * checkout.session.completed
     * invoice.payment_succeeded
     * invoice.payment_failed
     * customer.subscription.deleted
     * customer.subscription.updated
     * invoice.upcoming
4. Copia el "Signing secret" del webhook

PAYPAL SETUP:
1. Ve a https://developer.paypal.com/dashboard/
2. En "Apps & Credentials", crea una nueva app REST API
3. Copia el Client ID y Secret Key
4. Para webhooks (en producción):
   - Ve a "Webhooks" en tu app
   - Añade webhook URL: https://tudominio.com/billing_bp/paypal/webhook
   - Selecciona eventos:
     * BILLING.SUBSCRIPTION.ACTIVATED
     * BILLING.SUBSCRIPTION.CANCELLED
     * BILLING.SUBSCRIPTION.SUSPENDED
     * PAYMENT.SALE.COMPLETED
     * PAYMENT.SALE.REFUNDED
   - Copia el Webhook ID

SANDBOX TESTING:
Para probar PayPal en sandbox:
1. Ve a https://developer.paypal.com/dashboard/accounts
2. Crea cuentas de prueba (Business y Personal)
3. Usa las credenciales de la cuenta Personal para hacer pruebas

USUARIOS DE PRUEBA PAYPAL SANDBOX:
- Email: sb-buyer@personal.example.com (generado automáticamente)
- Password: (generada por PayPal)

TARJETAS DE PRUEBA STRIPE:
- Visa exitosa: 4242 4242 4242 4242
- Visa requiere autenticación: 4000 0027 6000 3184
- Visa declinada: 4000 0000 0000 0002
- Fecha de expiración: Cualquier fecha futura
- CVC: Cualquier 3 dígitos
- ZIP: Cualquier código postal

CONFIGURACIÓN EN LA BASE DE DATOS:
Asegúrate de tener estos campos en tu tabla StoragePlan:
- stripe_price_monthly (VARCHAR)
- stripe_price_annual (VARCHAR)
- paypal_plan_monthly (VARCHAR)
- paypal_plan_annual (VARCHAR)

Ejemplo de datos:
INSERT INTO storage_plans (
    name, 
    stripe_price_monthly, 
    stripe_price_annual, 
    paypal_plan_monthly, 
    paypal_plan_annual
) VALUES (
    'Scholar Suite',
    'price_1xxxxxxxxxxxxx',  -- ID de precio mensual en Stripe
    'price_1xxxxxxxxxxxxx',  -- ID de precio anual en Stripe
    'P-xxxxxxxxxxxxx',       -- ID de plan mensual en PayPal
    'P-xxxxxxxxxxxxx'        -- ID de plan anual en PayPal
);

MIGRACIÓN A PRODUCCIÓN:
1. Cambia PAYPAL_MODE de 'sandbox' a 'live'
2. Reemplaza todas las claves de prueba por las de producción
3. Configura webhooks en los dashboards de producción
4. Prueba con pequeñas transacciones reales antes del lanzamiento
"""

# ============================================
# VARIABLES DE ENTORNO (.env)
# ============================================

"""
Para mayor seguridad, considera usar variables de entorno:

# .env file
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=AxxxxxxxxxxxxxxxxxxxxxxxxZQ
PAYPAL_CLIENT_SECRET=ExxxxxxxxxxxxxxxxxxxxxxxxGg
PAYPAL_WEBHOOK_ID=1WR12345678901234567890

Luego en tu config.py:
import os
from dotenv import load_dotenv

load_dotenv()

STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
PAYPAL_WEBHOOK_ID = os.getenv('PAYPAL_WEBHOOK_ID')
"""
