// Toggle password function
function togglePassword() {
    const passwordInput = document.getElementById('login_password');
    const eyeIcon = document.getElementById('loginEyeIcon');

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        eyeIcon.innerHTML = '<path d="M11.83 9L15 12.16V12a3 3 0 0 0-3-3h-.17zm-4.3.8l1.55 1.55c-.05.21-.08.42-.08.65a3 3 0 0 0 3 3c.22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53a5 5 0 0 1-5-5c0-.79.2-1.53.53-2.2zm-.84-.84L8.46 7.3A9.05 9.05 0 0 0 6 12c0 5 4 10 6 10a9.11 9.05 0 0 0 3.3-.62l1.79 1.79 1.42-1.42L3.42 6.42 2 7.84zm6.47 6.47L10.5 12.6A1 1 0 0 1 12 11c0-.22-.06-.44-.16-.64l-1.86-1.86A3 3 0 0 1 12 8a3 3 0 0 1 3 3l2.4 2.4A9.05 9.05 0 0 0 18 12c0-5-4-10-6-10-.85 0-1.69.18-2.47.5L10.38 3.9a1 1 0 0 1 1.24 0L13.16 5.4z"/>';
    } else {
        passwordInput.type = 'password';
        eyeIcon.innerHTML = '<path d="M15 12c0 1.654-1.346 3-3 3s-3-1.346-3-3 1.346-3 3-3 3 1.346 3 3zm9-.449s-4.252 8.449-11.985 8.449c-7.18 0-12.015-8.449-12.015-8.449s4.446-7.551 12.015-7.551c7.694 0 11.985 7.551 11.985 7.551zm-7 .449c0-2.757-2.243-5-5-5s-5 2.243-5 5 2.243 5 5 5 5-2.243 5-5z"/>';
    }
}

// Form submission handler with server integration
document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const email = document.getElementById('login_email').value;
    const password = document.getElementById('login_password').value;
    const rememberMe = document.getElementById('remember_me').checked;
    const submitBtn = document.getElementById('loginSubmitBtn');
    const btnText = document.getElementById('loginBtnText');
    const form = document.querySelector('.form'); // Note: This might still be issue if classes are shared, but selectors inside might differ.
    // However, loginForm is ID selector, so it's specific.
    // The .form class is used for styling and error states. specific selection might be needed if both forms are visible/conflicting, 
    // but they are in separate panels.
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
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        // Remove loading state
        form.classList.remove('loading');
        progressBar.style.display = 'none';

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
                const loginForm = document.getElementById('loginForm');
                const submitBtn = document.getElementById('loginSubmitBtn');
                const btnText = document.getElementById('loginBtnText');
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
    const form = document.getElementById('loginForm');
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
    const inputs = document.querySelectorAll('.input');
    inputs.forEach(input => {
        input.disabled = false;
    });

    // Auto-clear error after 5 seconds
    setTimeout(() => {
        clearErrorStates();
    }, 5000);
}

function showValidationErrors(email, password) {
    const submitBtn = document.getElementById('loginSubmitBtn');
    const form = document.querySelector('.form');

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
    const form = document.querySelector('.form');
    const submitBtn = document.getElementById('loginSubmitBtn');
    const btnText = document.getElementById('loginBtnText');
    const errorMessage = document.querySelector('.error-message');
    const errorContainers = document.querySelectorAll('.input-container.error-state');

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