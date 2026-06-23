// settings.js — safe bindings, all DOM references guarded

// Add smooth scrolling and form validation
document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Card animations on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    document.querySelectorAll('.fade-in-delayed').forEach(el => {
        observer.observe(el);
    });
});

// Flash message helper — only works if elements exist
function showFlashMessage(message, type = 'info') {
    const alertDiv = document.querySelector('.alert');
    const messageSpan = document.getElementById('flash-message-text');
    if (!alertDiv || !messageSpan) return;
    messageSpan.textContent = message;
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.style.display = 'block';
    setTimeout(() => { alertDiv.style.display = 'none'; }, 5000);
}

// Credit card number formatting — only bind if element exists
const ccNumber = document.getElementById('cc-number');
if (ccNumber) {
    ccNumber.addEventListener('input', function(e) {
        let value = e.target.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
        let formattedValue = value.match(/.{1,4}/g)?.join(' ') || value;
        if (formattedValue.length > 19) formattedValue = formattedValue.substring(0, 19);
        e.target.value = formattedValue;
    });
}

// Expiration date formatting — only bind if element exists
const ccExp = document.getElementById('cc-expiration');
if (ccExp) {
    ccExp.addEventListener('input', function(e) {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length >= 2) {
            value = value.substring(0, 2) + '/' + value.substring(2, 4);
        }
        e.target.value = value;
    });
}

// CVV formatting — only bind if element exists
const ccCvv = document.getElementById('cc-cvv');
if (ccCvv) {
    ccCvv.addEventListener('input', function(e) {
        e.target.value = e.target.value.replace(/\D/g, '').substring(0, 4);
    });
}