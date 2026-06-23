document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    const loginBtn = document.getElementById('loginBtn');
    
    // Toggle password visibility
    togglePassword.addEventListener('click', () => {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        
        // Change icon
        togglePassword.innerHTML = type === 'password' ? 
            `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
            </svg>` :
            `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
            </svg>`;
    });
    
    // Handle form submission
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        // Show loading state
        loginBtn.innerHTML = '<div class="spinner"></div> Iniciando sesión...';
        loginBtn.disabled = true;
        
       // try {
            // Replace the fetch block in your JavaScript with:
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch('/auth_bp/login', {
                method: 'POST',
                body: formData  // Send as FormData instead of JSON
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Login successful
                window.location.href = result.redirect || '/dashboard';
            } else {
                // Show error message
                showNotification(result.error || 'Error al iniciar sesión', 'error');
                loginBtn.innerHTML = 'Iniciar sesión';
                loginBtn.disabled = false;
                
                // Shake animation for error
                loginForm.classList.add('shake');
                setTimeout(() => {
                    loginForm.classList.remove('shake');
                }, 500);
            }
     //  } catch (error) {
            console.error('Login error:', error);
            showNotification('Error de conexión', 'error');
            loginBtn.innerHTML = 'Iniciar sesión';
            loginBtn.disabled = false;
        }
    });
    
    // Show notification function
    function showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.querySelector('.login-container').appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    // Handle social login
    document.querySelectorAll('.btn-social').forEach(btn => {
        btn.addEventListener('click', () => {
            const provider = btn.classList.contains('google') ? 'google' : 'github';
            showNotification(`Redirigiendo a ${provider === 'google' ? 'Google' : 'GitHub'}...`, 'info');
            
            // In a real app, this would redirect to OAuth endpoint
            setTimeout(() => {
                showNotification('Integración de inicio de sesión social no implementada', 'error');
            }, 1500);
        });
    });
});