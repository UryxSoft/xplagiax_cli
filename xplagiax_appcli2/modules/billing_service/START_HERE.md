# 🚀 GUÍA RÁPIDA DE INICIO - 5 MINUTOS

## Lo que tienes:

📁 **7 archivos nuevos:**
1. `billing_routes.py` - Backend completo con Stripe y PayPal
2. `pricing.html` - Frontend con selector de pagos
3. `config_example.py` - Plantilla de configuración
4. `requirements.txt` - Dependencias
5. `README.md` - Documentación completa
6. `test_payment_config.py` - Script de verificación
7. `database_setup.sql` - Queries SQL
8. `IMPLEMENTATION_CHECKLIST.md` - Lista de tareas

---

## ⚡ INICIO RÁPIDO (20 minutos)

### 1. Instalar dependencias (2 min)
```bash
pip install stripe==7.8.0
pip install paypalrestsdk==1.13.1
```

### 2. Configurar Stripe (8 min)
1. Ve a https://dashboard.stripe.com/register
2. Copia tus claves en `Developers > API keys`
3. Añade a tu `config.py`:
```python
STRIPE_SECRET_KEY = 'sk_test_...'
STRIPE_PUBLISHABLE_KEY = 'pk_test_...'
```

### 3. Configurar PayPal (8 min)
1. Ve a https://developer.paypal.com/
2. Crea una app REST API
3. Copia Client ID y Secret
4. Añade a tu `config.py`:
```python
PAYPAL_MODE = 'sandbox'
PAYPAL_CLIENT_ID = 'tu_client_id'
PAYPAL_CLIENT_SECRET = 'tu_secret'
```

### 4. Integrar código (2 min)
```python
# En tu app.py
from billing_routes import billing_bp
app.register_blueprint(billing_bp, url_prefix='/billing_bp')

import stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']
```

---

## 🎯 PRÓXIMOS PASOS

### Para empezar a probar:
1. Ejecuta: `python test_payment_config.py`
2. Abre: `http://localhost:5000/pricing`
3. Prueba un pago con: `4242 4242 4242 4242`

### Para producción:
1. Lee `README.md` completo
2. Sigue `IMPLEMENTATION_CHECKLIST.md`
3. Configura webhooks
4. Actualiza base de datos con `database_setup.sql`

---

## 📞 ¿PROBLEMAS?

**Error: Module not found**
```bash
pip install -r requirements.txt
```

**Error: Can't connect to Stripe**
- Verifica que las claves sean correctas
- Asegúrate de usar las claves de TEST (sk_test_...)

**Error: Can't connect to PayPal**
- Verifica Client ID y Secret
- Asegúrate de que `PAYPAL_MODE = 'sandbox'`

**Error: No plans found**
- Ejecuta los queries de `database_setup.sql`
- Actualiza los Price IDs de Stripe y Plan IDs de PayPal

---

## 📚 DOCUMENTACIÓN

- **Guía completa:** `README.md`
- **Checklist de implementación:** `IMPLEMENTATION_CHECKLIST.md`
- **Configuración:** `config_example.py`
- **SQL:** `database_setup.sql`

---

## ✅ VERIFICACIÓN RÁPIDA

Ejecuta este comando para verificar que todo funciona:
```bash
python test_payment_config.py
```

Si todas las pruebas pasan: **¡Estás listo! 🎉**

Si hay errores: Revisa el output y corrige según las indicaciones.

---

## 💡 TIPS IMPORTANTES

1. **SIEMPRE** empieza en modo sandbox/test
2. **NUNCA** subas tus claves a Git
3. **USA** .env para variables sensibles
4. **PRUEBA** con tarjetas de prueba antes de producción
5. **LEE** la documentación completa antes de ir a producción

---

## 🎓 RECURSOS DE APRENDIZAJE

- Stripe Testing: https://stripe.com/docs/testing
- PayPal Sandbox: https://developer.paypal.com/dashboard/accounts
- Webhook Testing: https://ngrok.com/

---

**¿Listo para empezar?** 
1. Instala dependencias
2. Configura claves
3. Ejecuta test script
4. ¡Comienza a aceptar pagos!

**¡Buena suerte! 🚀**
