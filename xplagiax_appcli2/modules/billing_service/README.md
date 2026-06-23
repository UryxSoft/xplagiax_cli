# Sistema de Pagos con Stripe y PayPal - Guía de Implementación

## 📋 Contenido

1. [Instalación](#instalación)
2. [Configuración Stripe](#configuración-stripe)
3. [Configuración PayPal](#configuración-paypal)
4. [Estructura de Base de Datos](#estructura-de-base-de-datos)
5. [Implementación](#implementación)
6. [Pruebas](#pruebas)
7. [Producción](#producción)

---

## 🚀 Instalación

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

O instalar manualmente:

```bash
pip install stripe==7.8.0
pip install paypalrestsdk==1.13.1
pip install python-dotenv==1.0.0
```

### 2. Verificar Instalación

```python
import stripe
import paypalrestsdk
print("✅ Dependencias instaladas correctamente")
```

---

## 💳 Configuración Stripe

### 1. Crear Cuenta Stripe

1. Ve a [https://dashboard.stripe.com/register](https://dashboard.stripe.com/register)
2. Crea tu cuenta (empieza en modo Test)

### 2. Obtener API Keys

1. Ve a **Developers > API keys**
2. Copia las siguientes claves:
   - **Publishable key** (pk_test_...)
   - **Secret key** (sk_test_...)

### 3. Crear Precios en Stripe

1. Ve a **Products > Add Product**
2. Crea un producto para cada plan
3. Añade precios (monthly/annual)
4. Copia los **Price IDs** (price_xxx)

### 4. Configurar Webhook

1. Ve a **Developers > Webhooks > Add endpoint**
2. URL: `https://tudominio.com/billing_bp/stripe/webhook`
3. Selecciona estos eventos:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
   - `invoice.upcoming`
4. Copia el **Signing secret** (whsec_...)

### 5. Añadir a tu Config

```python
STRIPE_PUBLISHABLE_KEY = 'pk_test_xxxxxxxxxxxxxxxxxxxxx'
STRIPE_SECRET_KEY = 'sk_test_xxxxxxxxxxxxxxxxxxxxx'
STRIPE_WEBHOOK_SECRET = 'whsec_xxxxxxxxxxxxxxxxxxxxx'
```

---

## 🅿️ Configuración PayPal

### 1. Crear Cuenta Developer

1. Ve a [https://developer.paypal.com/](https://developer.paypal.com/)
2. Inicia sesión o crea cuenta

### 2. Crear App REST

1. Ve a **Apps & Credentials**
2. Click en **Create App**
3. Selecciona **Merchant** como tipo
4. Copia:
   - **Client ID**
   - **Secret**

### 3. Crear Planes de Suscripción

#### Opción A: Desde el Dashboard (Recomendado)

1. Ve a [PayPal Business](https://www.paypal.com/businessmanage/products/create)
2. Create Product > Subscription
3. Define:
   - Nombre del plan
   - Descripción
   - Precio mensual/anual
   - Frecuencia de cobro
4. Copia el **Plan ID** (P-xxxxxxxxxxxxx)

#### Opción B: Por API

```python
import paypalrestsdk

paypalrestsdk.configure({
    'mode': 'sandbox',
    'client_id': 'tu_client_id',
    'client_secret': 'tu_secret'
})

billing_plan = paypalrestsdk.BillingPlan({
    "name": "Scholar Suite Monthly",
    "description": "Suscripción mensual Scholar Suite",
    "type": "INFINITE",
    "payment_definitions": [{
        "name": "Regular Payment",
        "type": "REGULAR",
        "frequency": "MONTH",
        "frequency_interval": "1",
        "cycles": "0",
        "amount": {
            "value": "15.00",
            "currency": "USD"
        }
    }],
    "merchant_preferences": {
        "return_url": "https://tudominio.com/billing_bp/checkout-success",
        "cancel_url": "https://tudominio.com/billing_bp/checkout-cancel",
        "auto_bill_amount": "YES",
        "initial_fail_amount_action": "CONTINUE",
        "max_fail_attempts": "3"
    }
})

if billing_plan.create():
    print(f"Plan ID: {billing_plan.id}")
```

### 4. Configurar Webhook (Producción)

1. En tu app, ve a **Webhooks**
2. Click **Add Webhook**
3. URL: `https://tudominio.com/billing_bp/paypal/webhook`
4. Eventos:
   - `BILLING.SUBSCRIPTION.ACTIVATED`
   - `BILLING.SUBSCRIPTION.CANCELLED`
   - `BILLING.SUBSCRIPTION.SUSPENDED`
   - `PAYMENT.SALE.COMPLETED`
   - `PAYMENT.SALE.REFUNDED`
5. Copia el **Webhook ID**

### 5. Añadir a tu Config

```python
PAYPAL_MODE = 'sandbox'  # cambiar a 'live' en producción
PAYPAL_CLIENT_ID = 'AxxxxxxxxxxxxxxxxxxxxxxxxZQ'
PAYPAL_CLIENT_SECRET = 'ExxxxxxxxxxxxxxxxxxxxxxxxGg'
PAYPAL_WEBHOOK_ID = '1WR12345678901234567890'  # opcional en sandbox
```

---

## 🗄️ Estructura de Base de Datos

### Tabla: storage_plans

Añade estas columnas si no las tienes:

```sql
ALTER TABLE storage_plans ADD COLUMN stripe_price_monthly VARCHAR(255);
ALTER TABLE storage_plans ADD COLUMN stripe_price_annual VARCHAR(255);
ALTER TABLE storage_plans ADD COLUMN paypal_plan_monthly VARCHAR(255);
ALTER TABLE storage_plans ADD COLUMN paypal_plan_annual VARCHAR(255);
```

### Ejemplo de Datos

```sql
INSERT INTO storage_plans (
    name, 
    description,
    price_monthly_usd,
    price_annual_usd,
    stripe_price_monthly, 
    stripe_price_annual, 
    paypal_plan_monthly, 
    paypal_plan_annual,
    trial_days,
    is_active
) VALUES (
    'Scholar Suite',
    'Plan para estudiantes',
    15.00,
    150.00,
    'price_1xxxxStripeMonthly',
    'price_1xxxxStripeAnnual',
    'P-1xxxxPayPalMonthly',
    'P-2xxxxPayPalAnnual',
    14,
    1
);
```

---

## 📦 Implementación

### 1. Copiar Archivos

```
tu_proyecto/
├── billing_routes.py          # ✅ Reemplazar archivo completo
├── templates/
│   └── pricing.html           # ✅ Reemplazar o crear
├── config.py                  # ✅ Añadir configuración
└── requirements.txt           # ✅ Verificar dependencias
```

### 2. Registrar Blueprint

En tu `app.py` o `__init__.py`:

```python
from billing_routes import billing_bp

app.register_blueprint(billing_bp, url_prefix='/billing_bp')
```

### 3. Inicializar Stripe

En tu `app.py`:

```python
import stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']
```

### 4. Verificar Rutas

Las siguientes rutas deben estar disponibles:

```
GET  /billing_bp/plans
POST /billing_bp/create-checkout-session
GET  /billing_bp/checkout-success
GET  /billing_bp/checkout-cancel
POST /billing_bp/stripe/webhook
POST /billing_bp/paypal/create-order
POST /billing_bp/paypal/execute-agreement
POST /billing_bp/paypal/webhook
POST /billing_bp/cancel-subscription
GET  /billing_bp/subscription-status
```

---

## 🧪 Pruebas

### Probar Stripe (Tarjetas de Prueba)

```
Visa exitosa:           4242 4242 4242 4242
Visa con 3D Secure:     4000 0027 6000 3184
Visa declinada:         4000 0000 0000 0002
Mastercard exitosa:     5555 5555 5555 4444

Fecha: Cualquier fecha futura
CVC: Cualquier 3 dígitos
ZIP: Cualquier código
```

### Probar PayPal (Sandbox)

1. Ve a [PayPal Sandbox Accounts](https://developer.paypal.com/dashboard/accounts)
2. Crea cuentas de prueba:
   - **Business Account** (para recibir pagos)
   - **Personal Account** (para hacer pagos)
3. Usa las credenciales de la Personal Account para pagar

Ejemplo:
```
Email: sb-buyer@personal.example.com
Password: (generada automáticamente)
```

### Probar Webhooks Localmente

Usa **ngrok** para exponer tu localhost:

```bash
# Instalar ngrok
npm install -g ngrok

# Exponer puerto
ngrok http 5000

# Usa la URL generada en tus webhooks:
# https://xxxx-xxx-xxx-xxx-xxx.ngrok.io/billing_bp/stripe/webhook
```

### Comandos de Prueba

```python
# En Python shell
from app import app, db
from modules.models.model import StoragePlan

# Verificar planes
plans = StoragePlan.query.filter_by(is_active=True).all()
for plan in plans:
    print(f"{plan.name}: Stripe={plan.stripe_price_monthly}, PayPal={plan.paypal_plan_monthly}")
```

---

## 🚀 Producción

### Checklist Pre-Producción

- [ ] Cambiar todas las claves de test a producción
- [ ] Cambiar `PAYPAL_MODE` a `'live'`
- [ ] Configurar webhooks en producción
- [ ] Probar con transacciones reales pequeñas
- [ ] Configurar SSL/HTTPS (requerido)
- [ ] Configurar manejo de errores y logging
- [ ] Implementar reintentos automáticos
- [ ] Configurar emails de confirmación
- [ ] Revisar términos y condiciones
- [ ] Implementar política de reembolsos

### Variables de Entorno en Producción

Usa `.env` en producción:

```bash
# .env
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxxxxxxxxxx
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=AxxxxxxxxxxxxxxxxxxxxxxxxZQ
PAYPAL_CLIENT_SECRET=ExxxxxxxxxxxxxxxxxxxxxxxxGg
PAYPAL_WEBHOOK_ID=1WR12345678901234567890
```

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
# ... resto de configuración
```

### Monitoreo

- Stripe Dashboard: [https://dashboard.stripe.com/](https://dashboard.stripe.com/)
- PayPal Dashboard: [https://www.paypal.com/businessmanage/](https://www.paypal.com/businessmanage/)

### Logs Importantes

```python
# Ver logs de pagos
tail -f /var/log/app/payments.log

# Ver webhooks de Stripe
# Stripe Dashboard > Developers > Webhooks > Ver detalles

# Ver webhooks de PayPal
# PayPal Dashboard > Webhooks > Ver eventos
```

---

## 🐛 Troubleshooting

### Error: "Webhook signature verification failed"

**Stripe:**
- Verifica que `STRIPE_WEBHOOK_SECRET` sea correcto
- Asegúrate de usar el secret del webhook específico
- Revisa que la URL del webhook sea exacta

**PayPal:**
- Comenta la verificación en sandbox si no tienes webhook_id
- En producción, asegúrate de tener el webhook_id configurado

### Error: "No plans found"

```python
# Verificar planes en DB
from app import db
from modules.models.model import StoragePlan

plans = StoragePlan.query.filter_by(is_active=True).all()
for plan in plans:
    print(f"Plan: {plan.name}")
    print(f"  Stripe Monthly: {plan.stripe_price_monthly}")
    print(f"  PayPal Monthly: {plan.paypal_plan_monthly}")
```

### Error: "PayPal authentication failed"

- Verifica que client_id y client_secret sean correctos
- Asegúrate de estar en el modo correcto (sandbox/live)
- Revisa que las credenciales correspondan al modo

### Error: "Subscription not found"

- Verifica que el subscription_id se esté guardando correctamente
- Revisa que subscription_provider sea 'stripe' o 'paypal'
- Verifica la función `start_subscription()` en tu modelo User

---

## 📞 Soporte

- **Stripe Docs:** [https://stripe.com/docs](https://stripe.com/docs)
- **PayPal Docs:** [https://developer.paypal.com/docs/](https://developer.paypal.com/docs/)
- **Stripe Support:** [https://support.stripe.com/](https://support.stripe.com/)
- **PayPal Support:** [https://www.paypal.com/us/smarthelp/contact-us](https://www.paypal.com/us/smarthelp/contact-us)

---

## 📄 Licencia

Este código es para uso interno del proyecto XplagiaX.

---

**¡Listo para aceptar pagos!** 🎉
