# PENDIENTE: Configurar PayPal Webhook en Producción

> Esto solo se hace UNA VEZ. Sin este paso, los pagos llegarán a PayPal
> pero el sistema NO activará el plan del usuario automáticamente.

---

## Contexto rápido

Cuando un usuario paga con PayPal, PayPal manda una notificación automática
a tu servidor (llamada "webhook"). Tu servidor verifica que esa notificación
sea legítima usando un **Webhook ID**. Ese ID es lo que necesitas obtener
y pegar en la variable de entorno `PAYPAL_WEBHOOK_ID`.

---

## PASO 1 — Entrar al panel de desarrollador de PayPal

1. Abre el navegador y ve a:
   ```
   https://developer.paypal.com
   ```
2. Haz clic en **"Log in"** (arriba a la derecha).
3. Entra con la cuenta PayPal de la empresa (la misma con la que creaste
   los planes de suscripción).

---

## PASO 2 — Ir a la sección de Apps

1. Una vez dentro, en el menú superior haz clic en **"Apps & Credentials"**.
2. Asegúrate de que el switch en la parte superior diga **"Live"** si vas a
   configurar producción, o **"Sandbox"** si estás probando.
   - Para producción real → **Live**
   - Para hacer pruebas → **Sandbox**

---

## PASO 3 — Seleccionar tu aplicación

1. Verás una lista de aplicaciones. Haz clic en la que ya tienes creada
   (la que tiene el `PAYPAL_CLIENT_ID` que está en `config.py`).
2. Si no sabes cuál es, puedes verificar comparando el **Client ID**
   que aparece en la app con el que está en el archivo
   `modules/settings_service/config.py` en la línea `PAYPAL_CLIENT_ID`.

---

## PASO 4 — Crear el Webhook

1. Dentro de la página de tu aplicación, baja hasta la sección
   **"Webhooks"**.
2. Haz clic en el botón **"Add Webhook"**.
3. En el campo **"Webhook URL"** escribe la URL de tu servidor:
   ```
   https://TU_DOMINIO.com/billing_bp/paypal/webhook
   ```
   Reemplaza `TU_DOMINIO.com` con tu dominio real, por ejemplo:
   ```
   https://xplagiax.ca/billing_bp/paypal/webhook
   ```
   > IMPORTANTE: Debe ser HTTPS. PayPal rechaza URLs con HTTP.

4. En la sección **"Event types"** (tipos de eventos), marca TODOS estos:
   - `BILLING.SUBSCRIPTION.ACTIVATED`
   - `BILLING.SUBSCRIPTION.CANCELLED`
   - `BILLING.SUBSCRIPTION.EXPIRED`
   - `BILLING.SUBSCRIPTION.SUSPENDED`
   - `BILLING.SUBSCRIPTION.PAYMENT.FAILED`

5. Haz clic en **"Save"**.

---

## PASO 5 — Copiar el Webhook ID

1. Después de guardar, PayPal te mostrará el webhook recién creado
   en la lista.
2. Haz clic en ese webhook para ver los detalles.
3. Busca el campo que dice **"Webhook ID"**. Se ve algo así:
   ```
   3HB37679MY652834T
   ```
4. Cópialo.

---

## PASO 6 — Pegar el Webhook ID en el servidor

Tienes que agregar esta variable de entorno en el servidor donde
corre la aplicación. Hay dos formas dependiendo de cómo tengas
el servidor:

### Opción A — Variable de entorno en el sistema (Linux/servidor)

Conéctate al servidor por SSH y ejecuta:

```bash
export PAYPAL_WEBHOOK_ID="PEGA_AQUI_EL_ID_QUE_COPIASTE"
```

Para que persista entre reinicios, agrégalo al archivo `/etc/environment`
o al archivo `~/.bashrc` / `~/.profile` del usuario que corre la app:

```bash
echo 'PAYPAL_WEBHOOK_ID="PEGA_AQUI_EL_ID_QUE_COPIASTE"' >> /etc/environment
```

### Opción B — Archivo `.env` (si usas python-dotenv o Docker)

Si tienes un archivo `.env` en la raíz del proyecto, agrégale esta línea:

```
PAYPAL_WEBHOOK_ID=PEGA_AQUI_EL_ID_QUE_COPIASTE
```

### Opción C — Variable en Docker Compose

Si usas `docker-compose.yml`, agrégala en la sección `environment`:

```yaml
environment:
  - PAYPAL_WEBHOOK_ID=PEGA_AQUI_EL_ID_QUE_COPIASTE
```

---

## PASO 7 — Reiniciar la aplicación

Después de agregar la variable, reinicia el servidor para que
la aplicación la lea:

```bash
# Si usas Gunicorn directamente
sudo systemctl restart xplagiax

# Si usas Docker
docker-compose down && docker-compose up -d

# Si usas Docker sin compose
docker restart nombre_del_contenedor
```

---

## PASO 8 — Verificar que funciona

1. En el panel de PayPal Developer, entra al webhook que creaste.
2. Busca el botón **"Send test event"** (o "Simulate webhook event").
3. Selecciona el evento `BILLING.SUBSCRIPTION.ACTIVATED` y mándalo.
4. Revisa los logs del servidor:
   ```bash
   # Si usas Docker
   docker logs nombre_del_contenedor --tail 50

   # Si usas journalctl
   journalctl -u xplagiax -n 50
   ```
5. Deberías ver una línea que diga:
   ```
   INFO ... PayPal webhook: BILLING.SUBSCRIPTION.ACTIVATED sub=...
   ```
   Si ves eso, todo está funcionando.

---

## Resumen de lo que está configurado en el código

Para tu referencia, esto es lo que ya está implementado y NO necesitas tocar:

| Qué | Archivo | Estado |
|-----|---------|--------|
| Verificación de firma del webhook | `billing_routes_fixed.py` | ✅ Implementado |
| Activar plan cuando `SUBSCRIPTION.ACTIVATED` | `billing_routes_fixed.py` | ✅ Implementado |
| Cancelar plan cuando `SUBSCRIPTION.CANCELLED` | `billing_routes_fixed.py` | ✅ Implementado |
| Manejar `EXPIRED`, `SUSPENDED`, `PAYMENT.FAILED` | `billing_routes_fixed.py` | ✅ Implementado |
| Endpoint para que el frontend obtenga el plan_id | `GET /billing_bp/paypal/get-plan` | ✅ Implementado |
| Endpoint para confirmar suscripción desde frontend | `POST /billing_bp/paypal/subscription-confirm` | ✅ Implementado |
| Cancelar suscripción desde el panel del usuario | `POST /billing_bp/cancel-subscription` | ✅ Implementado |

---

## Lo que falta del lado del FRONTEND

El botón de PayPal en el HTML debe usar este código JavaScript:

```javascript
paypal.Buttons({
    createSubscription: async function(data, actions) {
        // Obtiene el plan_id de PayPal desde el backend
        const resp = await fetch(
            '/billing_bp/paypal/get-plan?plan=NOMBRE_DEL_PLAN&billing_cycle=monthly'
            // Reemplaza NOMBRE_DEL_PLAN por el nombre exacto en la BD, ej: "Pro", "Basic"
            // billing_cycle puede ser "monthly" o "annual"
        );
        const { paypal_plan_id } = await resp.json();
        return actions.subscriptions.create({ plan_id: paypal_plan_id });
    },
    onApprove: async function(data) {
        // Confirma la suscripción con el backend (activa el plan en BD)
        await fetch('/billing_bp/paypal/subscription-confirm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                subscription_id: data.subscriptionID,
                plan: 'NOMBRE_DEL_PLAN',   // igual que arriba
                billing_cycle: 'monthly'    // o 'annual'
            })
        });
        // Redirigir al usuario al dashboard o recargar la página
        window.location.href = '/home';
    },
    onError: function(err) {
        console.error('PayPal error:', err);
        alert('Ocurrió un error con PayPal. Intenta de nuevo.');
    }
}).render('#paypal-button-container');
// '#paypal-button-container' es el id del div donde quieres que aparezca el botón
```

Y el script de PayPal SDK debe estar en el `<head>` del HTML:

```html
<script src="https://www.paypal.com/sdk/js?client-id=TU_PAYPAL_CLIENT_ID&vault=true&intent=subscription"></script>
```

Reemplaza `TU_PAYPAL_CLIENT_ID` con el valor de `PAYPAL_CLIENT_ID` en `config.py`.

---

> Una vez hecho el PASO 6 y reiniciado el servidor, los pagos
> se activarán automáticamente en la base de datos sin intervención manual.
