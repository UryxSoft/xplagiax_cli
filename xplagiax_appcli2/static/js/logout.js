// Función para abrir el modal de logout
function abrirModalLogout() {
    const logoutModal = document.getElementById('logoutModal');
    logoutModal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Prevenir scroll
}

// Función para cerrar el modal de logout
function cerrarLogoutModal() {
    const logoutModal = document.getElementById('logoutModal');
    logoutModal.classList.remove('active');
    document.body.style.overflow = 'auto'; // Restaurar scroll
}

// Función para confirmar logout
function confirmarLogout() {
    const logoutConfirmBtn = document.getElementById('logoutConfirmBtn');
    const logoutBtnText = document.getElementById('logoutBtnText');
    const logoutBtnSpinner = document.getElementById('logoutBtnSpinner');

    // Mostrar estado de carga
    logoutConfirmBtn.classList.add('logout-btn-loading');
    logoutConfirmBtn.disabled = true;
    logoutBtnText.textContent = 'Cerrando...';
    logoutBtnSpinner.style.display = 'block';

    // Simular un pequeño delay para mejor UX
    setTimeout(() => {
        // Aquí iría tu URL de Flask
        window.location.href = "/login"; // Cambia por: "{{ url_for('x_auth.logout') }}"
    }, 800);
}

// Cerrar modal de logout al hacer clic fuera de él
//document.getElementById('logoutModal').addEventListener('click', function(e) {
//    if (e.target === this) {
//        cerrarLogoutModal();
//    }
//});

// Cerrar modal de logout con la tecla Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        cerrarLogoutModal();
    }
});
