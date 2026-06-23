# 📋 CHECKLIST DE IMPLEMENTACIÓN - SISTEMA DE PAGOS

## ✅ FASE 1: PREPARACIÓN (30 min)

### Dependencias
- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Verificar instalación: `python -c "import stripe, paypalrestsdk; print('OK')"`

### Archivos
- [ ] Copiar `billing_routes.py` a tu proyecto
- [ ] Copiar `pricing.html` a tu carpeta de templates
- [ ] Añadir configuración a `config.py`
- [ ] Crear archivo `.env` (recomendado para producción)

---

## ✅ FASE 2: CONFIGURACIÓN STRIPE (45 min)

### Cuenta y Claves
- [ ] Crear cuenta en [https://dashboard.stripe.com/register](https://dashboard.stripe.com/register)
- [ ] Obtener Publishable Key (pk_test_...)
- [ ] Obtener Secret Key (sk_test_...)
- [ ] Añadir claves a `config.py`

### Productos y Precios
- [ ] Crear producto "Scholar Suite" en Stripe Dashboard
  - [ ] Precio mensual: $15.00
  - [ ] Precio anual: $150.00
  - [ ] Copiar Price IDs (price_xxx)
- [ ] Crear producto "Individual"
  - [ ] Precio mensual: $25.00
  - [ ] Precio anual: $250.00
  - [ ] Copiar Price IDs
- [ ] Crear producto "Research Essentials"
  - [ ] Precio mensual: $45.00
  - [ ] Precio anual: $450.00
  - [ ] Copiar Price IDs

### Webhook
- [ ] Ir a Developers > Webhooks > Add endpoint
- [ ] URL: `https://tudominio.com/billing_bp/stripe/webhook`
- [ ] Seleccionar eventos:
  - [ ] checkout.session.completed
  - [ ] invoice.payment_succeeded
  - [ ] invoice.payment_failed
  - [ ] customer.subscription.deleted
  - [ ] customer.subscription.updated
  - [ ] invoice.upcoming
- [ ] Copiar Signing Secret (whsec_...)
- [ ] Añadir a `config.py` como `STRIPE_WEBHOOK_SECRET`

---

## ✅ FASE 3: CONFIGURACIÓN PAYPAL (45 min)

### Cuenta y Claves
- [ ] Crear cuenta en [https://developer.paypal.com/](https://developer.paypal.com/)
- [ ] Ir a Apps & Credentials
- [ ] Crear nueva app REST API
- [ ] Copiar Client ID
- [ ] Copiar Secret
- [ ] Añadir a `config.py`

### Crear Planes de Suscripción
- [ ] Ir a [PayPal Business Products](https://www.paypal.com/businessmanage/products/create)
- [ ] Crear plan "Scholar Suite Monthly"
  - [ ] Tipo: Subscription
  - [ ] Precio: $15.00
  - [ ] Frecuencia: Mensual
  - [ ] Copiar Plan ID (P-xxx)
- [ ] Crear plan "Scholar Suite Annual"
  - [ ] Precio: $150.00
  - [ ] Frecuencia: Anual
  - [ ] Copiar Plan ID
- [ ] Repetir para "Individual" ($25/$250)
- [ ] Repetir para "Research Essentials" ($45/$450)

### Cuentas de Prueba Sandbox
- [ ] Ir a [Sandbox Accounts](https://developer.paypal.com/dashboard/accounts)
- [ ] Crear cuenta Business (para recibir pagos)
- [ ] Crear cuenta Personal (para hacer pruebas)
- [ ] Anotar credenciales de la cuenta Personal

### Webhook (Solo para producción)
- [ ] En tu app, ir a Webhooks
- [ ] Add Webhook
- [ ] URL: `https://tudominio.com/billing_bp/paypal/webhook`
- [ ] Seleccionar eventos:
  - [ ] BILLING.SUBSCRIPTION.ACTIVATED
  - [ ] BILLING.SUBSCRIPTION.CANCELLED
  - [ ] BILLING.SUBSCRIPTION.SUSPENDED
  - [ ] PAYMENT.SALE.COMPLETED
  - [ ] PAYMENT.SALE.REFUNDED
- [ ] Copiar Webhook ID
- [ ] Añadir a `config.py`

---

## ✅ FASE 4: BASE DE DATOS (20 min)

### Estructura
- [ ] Ejecutar `database_setup.sql` para añadir columnas necesarias
- [ ] Verificar que Users tenga columnas de suscripción

### Datos de Planes
- [ ] Actualizar `storage_plans` con los Price IDs de Stripe
- [ ] Actualizar `storage_plans` con los Plan IDs de PayPal
- [ ] Verificar con query:
  ```sql
  SELECT name, stripe_price_monthly, paypal_plan_monthly 
  FROM storage_plans WHERE is_active = 1;
  ```

---

## ✅ FASE 5: INTEGRACIÓN (30 min)

### Código
- [ ] Registrar blueprint en `app.py`:
  ```python
  from billing_routes import billing_bp
  app.register_blueprint(billing_bp, url_prefix='/billing_bp')
  ```
- [ ] Inicializar Stripe en `app.py`:
  ```python
  import stripe
  stripe.api_key = app.config['STRIPE_SECRET_KEY']
  ```
- [ ] Verificar que `start_subscription()` existe en modelo User

### Rutas
- [ ] Verificar que todas las rutas estén disponibles
- [ ] Probar endpoint: `/billing_bp/plans`
- [ ] Verificar que retorna JSON con planes

---

## ✅ FASE 6: PRUEBAS (1-2 horas)

### Ejecutar Test Script
- [ ] Ejecutar `python test_payment_config.py`
- [ ] Verificar que todas las pruebas pasen
- [ ] Corregir errores si los hay

### Pruebas Stripe
- [ ] Abrir página de pricing
- [ ] Seleccionar plan "Individual"
- [ ] Elegir pago con Stripe
- [ ] Usar tarjeta de prueba: `4242 4242 4242 4242`
- [ ] Completar pago
- [ ] Verificar redirección a success
- [ ] Verificar en DB que subscription_id está guardado
- [ ] Verificar en Stripe Dashboard que la suscripción aparece

### Pruebas PayPal
- [ ] Seleccionar plan "Scholar Suite"
- [ ] Elegir pago con PayPal
- [ ] Iniciar sesión con cuenta sandbox Personal
- [ ] Aprobar pago
- [ ] Verificar redirección a success
- [ ] Verificar en DB que subscription_id está guardado
- [ ] Verificar en PayPal Dashboard que la suscripción aparece

### Pruebas de Webhooks (Con ngrok)
- [ ] Instalar ngrok: `npm install -g ngrok`
- [ ] Ejecutar: `ngrok http 5000`
- [ ] Actualizar webhook URL en Stripe Dashboard con URL de ngrok
- [ ] Hacer una compra de prueba
- [ ] Verificar que el webhook se recibe
- [ ] Verificar logs en consola
- [ ] Verificar que el usuario se actualiza en DB

### Pruebas de Cancelación
- [ ] Crear suscripción de prueba
- [ ] Ir a dashboard del usuario
- [ ] Cancelar suscripción
- [ ] Verificar que cambia a "canceled"
- [ ] Verificar en Stripe/PayPal que la cancelación se procesó

---

## ✅ FASE 7: SEGURIDAD Y OPTIMIZACIÓN (30 min)

### Seguridad
- [ ] Verificar que todas las claves estén en .env (no en código)
- [ ] Añadir .env a .gitignore
- [ ] Verificar que webhooks validen firma
- [ ] Implementar rate limiting en endpoints de pago
- [ ] Configurar HTTPS (requerido para producción)

### Logging
- [ ] Verificar que haya logs de pagos exitosos
- [ ] Verificar logs de pagos fallidos
- [ ] Configurar alertas para errores críticos

### UI/UX
- [ ] Verificar diseño responsive en móvil
- [ ] Probar selector de método de pago
- [ ] Verificar mensajes de error claros
- [ ] Probar loading states durante pagos

---

## ✅ FASE 8: PRE-PRODUCCIÓN (1 hora)

### Configuración Producción
- [ ] Cambiar `PAYPAL_MODE` a `'live'`
- [ ] Reemplazar todas las claves test por producción
- [ ] Configurar webhooks en producción (no sandbox)
- [ ] Verificar URLs de webhooks sean HTTPS

### Testing en Producción
- [ ] Hacer una compra real pequeña ($1) con tarjeta propia
- [ ] Verificar que el pago se procesa
- [ ] Verificar webhook en producción
- [ ] Cancelar la suscripción de prueba
- [ ] Solicitar reembolso en Stripe Dashboard

### Documentación
- [ ] Documentar proceso de pago para equipo
- [ ] Crear guía de troubleshooting
- [ ] Documentar cómo añadir nuevos planes
- [ ] Crear runbook para problemas comunes

---

## ✅ FASE 9: LANZAMIENTO (30 min)

### Pre-lanzamiento
- [ ] Backup completo de base de datos
- [ ] Verificar que todos los planes estén activos
- [ ] Verificar precios correctos en frontend
- [ ] Revisar términos y condiciones
- [ ] Revisar política de privacidad

### Monitoreo Post-lanzamiento
- [ ] Configurar alertas para pagos fallidos
- [ ] Monitorear dashboard de Stripe/PayPal primeras 24h
- [ ] Verificar que webhooks se reciban correctamente
- [ ] Revisar logs de errores cada hora
- [ ] Estar disponible para soporte

### Marketing
- [ ] Anunciar nuevos planes de pago
- [ ] Enviar email a usuarios existentes
- [ ] Actualizar documentación pública
- [ ] Actualizar FAQ

---

## ✅ FASE 10: MANTENIMIENTO (Continuo)

### Diario
- [ ] Revisar dashboard de pagos
- [ ] Verificar webhooks fallidos
- [ ] Responder tickets de soporte sobre pagos

### Semanal
- [ ] Revisar métricas de conversión
- [ ] Analizar abandonos en checkout
- [ ] Verificar suscripciones próximas a vencer
- [ ] Enviar recordatorios de renovación

### Mensual
- [ ] Reporte de revenue
- [ ] Análisis de churn rate
- [ ] Review de planes más populares
- [ ] Optimización de precios si es necesario

---

## 🆘 RECURSOS DE AYUDA

### Si algo falla:
1. Revisar logs de la aplicación
2. Revisar webhooks en Stripe/PayPal Dashboard
3. Ejecutar `python test_payment_config.py`
4. Consultar documentación:
   - [Stripe Docs](https://stripe.com/docs)
   - [PayPal Docs](https://developer.paypal.com/docs/)

### Contactos de Soporte:
- Stripe Support: [https://support.stripe.com/](https://support.stripe.com/)
- PayPal Support: [https://www.paypal.com/us/smarthelp/contact-us](https://www.paypal.com/us/smarthelp/contact-us)

---

## ✨ CHECKLIST COMPLETADO

- [ ] Todas las fases completadas
- [ ] Sistema probado en desarrollo
- [ ] Sistema probado en producción
- [ ] Equipo entrenado
- [ ] Documentación actualizada
- [ ] Monitoreo configurado

**¡Felicitaciones! Tu sistema de pagos está listo. 🎉**
