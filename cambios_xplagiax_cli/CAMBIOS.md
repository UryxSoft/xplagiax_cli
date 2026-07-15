# Correcciones de autenticación — xplagiax_appcli2

Fecha: 2026-07-15 · Rama: `claude/session-nc5rn1` (commit local `e38ebcf`, **no** pusheado)

## Cómo aplicar

Opción A — copiar los archivos (este tar conserva las rutas del repo):

```bash
tar -xzf cambios_xplagiax_cli.tar.gz
cp -r cambios_xplagiax_cli/files/xplagiax_appcli2/ /ruta/al/repo/
```

Opción B — aplicar el patch sobre el commit `4566c24` (main actual):

```bash
git apply cambios_xplagiax_cli/cambios.patch
# o con metadatos de commit:
git am cambios_xplagiax_cli/cambios.mbox
```

## Archivos modificados (9)

| Archivo | Fixes |
|---|---|
| `templates/auth/sign_users.html` | E1 (meta csrf-token), E5 (render de mensajes flash en el panel de login) |
| `static/js/enhanced_signin.js` | E1 (header X-CSRFToken), E4 (IIFE — fin de la colisión de funciones globales; errores del login ahora visibles y botón nunca se queda bloqueado) |
| `static/js/enhanced_signup.js` | E1 (header X-CSRFToken), E4 (IIFE + `window.togglePassword`), E10 (envía `lastname` como campo propio), E11 (mensajes de éxito acotados a `#signupForm`) |
| `modules/auth_service/auth_routes_fixed.py` | E2/E3 (fail-fast si falta client_id/secret), E6 (avatar Microsoft best-effort con `makedirs`), E7 (login exige `confirmed`), E8 (GET signup → `?mode=register`), E9 (resend_confirmation: `get_token` + `auth_bp.confirm_email`), E10 (acepta `lastname`), E12 (imports muertos fuera) |
| `modules/auth_service/google_oauth.py` | E2 (redirect_uri dinámica: `GOOGLE_REDIRECT_URI` o `url_for(_external=True)`) |
| `modules/auth_service/microsoft_oauth.py` | E3 (redirect_uri dinámica: `MICROSOFT_REDIRECT_URI` o `url_for(_external=True)`) |
| `modules/apps_service/apps_routes.py` | E8 (`/register` redirige a `login?mode=register` — el template `auth/signup.html` no existe) |
| `settings/config.py` | `REMEMBER_COOKIE_SAMESITE` de `strict` a `Lax` (con strict el remember-me se perdía al volver del IdP) |
| `settings/utilities.py` | Clave JWT env-first (`SECRET_KEY`) con fallback de compatibilidad |

## Causas raíz que esto corrige

1. **Login y registro devolvían 400 siempre**: `CSRFProtect` global exige token CSRF en todo POST y el frontend nunca lo enviaba (ni el template lo emitía). Ahora el token viaja en el header `X-CSRFToken`.
2. **Google OAuth**: `client_id` vacío sin env var y `redirect_uri` fija al puerto 5000 (la app corre en 5003) → `invalid_request` / `redirect_uri_mismatch`. Ahora la URI se deriva del host real de cada request (ProxyFix la hace correcta detrás de nginx) y la env var manda si está definida.
3. **Microsoft OAuth**: mismo mismatch de redirect URI; además, en despliegues limpios el guardado del avatar lanzaba `FileNotFoundError` (no existía `static/img/avatars/`) y abortaba el callback completo con rollback.
4. **Errores invisibles**: los dos JS se pisaban las funciones globales (los errores del login se pintaban en el panel oculto y el botón quedaba en spinner infinito) y la página nunca renderizaba los `flash()` de los callbacks OAuth.

## Pasos operativos OBLIGATORIOS (no son código)

1. **Variables de entorno** (producción y dev):
   - `SECRET_KEY` (fija y única — las cookies y los tokens de confirmación dependen de ella)
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` (rotar el secret que estaba hardcodeado en el repo)
   - Opcional: `GOOGLE_REDIRECT_URI` / `MICROSOFT_REDIRECT_URI` para forzar una URI concreta.
2. **Registrar las redirect URIs exactas** en las consolas:
   - Google Cloud Console: `https://app.xplagiax.ca/auth_bp/google/callbackx` (ojo con la `x` final) y la de dev `http://127.0.0.1:5003/auth_bp/google/callbackx`
   - Azure Portal: `https://app.xplagiax.ca/auth_bp/microsoft/callback` y `http://127.0.0.1:5003/auth_bp/microsoft/callback`
3. **Rotar TODOS los secretos que siguen hardcodeados en el repo** (SMTP, PayPal live, MySQL de producción, SerpAPI/Zenserp) y moverlos a env vars.
4. Cuando el login OAuth quede estable, poner `OAUTH_RELAX_STATE=false` para reactivar la validación anti-CSRF del `state`.

## Verificación posterior sugerida

- Login con email/contraseña: la respuesta debe ser 200 con `{redirect}` (antes 400).
- Registro: 201 y el usuario aparece con `name` y `lastname` separados.
- `/register` y `GET /auth_bp/signup`: redirigen al panel de registro (antes 500).
- Provocar un error OAuth (p. ej. cancelar en Google): el mensaje aparece en rojo en el panel de login (antes, silencio).
