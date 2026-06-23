// Mobile sidebar toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('open');
}

// Smooth counter animation
function animateCounters() {
    const counters = document.querySelectorAll('.stat-value');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent.replace(/,/g, ''));
        const increment = target / 100;
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.textContent = target.toLocaleString();
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current).toLocaleString();
            }
        }, 20);
    });
}

// Initialize animations on load
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(animateCounters, 500);
});

// Add click handlers for navigation
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(navItem => {
            navItem.classList.remove('active');
        });

        item.classList.add('active');
    });
});


// Simulate real-time updates
setInterval(() => {
    const activities = document.querySelectorAll('.activity-time');
    activities.forEach(time => {
        const currentText = time.textContent;
        if (currentText.includes('minutos')) {
            const minutes = parseInt(currentText.match(/\d+/)[0]);
            time.textContent = `Hace ${minutes + 1} minutos`;
        }
    });
}, 60000); // Update every minute

// Elementos del DOM
const sidebar = document.getElementById('sidebar');
const toggleBtn = document.getElementById('toggleBtn');
const mainContent = document.getElementById('mainContent');
const sectionHeaders = document.querySelectorAll('.nav-section-header');

// Toggle sidebar minimizado
toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('minimized');
    mainContent.classList.toggle('expanded');
    
    // Cambiar icono del botón
    const icon = toggleBtn.querySelector('i');
    if (sidebar.classList.contains('minimized')) {
        icon.className = 'bi bi-arrow-right';
    } else {
        icon.className = 'bi bi-list';
    }
});

// Acordeón de secciones
sectionHeaders.forEach(header => {
    header.addEventListener('click', (e) => {
        const section = header.parentElement;
        const isExpanded = section.classList.contains('expanded');
        
        // Si se hizo clic en el icono mini (sidebar minimizado)
        if (e.target.classList.contains('section-mini-icon')) {
            if (sidebar.classList.contains('minimized')) {
                // Expandir el sidebar temporalmente para mostrar la sección
                sidebar.classList.remove('minimized');
                mainContent.classList.remove('expanded');
                
                // Cambiar icono del botón toggle
                const toggleIcon = toggleBtn.querySelector('i');
                toggleIcon.className = 'bi bi-list';
                
                // Cerrar todas las secciones y abrir la clickeada
                document.querySelectorAll('.nav-section').forEach(s => {
                    s.classList.remove('expanded');
                });
                section.classList.add('expanded');
                
                return;
            }
        }
        
        // Si el sidebar está minimizado y no se hizo clic en el mini icono, no hacer nada
        if (sidebar.classList.contains('minimized')) {
            return;
        }
        
        // Si la sección ya está expandida, solo la contraemos
        if (isExpanded) {
            section.classList.remove('expanded');
        } else {
            // Cerrar todas las otras secciones
            document.querySelectorAll('.nav-section').forEach(s => {
                if (s !== section) {
                    s.classList.remove('expanded');
                }
            });
            // Abrir la sección actual
            section.classList.add('expanded');
        }
    });
});

// Cerrar secciones cuando se minimiza el sidebar
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
            if (sidebar.classList.contains('minimized')) {
                // Cerrar todas las secciones cuando se minimiza
                document.querySelectorAll('.nav-section').forEach(section => {
                    section.classList.remove('expanded');
                });
            } else {
                // Abrir la primera sección cuando se expande
                document.querySelector('.nav-section').classList.add('expanded');
            }
        }
    });
});

observer.observe(sidebar, { attributes: true });

// Manejo de enlaces activos
const navItems = document.querySelectorAll('.nav-item');
navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        // Remover clase active de todos los elementos
        navItems.forEach(nav => nav.classList.remove('active'));
        // Añadir clase active al elemento clickeado
        item.classList.add('active');
    });
});

// Responsive: cerrar sidebar en móvil al hacer clic fuera
document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768) {
        if (!sidebar.contains(e.target) && sidebar.classList.contains('mobile-open')) {
            sidebar.classList.remove('mobile-open');
        }
    }
});