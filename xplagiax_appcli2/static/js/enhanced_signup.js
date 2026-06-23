// Enhanced signup functionality with password strength checker
document.addEventListener('DOMContentLoaded', function () {
    const signupForm = document.getElementById('signupForm');

    if (!signupForm) {
        console.error('signupForm not found');
        return;
    }

    // Initialize password strength checker
    initializePasswordStrengthChecker();

    // Form submission handler
    signupForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const name = document.getElementById('name').value.trim();
        const lastname = document.getElementById('lastname').value.trim();
        const email = document.getElementById('signup_email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('password_confirm').value;
        const submitBtn = document.getElementById('signupSubmitBtn');
        const btnText = document.getElementById('signupBtnText');
        const form = document.getElementById('signupForm'); // prefer ID over class .form for specificity if possible, but keep .form logic if styled that way
        const inputs = document.querySelectorAll('#signupForm .input');
        const progressBar = document.getElementById('signupProgressBar');

        // Remove any existing error states
        clearErrorStates();

        // Validation check
        if (!name || !lastname || !email || !password || !confirmPassword) {
            showValidationErrors(name, lastname, email, password, confirmPassword);
            return;
        }

        // Email format validation
        if (!isValidEmail(email)) {
            showError('Please enter a valid email address');
            return;
        }

        // Password strength validation
        const passwordStrength = checkPasswordStrength(password);
        if (passwordStrength.score < 2) {
            showError('The password must be stronger. ' + passwordStrength.feedback);
            return;
        }

        // Password confirmation check
        if (password !== confirmPassword) {
            showPasswordMismatchError();
            return;
        }

        // Start loading state
        form.classList.add('loading');
        submitBtn.disabled = true;
        if (progressBar) progressBar.style.display = 'block';

        // Show loading spinner
        btnText.innerHTML = `
            <span class="loading-spinner"></span>
            Registering...
        `;

        // Disable all inputs
        inputs.forEach(input => {
            input.disabled = true;
        });

        try {
            const formData = {
                name: name + ' ' + lastname,
                email: email,
                password: password
            };

            const response = await fetch('/auth_bp/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            // Remove loading state
            form.classList.remove('loading');
            if (progressBar) progressBar.style.display = 'none';

            if (response.ok) {
                // SUCCESS STATE
                form.classList.add('success');

                btnText.innerHTML = `
                    <svg class="success-checkmark" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                    </svg>
                    ¡Registro Exitoso!
                `;

                submitBtn.style.background = '#10b981';

                // Show success message
                showSuccess(data.message || 'Account created successfully!');

                // Reset form after delay
                setTimeout(() => {
                    signupForm.reset();
                    clearErrorStates();
                    switchToLogin(); // Switch to login panel
                }, 2000);

            } else {
                // SERVER ERROR STATE
                const errorMessage = data.error || 'Registration error. Please try again.';

                // Dramatic shake and persistent loading effect if already registered
                if (errorMessage.toLowerCase().includes('already registered')) {
                    const signupForm = document.getElementById('signupForm');
                    const submitBtn = document.getElementById('signupSubmitBtn');
                    const btnText = document.getElementById('signupBtnText');
                    const inputContainers = signupForm.querySelectorAll('.input-container');

                    // 1. Show the error message first
                    showError(errorMessage);

                    // 2. Override states for dramatic effect
                    signupForm.classList.add('error-shake', 'error-state');
                    submitBtn.classList.add('error');
                    submitBtn.disabled = true; // Stay blocked
                    inputContainers.forEach(container => container.classList.add('error-state'));

                    // Show loading animation on red button
                    btnText.innerHTML = `<span class="loading-spinner"></span> Verification failed...`;

                    // Revert to normal after a delay
                    setTimeout(() => {
                        signupForm.classList.remove('error-shake', 'error-state');
                        submitBtn.classList.remove('error');
                        submitBtn.disabled = false;
                        btnText.textContent = 'Sign Up';
                        inputContainers.forEach(container => container.classList.remove('error-state'));
                    }, 3000);
                } else {
                    showError(errorMessage);
                }
            }

        } catch (error) {
            // CONNECTION ERROR STATE
            form.classList.remove('loading');
            if (progressBar) progressBar.style.display = 'none';
            showError('Connection error. Please check your internet connection and try again.');
            console.error('Registration error:', error);
        }
    });
});

// Password strength checker initialization
function initializePasswordStrengthChecker() {
    const passwordInput = document.getElementById('password');
    if (!passwordInput) return;

    // Create strength indicator if it doesn't exist
    const existingIndicator = passwordInput.closest('.form-group').querySelector('.password-strength');
    if (existingIndicator) return;

    const strengthHTML = `
        <div class="password-strength">
            <div class="indicator">
                <span class="weak"></span>
                <span class="medium"></span>
                <span class="strong"></span>
            </div>
            <div class="text"></div>
        </div>
    `;

    passwordInput.closest('.input-container').insertAdjacentHTML('afterend', strengthHTML);

    // Add event listener for password input
    passwordInput.addEventListener('input', function () {
        const password = this.value;
        const strengthResult = checkPasswordStrength(password);
        updatePasswordStrengthUI(strengthResult, password.length > 0);
    });
}

// Password strength checking function
function checkPasswordStrength(password) {
    let score = 0;
    let feedback = [];

    if (password.length === 0) {
        return { score: 0, feedback: '', strength: '' };
    }

    // Length check
    if (password.length < 8) {
        feedback.push('Minimum 8 characters');
    } else {
        score += 1;
    }

    // Lowercase check
    if (!/[a-z]/.test(password)) {
        feedback.push('Includes lowercase letters');
    } else {
        score += 1;
    }

    // Uppercase check
    if (!/[A-Z]/.test(password)) {
        feedback.push('Includes capital letters');
    } else {
        score += 1;
    }

    // Number check
    if (!/[0-9]/.test(password)) {
        feedback.push('Includes numbers');
    } else {
        score += 1;
    }

    // Special character check
    if (!/[^A-Za-z0-9]/.test(password)) {
        feedback.push('Includes special symbols');
    } else {
        score += 1;
    }

    let strength = '';
    if (score < 2) {
        strength = 'weak';
    } else if (score < 4) {
        strength = 'medium';
    } else {
        strength = 'strong';
    }

    return {
        score: score,
        feedback: feedback.join(', '),
        strength: strength
    };
}

// Update password strength UI
function updatePasswordStrengthUI(strengthResult, show) {
    const strengthContainer = document.querySelector('.password-strength');
    const indicator = strengthContainer.querySelector('.indicator');
    const textElement = strengthContainer.querySelector('.text');
    const spans = indicator.querySelectorAll('span');

    if (!show) {
        strengthContainer.style.display = 'none';
        return;
    }

    strengthContainer.style.display = 'block';
    indicator.style.display = 'flex';
    textElement.style.display = 'block';

    // Reset all spans
    spans.forEach(span => {
        span.classList.remove('active');
    });

    // Remove previous strength classes
    textElement.classList.remove('weak', 'medium', 'strong');

    // Update based on strength
    if (strengthResult.strength === 'weak') {
        spans[0].classList.add('active');
        textElement.textContent = 'Débil';
        textElement.classList.add('weak');
    } else if (strengthResult.strength === 'medium') {
        spans[0].classList.add('active');
        spans[1].classList.add('active');
        textElement.textContent = 'Mediana';
        textElement.classList.add('medium');
    } else if (strengthResult.strength === 'strong') {
        spans.forEach(span => span.classList.add('active'));
        textElement.textContent = 'Fuerte';
        textElement.classList.add('strong');
    }

    // Show feedback if password is weak
    if (strengthResult.score < 2 && strengthResult.feedback) {
        textElement.textContent += ' - ' + strengthResult.feedback;
    }
}


// Fixed toggle password function
function togglePassword(inputId, iconId) {
    const passwordInput = document.getElementById(inputId);
    const eyeIcon = document.getElementById(iconId);

    if (!passwordInput || !eyeIcon) {
        console.error('Password input or eye icon not found:', inputId, iconId);
        return;
    }

    const isPassword = passwordInput.type === 'password' || passwordInput.type === 'password_confirm';

    if (isPassword) {
        passwordInput.type = 'text';
        eyeIcon.innerHTML = '<path d="M11.83 9L15 12.16V12a3 3 0 0 0-3-3h-.17zm-4.3.8l1.55 1.55c-.05.21-.08.42-.08.65a3 3 0 0 0 3 3c.22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53a5 5 0 0 1-5-5c0-.79.2-1.53.53-2.2zm-.84-.84L8.46 7.3A9.05 9.05 0 0 0 6 12c0 5 4 10 6 10a9.11 9.11 0 0 0 3.3-.62l1.79 1.79 1.42-1.42L3.42 6.42 2 7.84zm6.47 6.47L10.5 12.6A1 1 0 0 1 12 11c0-.22-.06-.44-.16-.64l-1.86-1.86A3 3 0 0 1 12 8a3 3 0 0 1 3 3l2.4 2.4A9.05 9.05 0 0 0 18 12c0-5-4-10-6-10-.85 0-1.69.18-2.47.5L10.38 3.9a1 1 0 0 1 1.24 0L13.16 5.4z"/>';
    } else {
        passwordInput.type = inputId === 'password_confirm' ? 'password' : 'password';
        eyeIcon.innerHTML = '<path d="M15 12c0 1.654-1.346 3-3 3s-3-1.346-3-3 1.346-3 3-3 3 1.346 3 3zm9-.449s-4.252 8.449-11.985 8.449c-7.18 0-12.015-8.449-12.015-8.449s4.446-7.551 12.015-7.551c7.694 0 11.985 7.551 11.985 7.551zm-7 .449c0-2.757-2.243-5-5-5s-5 2.243-5 5 2.243 5 5 5 5-2.243 5-5z"/>';
    }
}

// Email validation function
function isValidEmail(email) {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
}

// Error and success handling functions
function showError(message) {
    const form = document.getElementById('signupForm');
    const submitBtn = document.getElementById('signupSubmitBtn');
    const btnText = document.getElementById('signupBtnText');
    const formHeader = form.querySelector('.form-header');

    // Add error state to form
    form.classList.add('error-state');

    // Remove existing messages
    const existingError = form.querySelector('.error-message');
    if (existingError) existingError.remove();

    // Create error message
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
    btnText.textContent = 'Sign Up';

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

function showSuccess(message) {
    const formHeader = document.querySelector('.form-header');

    // Remove existing messages
    const existingSuccess = document.querySelector('.success-message');
    if (existingSuccess) existingSuccess.remove();

    // Create success message
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
        </svg>
        ${message}
    `;

    formHeader.appendChild(successDiv);

    // Auto-clear success message after 3 seconds
    setTimeout(() => {
        const successMsg = document.querySelector('.success-message');
        if (successMsg) {
            successMsg.classList.add('success-message-hide');
            setTimeout(() => successMsg.remove(), 300);
        }
    }, 3000);
}

function showPasswordMismatchError() {
    const form = document.querySelector('.form');
    const submitBtn = document.getElementById('signupSubmitBtn');

    form.classList.add('error-state');

    // Highlight password fields
    const passwordContainer = document.getElementById('password').closest('.input-container');
    const confirmPasswordContainer = document.getElementById('password_confirm').closest('.input-container');

    passwordContainer.classList.add('error-state');
    confirmPasswordContainer.classList.add('error-state');

    // Shake button
    submitBtn.classList.add('error-shake');

    // Show mismatch message
    showError('Passwords do not match');

    // Clear shake animation
    setTimeout(() => {
        submitBtn.classList.remove('error-shake');
    }, 500);
}

function showValidationErrors(name, lastname, email, password, confirmPassword) {
    const submitBtn = document.getElementById('signupSubmitBtn');
    const form = document.querySelector('.form');

    form.classList.add('error-state');

    // Highlight empty fields
    const fieldsToCheck = [
        { value: name, id: 'name', label: 'name' },
        { value: lastname, id: 'lastname', label: 'last name' },
        { value: email, id: 'signup_email', label: 'email' },
        { value: password, id: 'password', label: 'password' },
        { value: confirmPassword, id: 'password_confirm', label: 'password confirmation' }
    ];

    let firstEmptyField = null;

    fieldsToCheck.forEach(field => {
        if (!field.value) {
            const container = document.getElementById(field.id).closest('.input-container');
            container.classList.add('error-state');
            if (!firstEmptyField) firstEmptyField = field;
        }
    });

    // Shake whole form
    form.classList.add('error-shake');

    // Show validation message
    const message = firstEmptyField
        ? `Please enter your ${firstEmptyField.label}`
        : 'Please complete all fields.';

    showError(message);

    // Clear shake animation
    setTimeout(() => {
        form.classList.remove('error-shake');
    }, 500);
}

function clearErrorStates() {
    const form = document.querySelector('.form');
    const submitBtn = document.getElementById('signupSubmitBtn');
    const btnText = document.getElementById('signupBtnText');
    const errorMessage = document.querySelector('.error-message');
    const successMessage = document.querySelector('.success-message');
    const errorContainers = document.querySelectorAll('.input-container.error-state');

    // Remove form error and success states
    form.classList.remove('error-state', 'success');

    // Clear button error state
    submitBtn.classList.remove('error', 'error-shake');
    submitBtn.style.background = '#1a1a1a';
    submitBtn.disabled = false;

    // Reset button text
    btnText.textContent = 'Sign Up';

    // Remove error message with animation
    if (errorMessage) {
        errorMessage.classList.add('error-message-hide');
        setTimeout(() => errorMessage.remove(), 300);
    }

    // Remove success message with animation
    if (successMessage) {
        successMessage.classList.add('success-message-hide');
        setTimeout(() => successMessage.remove(), 300);
    }

    // Clear input error states
    errorContainers.forEach(container => {
        container.classList.remove('error-state');
    });
}