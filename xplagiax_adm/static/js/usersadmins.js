// Global variables
let currentPage = 1;
let totalPages = 1;
let totalUsers = 0;
let sortField = 'created_at';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints
const API_BASE = '/usersadmin_bp/api/users_admin';
const ENDPOINTS = {
    list: `${API_BASE}`,
    create: `${API_BASE}`,
    update: (id) => `${API_BASE}/${id}`,
    delete: (id) => `${API_BASE}/${id}`,
    export: `${API_BASE}/export`,
    stats: `${API_BASE}/stats`,
    sessions: (userId) => `${API_BASE}/${userId}/sessions`,
    resetPassword: (userId) => `${API_BASE}/${userId}/reset_password`
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadUsers();
    loadStats();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    let searchTimeout;
    document.getElementById('searchInput').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            applyFilters();
        }, 500);
    });

    ['roleFilter', 'statusFilter', 'sortFilter'].forEach(id => {
        document.getElementById(id).addEventListener('change', applyFilters);
    });
}

// Load users from API
async function loadUsers(page = 1) {
    try {
        showLoading(true);
        
        const params = new URLSearchParams({
            page: page,
            per_page: 10,
            sort_field: sortField,
            sort_direction: sortDirection,
            ...currentFilters
        });

        const response = await fetch(`${ENDPOINTS.list}?${params}`);
        if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
        
        const data = await response.json();
        displayUsers(data.users || []);
        updatePagination(data.pagination || {});
        updateTableStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading users:', error);
        showError('Error al cargar usuarios: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(ENDPOINTS.stats);
        if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
        
        const stats = await response.json();
        document.getElementById('totalUsers').textContent = stats.total || 0;
        document.getElementById('activeUsers').textContent = stats.active || 0;
        document.getElementById('adminUsers').textContent = stats.admins || 0;
        document.getElementById('monthlyUsers').textContent = stats.monthly || 0;
        
    } catch (error) {
        console.error('Error loading stats:', error);
        showError('Error al cargar estadísticas: ' + error.message);
    }
}

// Display users in table
function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    
    if (users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron usuarios
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = users.map(user => `
        <tr>
            <td>
                <div style="font-weight: 500; color: #212529;">
                    <i class="fas fa-user-circle" style="margin-right: 8px; color: #94a3b8;"></i>
                    ${user.username || 'Sin nombre'}
                </div>
            </td>
            <td>${user.email || '-'}</td>
            <td>
                <span class="role-badge role-${user.role}">
                    ${getRoleName(user.role)}
                </span>
            </td>
            <td>${formatDate(user.created_at)}</td>
            <td>${user.last_login_at ? formatDate(user.last_login_at) : '-'}</td>
            <td>
                <span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">
                    ${user.is_active ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td>
                <div class="actions-row">
                    <!-- Botón de edición directo -->
                 
                    <!-- Menú desplegable para otras acciones -->
                    <div class="actions-menu">
                        <button class="actions-btn" onclick="toggleActionDropdown(${user.id})" title="Más acciones">
                              <i class="bi bi-grid"></i> Opciones
                        </button>
                        <div class="actions-dropdown" id="dropdown-${user.id}">
                            <a href="#" class="dropdown-item" onclick="viewSessions(${user.id})">
                                <i class="bi bi-terminal" style="margin-right: 8px;"></i> Ver Sesiones
                            </a>
                            <a href="#" class="dropdown-item" onclick="openResetPasswordModal(${user.id})">
                                <i class="bi bi-key" style="margin-right: 8px;"></i> Resetear Contraseña
                            </a>
                            <a href="#" class="dropdown-item danger" onclick="deleteUser(${user.id})">
                                <i class="bi bi-trash" style="margin-right: 8px;"></i> Eliminar
                            </a>
                        </div>
                    </div>
                </div>
            </td>
        </tr>
    `).join('');
}

// Helper functions
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getRoleName(role) {
    const roles = {
        'admin': 'Administrador',
        'user': 'Usuario',
        'manager': 'Manager'
    };
    return roles[role] || role;
}

// Pagination functions
function updatePagination(pagination) {
    totalPages = pagination.pages || 1;
    totalUsers = pagination.total || 0;
    
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i> Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => loadUsers(currentPage - 1);
    controls.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => loadUsers(1);
        controls.appendChild(firstBtn);

        if (startPage > 2) {
            const dotsSpan = document.createElement('span');
            dotsSpan.textContent = '...';
            dotsSpan.style.padding = '6px 12px';
            dotsSpan.style.display = 'flex';
            dotsSpan.style.alignItems = 'center';
            controls.appendChild(dotsSpan);
        }
    }

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `pagination-btn ${i === currentPage ? 'active' : ''}`;
        pageBtn.textContent = i;
        pageBtn.onclick = () => loadUsers(i);
        controls.appendChild(pageBtn);
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const dotsSpan = document.createElement('span');
            dotsSpan.textContent = '...';
            dotsSpan.style.padding = '6px 12px';
            dotsSpan.style.display = 'flex';
            dotsSpan.style.alignItems = 'center';
            controls.appendChild(dotsSpan);
        }

        const lastBtn = document.createElement('button');
        lastBtn.className = 'pagination-btn';
        lastBtn.textContent = totalPages;
        lastBtn.onclick = () => loadUsers(totalPages);
        controls.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.innerHTML = 'Siguiente <i class="fas fa-chevron-right"></i>';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadUsers(currentPage + 1);
    controls.appendChild(nextBtn);
}

function updateTableStats(pagination) {
    const stats = document.getElementById('tableStats');
    const info = document.getElementById('paginationInfo');
    
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 10) + 1;
    const end = Math.min(start + (pagination.per_page || 10) - 1, pagination.total || 0);
    
    stats.textContent = `${pagination.total || 0} usuarios encontrados`;
    info.textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0} usuarios`;
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const role = document.getElementById('roleFilter').value;
    const status = document.getElementById('statusFilter').value;
    const sort = document.getElementById('sortFilter').value;

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (role) currentFilters.role = role;
    if (status) currentFilters.is_active = status;
    if (sort) sortField = sort;

    currentPage = 1;
    loadUsers(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('roleFilter').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('sortFilter').value = 'created_at';
    
    currentFilters = {};
    sortField = 'created_at';
    sortDirection = 'desc';
    currentPage = 1;
    loadUsers(1);
}

// Sort functions
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    loadUsers(currentPage);
}

// Modal functions
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Nuevo Usuario';
    document.getElementById('userForm').reset();
    document.getElementById('userId').value = '';
    document.getElementById('passwordNote').style.display = 'none';
    document.getElementById('activeStatus').checked = true;
    document.getElementById('userModal').classList.add('show');
}

function closeModal() {
    document.getElementById('userModal').classList.remove('show');
}

// CRUD operations
async function saveUser() {
    try {
        const formData = {
            username: document.getElementById('username').value.trim(),
            email: document.getElementById('email').value.trim(),
            role: document.getElementById('role').value,
            is_active: document.querySelector('input[name="status"]:checked').value === 'true',
            password: document.getElementById('password').value || null
        };

        const userId = document.getElementById('userId').value;
        const isEdit = !!userId;

        // Validate password on create
        if (!isEdit && !formData.password) {
            showError('La contraseña es requerida para nuevos usuarios');
            return;
        }

        // Validate password match
        if (formData.password && formData.password !== document.getElementById('confirmPassword').value) {
            showError('Las contraseñas no coinciden');
            return;
        }

        // Prepare request
        const url = isEdit ? ENDPOINTS.update(userId) : ENDPOINTS.create;
        const method = isEdit ? 'PUT' : 'POST';
        
        // Remove password if empty on edit
        if (isEdit && !formData.password) {
            delete formData.password;
        }

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Error ${response.status}`);
        }

        closeModal();
        loadUsers(currentPage);
        loadStats();
        showSuccess(isEdit ? 'Usuario actualizado correctamente' : 'Usuario creado correctamente');

    } catch (error) {
        console.error('Error saving user:', error);
        showError('Error al guardar usuario: ' + error.message);
    }
}

async function editUser(userId) {
    try {
        const response = await fetch(ENDPOINTS.update(userId));
        if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
        
        const user = await response.json();
        
        document.getElementById('modalTitle').textContent = 'Editar Usuario';
        document.getElementById('userId').value = user.id;
        document.getElementById('username').value = user.username || '';
        document.getElementById('email').value = user.email || '';
        document.getElementById('role').value = user.role || '';
        document.getElementById('passwordNote').style.display = 'inline';
        
        if (user.is_active) {
            document.getElementById('activeStatus').checked = true;
        } else {
            document.getElementById('inactiveStatus').checked = true;
        }
        
        document.getElementById('userModal').classList.add('show');
        
    } catch (error) {
        console.error('Error loading user:', error);
        showError('Error al cargar datos del usuario: ' + error.message);
    }
}

async function deleteUser(userId) {
    if (!confirm('¿Estás seguro de que quieres eliminar este usuario? Esta acción no se puede deshacer.')) {
        return;
    }

    try {
        const response = await fetch(ENDPOINTS.delete(userId), { method: 'DELETE' });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Error ${response.status}`);
        }

        loadUsers(currentPage);
        loadStats();
        showSuccess('Usuario eliminado correctamente');

    } catch (error) {
        console.error('Error deleting user:', error);
        showError('Error al eliminar usuario: ' + error.message);
    }
}

// Función para abrir offcanvas de sesiones
async function viewSessions(userId) {
    try {
        // Cerrar menú desplegable
        const dropdown = document.getElementById(`dropdown-${userId}`);
        if (dropdown) dropdown.classList.remove('show');
        
        // Mostrar carga
        document.getElementById('sessionsLoading').style.display = 'flex';
        document.getElementById('sessionsTable').style.display = 'none';
        
        // Abrir offcanvas usando Bootstrap
        const offcanvasElement = document.getElementById('sessionsOffcanvas');
        const offcanvas = bootstrap.Offcanvas.getOrCreateInstance(offcanvasElement);
        offcanvas.show();
        
        // Cargar sesiones
        const response = await fetch(ENDPOINTS.sessions(userId));
        if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
        
        const sessions = await response.json();
        
        // Mostrar sesiones
        const tbody = document.getElementById('sessionsTableBody');
        if (!sessions || sessions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay sesiones registradas</td></tr>';
        } else {
            tbody.innerHTML = sessions.map(session => `
                <tr>
                    <td>${session.name || '-'}</td>
                    <td>${session.hostname || '-'}</td>
                    <td>${session.username || '-'}</td>
                    <td>${session.last_used_at ? formatDate(session.last_used_at) : 'Nunca'}</td>
                    <td>
                        <span class="status-badge ${session.is_active ? 'status-active' : 'status-inactive'}">
                            ${session.is_active ? 'Activa' : 'Inactiva'}
                        </span>
                    </td>
                </tr>
            `).join('');
        }
        
        // Ocultar carga y mostrar tabla
        document.getElementById('sessionsLoading').style.display = 'none';
        document.getElementById('sessionsTable').style.display = 'table';
        
    } catch (error) {
        console.error('Error loading sessions:', error);
        showError('Error al cargar sesiones: ' + error.message);
    }
}

// Funciones para resetear contraseña
function openResetPasswordModal(userId) {
    document.getElementById('resetUserId').value = userId;
    document.getElementById('resetPasswordModal').classList.add('show');
}

function closeResetPasswordModal() {
    document.getElementById('resetPasswordModal').classList.remove('show');
    document.getElementById('resetPasswordForm').reset();
}

async function submitResetPassword() {
    try {
        const userId = document.getElementById('resetUserId').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmNewPassword').value;
        
        if (!newPassword) {
            showError('La nueva contraseña es requerida');
            return;
        }
        
        if (newPassword !== confirmPassword) {
            showError('Las contraseñas no coinciden');
            return;
        }
        
        // Corrección: quitar la coma después de la URL
        const response = await fetch(ENDPOINTS.resetPassword(userId), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password: newPassword })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Error ${response.status}`);
        }
        
        closeResetPasswordModal();
        showSuccess('Contraseña actualizada correctamente');
        
    } catch (error) {
        console.error('Error resetting password:', error);
        showError('Error al resetear contraseña: ' + error.message);
    }
}

// Export function
async function exportUsers() {
    try {
        const response = await fetch(ENDPOINTS.export);
        if (!response.ok) throw new Error(`Error ${response.status}: ${response.statusText}`);
        
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `usuarios_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        
        URL.revokeObjectURL(url);
        showSuccess('Usuarios exportados correctamente');

    } catch (error) {
        console.error('Error exporting users:', error);
        showError('Error al exportar usuarios: ' + error.message);
    }
}

// Action dropdown functions
function toggleActionDropdown(userId) {
    const dropdown = document.getElementById(`dropdown-${userId}`);
    const allDropdowns = document.querySelectorAll('.actions-dropdown');
    
    allDropdowns.forEach(d => {
        if (d !== dropdown) d.classList.remove('show');
    });
    
    dropdown.classList.toggle('show');
}

// Utility functions
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('usersTable');
    
    if (show) {
        loading.style.display = 'flex';
        table.style.display = 'none';
    } else {
        loading.style.display = 'none';
        table.style.display = 'table';
    }
}

function showSuccess(message) {
    Swal.fire({
        icon: 'success',
        title: 'Éxito',
        text: message,
        timer: 2500,
        showConfirmButton: false,
        toast: true,
        position: 'top-end'
    });
}

function showError(message) {
    Swal.fire({
        icon: 'error',
        title: 'Error',
        text: message,
        timer: 3000,
        showConfirmButton: false,
        toast: true,
        position: 'top-end'
    });
}

function showInfo(message) {
    Swal.fire({
        icon: 'info',
        title: 'Información',
        text: message,
        timer: 3000,
        showConfirmButton: false,
        toast: true,
        position: 'top-end'
    });
}