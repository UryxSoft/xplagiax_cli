// Login form handling.
// Encapsulado en IIFE: este archivo se carga junto a enhanced_signup.js y ambos
// definían funciones globales homónimas (showError, clearErrorStates,
// showValidationErrors, togglePassword); la versión de signup pisaba a la de
// signin y los errores del login se pintaban en el panel oculto de registro.
(function () {
    'use strict';

    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : '';
    }

    // Form submission handler with server integration
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) {
        return; // página sin formulario de login (p.ej. otras vistas que cargan este JS)
    }

    // ── 2FA step state ──────────────────────────────────────────────────────
    // pending_token identifica la sesión a medio autenticar (firmado server-side,
    // expira en 5 min — ver auth_routes_fixed.py). remember_me viaja aparte porque
    // el checkbox pertenece al form de login, que queda oculto durante este paso.
    // tfaMethods: qué método(s) tiene activos la cuenta ('totp' y/o 'email') —
    // controla el texto/maxlength del paso y si se ofrece "usar email en su lugar".
    let tfaPendingToken = null;
    let tfaRememberMe = false;
    let tfaMethods = ['totp'];
    let tfaActiveMethod = 'totp'; // cuál de los dos está mostrando el input ahora mismo

    const tfaLoginForm = document.getElementById('tfaLoginForm');
    const tfaBackLink = document.getElementById('tfaBackToLoginLink');
    const tfaUseEmailLink = document.getElementById('tfaUseEmailLink');

    // Adapta copy/maxlength/hints del paso 2FA al método activo. Se llama al
    // entrar al paso y de nuevo si el usuario pasa a "usar email en su lugar".
    function applyTfaMethodUI(method) {
        tfaActiveMethod = method;
        const desc = document.getElementById('tfaStepDesc');
        const codeInput = document.getElementById('tfa_code');
        const recoveryHint = document.getElementById('tfaRecoveryHint');
        const useEmailWrap = document.getElementById('tfaUseEmailWrap');
        const bothMethods = tfaMethods.includes('totp') && tfaMethods.includes('email');

        if (method === 'email') {
            if (desc) desc.textContent = 'Enter the 4-digit code we emailed you.';
            if (codeInput) { codeInput.maxLength = 4; codeInput.placeholder = '0000'; }
            if (recoveryHint) recoveryHint.style.display = 'none';
            if (useEmailWrap) useEmailWrap.style.display = 'none';
        } else {
            if (desc) desc.textContent = 'Enter the 6-digit code from your authenticator app.';
            if (codeInput) { codeInput.maxLength = 6; codeInput.placeholder = '000000'; }
            if (recoveryHint) recoveryHint.style.display = '';
            // Solo se ofrece el atajo "usar email" cuando la cuenta de verdad
            // tiene AMBOS métodos activos — si solo tiene TOTP, no hay a dónde
            // mandar el código.
            if (useEmailWrap) useEmailWrap.style.display = bothMethods ? '' : 'none';
        }
    }

    function showTfaStep(pendingToken, rememberMe, methods) {
        tfaPendingToken = pendingToken;
        tfaRememberMe = rememberMe;
        tfaMethods = Array.isArray(methods) && methods.length ? methods : ['totp'];
        loginForm.style.display = 'none';
        if (tfaLoginForm) {
            tfaLoginForm.style.display = 'block';
            const codeInput = document.getElementById('tfa_code');
            if (codeInput) { codeInput.value = ''; setTimeout(() => codeInput.focus(), 60); }
            // Método por defecto al entrar: TOTP si la cuenta lo tiene (ya se
            // mostró el paso porque el código llegó vía app), si no, email
            // (que login()/las OAuth callbacks ya dispararon el envío para).
            applyTfaMethodUI(tfaMethods.includes('totp') ? 'totp' : 'email');
        }
    }

    function backToLoginStep() {
        tfaPendingToken = null;
        if (tfaLoginForm) tfaLoginForm.style.display = 'none';
        loginForm.style.display = 'block';
        clearErrorStates();
    }

    if (tfaBackLink) {
        tfaBackLink.addEventListener('click', backToLoginStep);
    }

    if (tfaUseEmailLink) {
        tfaUseEmailLink.addEventListener('click', async function () {
            if (!tfaPendingToken) return;
            tfaUseEmailLink.textContent = 'Sending…';
            try {
                const res = await fetch('/auth_bp/2fa/email/send-login-code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                    body: JSON.stringify({ pending_token: tfaPendingToken })
                });
                const data = await res.json();
                if (!res.ok) {
                    showError(data.error || 'Could not send the code.');
                    tfaUseEmailLink.textContent = 'Send a code to my email instead';
                    return;
                }
                applyTfaMethodUI('email');
                const codeInput = document.getElementById('tfa_code');
                if (codeInput) { codeInput.value = ''; setTimeout(() => codeInput.focus(), 60); }
            } catch (_) {
                showError('Connection error. Please try again.');
                tfaUseEmailLink.textContent = 'Send a code to my email instead';
            }
        });
    }

    if (tfaLoginForm) {
        tfaLoginForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const codeInput = document.getElementById('tfa_code');
            const code = (codeInput.value || '').trim();
            const submitBtn = document.getElementById('tfaSubmitBtn');
            const btnText = document.getElementById('tfaBtnText');
            const progressBar = document.getElementById('tfaProgressBar');

            if (!code) {
                codeInput.closest('.input-container').classList.add('error-state');
                return;
            }
            codeInput.closest('.input-container').classList.remove('error-state');

            submitBtn.disabled = true;
            progressBar.style.display = 'block';
            btnText.innerHTML = '<span class="loading-spinner"></span> Verifying...';

            try {
                const response = await fetch('/auth_bp/2fa/verify-login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                    body: JSON.stringify({
                        pending_token: tfaPendingToken,
                        code: code,
                        remember_me: tfaRememberMe
                    })
                });
                const data = await response.json();
                progressBar.style.display = 'none';

                if (response.ok) {
                    btnText.innerHTML = `
                        <svg class="success-checkmark" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                        </svg>
                        Success!`;
                    setTimeout(() => { window.location.href = data.redirect || '/home'; }, 600);
                } else {
                    submitBtn.disabled = false;
                    btnText.textContent = 'Verify';
                    codeInput.closest('.input-container').classList.add('error-state');
                    tfaLoginForm.classList.add('error-shake');
                    setTimeout(() => tfaLoginForm.classList.remove('error-shake'), 500);
                    const existing = tfaLoginForm.querySelector('.error-message');
                    if (existing) existing.remove();
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-message';
                    errorDiv.textContent = data.error || 'Invalid code.';
                    tfaLoginForm.querySelector('.form-header').appendChild(errorDiv);
                    if (response.status === 401 && (data.error || '').includes('expired')) {
                        // pending_token venció (>5 min) — no hay nada que reintentar, forzar re-login.
                        setTimeout(backToLoginStep, 2000);
                    }
                }
            } catch (error) {
                progressBar.style.display = 'none';
                submitBtn.disabled = false;
                btnText.textContent = 'Verify';
            }
        });
    }

    // ── OAuth → 2FA bridge ────────────────────────────────────────────────
    // google_callbackx()/microsoft_callback() are plain GET redirects, not
    // fetch() calls — they can't hand the pending_token back the way login()
    // does. Instead they stash it server-side (Flask session) and redirect
    // here with ?oauth_2fa=1; this reads it once via a dedicated endpoint
    // and drops straight into the same #tfaLoginForm used for password
    // login. remember_me defaults true for OAuth, matching login_user
    // (remember=True) in both OAuth callbacks.
    (function bootstrapOAuthTfaIfPending() {
        const params = new URLSearchParams(window.location.search);
        if (params.get('oauth_2fa') !== '1') return;
        // Strip the marker immediately so a refresh/back-navigation doesn't
        // re-trigger this against an already-consumed (or absent) token.
        params.delete('oauth_2fa');
        const cleanQs = params.toString();
        history.replaceState(null, '', window.location.pathname + (cleanQs ? '?' + cleanQs : ''));

        fetch('/auth_bp/2fa/oauth-pending', { credentials: 'include' })
            .then(r => r.json())
            .then(data => {
                if (data && data.pending && data.pending_token) {
                    showTfaStep(data.pending_token, true, data.methods);
                }
            })
            .catch(() => { /* best-effort — user can just sign in again */ });
    })();

    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const email = document.getElementById('login_email').value;
        const password = document.getElementById('login_password').value;
        const rememberMe = document.getElementById('remember_me').checked;
        const submitBtn = document.getElementById('loginSubmitBtn');
        const btnText = document.getElementById('loginBtnText');
        const form = loginForm;
        const inputs = document.querySelectorAll('#loginForm .input'); // Scope to loginForm
        const progressBar = document.getElementById('loginProgressBar');

        // Remove any existing error states
        clearErrorStates();

        // Validation check
        if (!email || !password) {
            showValidationErrors(email, password);
            return;
        }

        // Start loading state
        form.classList.add('loading');
        submitBtn.disabled = true;
        progressBar.style.display = 'block';

        // Show loading spinner
        btnText.innerHTML = `
        <span class="loading-spinner"></span>
        Signing In...
    `;

        // Disable all inputs
        inputs.forEach(input => {
            input.disabled = true;
        });

        try {
            const formData = {
                email: email,
                password: password,
                remember_me: rememberMe
            };

            const response = await fetch('/auth_bp/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            // Remove loading state
            form.classList.remove('loading');
            progressBar.style.display = 'none';

            if (response.ok && data.requires_2fa) {
                // Password correct, but the account has 2FA on — hand off to
                // the code-entry step instead of redirecting. No session was
                // created server-side yet (see login() in auth_routes_fixed.py).
                submitBtn.disabled = false;
                btnText.textContent = 'Sign In';
                inputs.forEach(input => { input.disabled = false; });
                showTfaStep(data.pending_token, rememberMe, data.methods);
                return;
            }

            if (response.ok) {
                // SUCCESS STATE
                form.classList.add('success');

                btnText.innerHTML = `
                <svg class="success-checkmark" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
                Success!
            `;

                submitBtn.style.background = '#10b981';

                // Redirect after success animation
                setTimeout(() => {
                    window.location.href = data.redirect || '/home';
                }, 800);

            } else {
                // SERVER ERROR STATE
                const errorMessage = data.error || 'Invalid credentials. Please check your email and password.';

                // Dramatic shake and persistent loading effect on login failure
                if (response.status === 401 || errorMessage.toLowerCase().includes('password') || errorMessage.toLowerCase().includes('credentials')) {
                    const inputContainers = loginForm.querySelectorAll('.input-container');

                    // 1. Show the error message first (but we'll override the button/form states)
                    showError(errorMessage);

                    // 2. Override states for dramatic effect
                    loginForm.classList.add('error-shake', 'error-state');
                    submitBtn.classList.add('error');
                    submitBtn.disabled = true; // Stay blocked
                    inputContainers.forEach(container => container.classList.add('error-state'));

                    // Show loading animation on red button
                    btnText.innerHTML = `<span class="loading-spinner"></span> Verification failed...`;

                    // Revert to normal after a delay (e.g., 3 seconds)
                    setTimeout(() => {
                        loginForm.classList.remove('error-shake', 'error-state');
                        submitBtn.classList.remove('error');
                        submitBtn.disabled = false;
                        btnText.textContent = 'Sign In';
                        inputContainers.forEach(container => container.classList.remove('error-state'));
                    }, 3000);
                } else {
                    showError(errorMessage);
                }
            }

        } catch (error) {
            // CONNECTION ERROR STATE
            form.classList.remove('loading');
            progressBar.style.display = 'none';
            showError('Connection error. Please check your internet connection and try again.');
        }
    });

    function showError(message) {
        const form = loginForm;
        const submitBtn = document.getElementById('loginSubmitBtn');
        const btnText = document.getElementById('loginBtnText');
        const formHeader = form.querySelector('.form-header');

        // Add error state to form
        form.classList.add('error-state');

        // Create error message
        const existingError = form.querySelector('.error-message');
        if (existingError) existingError.remove();

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
        ${message}
    `;

        formHeader.appendChild(errorDiv);

        // Reset button state (keep it normal)
        submitBtn.classList.remove('error');
        submitBtn.disabled = false;
        btnText.textContent = 'Sign In';

        // Enable inputs for retry
        const inputs = document.querySelectorAll('#loginForm .input');
        inputs.forEach(input => {
            input.disabled = false;
        });

        // Auto-clear error after 5 seconds
        setTimeout(() => {
            clearErrorStates();
        }, 5000);
    }

    function showValidationErrors(email, password) {
        const form = loginForm;

        form.classList.add('error-state');

        // Highlight empty fields
        if (!email) {
            const emailContainer = document.getElementById('login_email').closest('.input-container');
            emailContainer.classList.add('error-state');
        }

        if (!password) {
            const passwordContainer = document.getElementById('login_password').closest('.input-container');
            passwordContainer.classList.add('error-state');
        }

        // Shake whole form
        form.classList.add('error-shake');

        // Show validation message
        const message = !email && !password ?
            'Please fill in all fields' :
            !email ? 'Please enter your email' : 'Please enter your password';

        showError(message);

        // Clear shake animation
        setTimeout(() => {
            form.classList.remove('error-shake');
        }, 500);
    }

    function clearErrorStates() {
        const form = loginForm;
        const submitBtn = document.getElementById('loginSubmitBtn');
        const btnText = document.getElementById('loginBtnText');
        const errorMessage = form.querySelector('.error-message');
        const errorContainers = form.querySelectorAll('.input-container.error-state');

        // Remove form error state
        form.classList.remove('error-state');

        // Clear button error state
        submitBtn.classList.remove('error', 'error-shake');
        submitBtn.style.background = '#1a1a1a';
        submitBtn.disabled = false;

        // Reset button text
        btnText.textContent = 'Sign In';

        // Remove error message with animation
        if (errorMessage) {
            errorMessage.classList.add('error-message-hide');
            setTimeout(() => errorMessage.remove(), 300);
        }

        // Clear input error states
        errorContainers.forEach(container => {
            container.classList.remove('error-state');
        });
    }

    // Add shake animation styles
    const style = document.createElement('style');
    style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-8px); }
        20%, 40%, 60%, 80% { transform: translateX(8px); }
    }
`;
    document.head.appendChild(style);
})();
