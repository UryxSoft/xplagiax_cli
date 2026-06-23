// Crear formas geométricas animadas
function createGeometricShapes() {
    const container = document.getElementById('geometricBg');
    const shapeCount = 15;

    for (let i = 0; i < shapeCount; i++) {
        const shape = document.createElement('div');
        shape.className = 'geometric-shape';
        
        // Tamaño aleatorio
        const size = Math.random() * 60 + 20;
        shape.style.width = size + 'px';
        shape.style.height = size + 'px';
        
        // Posición aleatoria
        shape.style.left = Math.random() * 100 + '%';
        shape.style.top = Math.random() * 100 + '%';
        
        // Duración de animación aleatoria
        shape.style.animationDuration = (Math.random() * 4 + 4) + 's';
        shape.style.animationDelay = Math.random() * 2 + 's';
        
        container.appendChild(shape);
    }
}

// Función para mostrar mensajes
function showMessage(text, type = 'info') {
    const messageElement = document.getElementById('message');
    messageElement.textContent = text;
    messageElement.className = `message ${type}`;
    messageElement.style.display = 'block';
    
    // Auto-ocultar después de 5 segundos
    setTimeout(() => {
        messageElement.style.display = 'none';
    }, 5000);
}

// Función para mostrar loading
function setLoading(isLoading) {
    const button = document.getElementById('loginButton');
    const spinner = document.getElementById('buttonSpinner');
    const buttonText = document.getElementById('buttonText');
    
    if (isLoading) {
        button.disabled = true;
        spinner.style.display = 'inline-block';
        buttonText.textContent = 'Verificando credenciales...';
    } else {
        button.disabled = false;
        spinner.style.display = 'none';
        buttonText.textContent = 'Iniciar Sesión';
    }
}

// Función para validar email
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Función para validar contraseña
function validatePassword(password) {
    return password.length >= 6;
}

// Función para hacer shake al contenedor
function shakeContainer() {
    const wrapper = document.querySelector('.login-wrapper');
    wrapper.classList.add('shake');
    setTimeout(() => {
        wrapper.classList.remove('shake');
    }, 600);
}

// Manejar envío del formulario
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const remember = document.getElementById('remember').checked;
    
    // Validaciones del lado del cliente
    if (!email || !password) {
        showMessage('Por favor completa todos los campos obligatorios', 'error');
        shakeContainer();
        return;
    }
    
    if (!validateEmail(email)) {
        showMessage('Por favor ingresa un correo electrónico válido', 'error');
        shakeContainer();
        return;
    }
    
    if (!validatePassword(password)) {
        showMessage('La contraseña debe tener al menos 6 caracteres', 'error');
        shakeContainer();
        return;
    }
    
    // Mostrar loading
    setLoading(true);
    
    try {
        // Enviar datos al servidor
        const response = await fetch('/auth_bp/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password,
                remember: remember
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage('¡Autenticación exitosa! Redirigiendo al panel...', 'success');
            
            // Esperar un poco antes de redirigir
            setTimeout(() => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    window.location.href = '/documents';
                }
            }, 1500);
        } else {
            showMessage(data.message || 'Credenciales incorrectas. Verifica tus datos.', 'error');
            shakeContainer();
        }
        
    } catch (error) {
        console.error('Error:', error);
        showMessage('Error de conexión. Verifica tu conexión a internet.', 'error');
        shakeContainer();
    } finally {
        setLoading(false);
    }
});

// Efectos de focus en los inputs
document.querySelectorAll('.form-group input').forEach(input => {
    input.addEventListener('focus', function() {
        this.parentElement.style.transform = 'translateY(-2px)';
    });
    
    input.addEventListener('blur', function() {
        this.parentElement.style.transform = 'translateY(0)';
    });
});

// Verificar si hay sesión activa al cargar la página
async function checkSession() {
    try {
        const response = await fetch('/auth_bp/check-session');
        const data = await response.json();
        
        if (data.authenticated) {
            showMessage('Ya tienes una sesión activa. Redirigiendo...', 'info');
            setTimeout(() => {
                window.location.href = '/documents';
            }, 2000);
        }
    } catch (error) {
        console.log('No hay sesión activa');
    }
}

// Inicializar página
document.addEventListener('DOMContentLoaded', function() {
    createGeometricShapes();
    checkSession();
    
    // Aplicar efectos de entrada
    document.querySelector('.login-wrapper').classList.add('fade-in');
    document.querySelector('.brand-logo').classList.add('pulse');
});

// Manejar errores de red
window.addEventListener('online', function() {
    showMessage('Conexión a internet restaurada', 'success');
});

window.addEventListener('offline', function() {
    showMessage('Sin conexión a internet. Verifica tu conexión.', 'error');
});

// Efectos adicionales en hover
document.querySelectorAll('.form-group input').forEach(input => {
    input.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-1px)';
    });
    
    input.addEventListener('mouseleave', function() {
        if (this !== document.activeElement) {
            this.style.transform = 'translateY(0)';
        }
    });
});

// Añadir efectos de ripple al botón
document.getElementById('loginButton').addEventListener('click', function(e) {
    const button = this;
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.style.position = 'absolute';
    ripple.style.borderRadius = '50%';
    ripple.style.backgroundColor = 'rgba(255, 255, 255, 0.3)';
    ripple.style.transform = 'scale(0)';
    ripple.style.animation = 'ripple 0.6s linear';
    ripple.style.pointerEvents = 'none';
    
    button.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
});

// Añadir animación de ripple
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
