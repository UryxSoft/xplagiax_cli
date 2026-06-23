// Global variables
let currentPage = 1;
let totalPages = 1;
let totalUsers = 0;
let sortField = 'created_date';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints - adjust these to match your Flask routes
const API_BASE = '/users_bp/api/users';
const ENDPOINTS = {
    list: `${API_BASE}`,
    create: `${API_BASE}`,
    update: (id) => `${API_BASE}/${id}`,
    delete: (id) => `${API_BASE}/${id}`,
    export: `${API_BASE}/export`,
    institutions: '/users_bp/api/institutions',
    countries: '/users_bp/api/countries'
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadUsers();
    setupEventListeners();
    loadCountries();
    loadInstitutions();
});

// Setup event listeners
function setupEventListeners() {
    // Search input with debounce
    let searchTimeout;
    document.getElementById('searchInput').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            applyFilters();
        }, 500);
    });

    // Filter selects
    ['statusFilter', 'typeFilter', 'professorFilter'].forEach(id => {
        document.getElementById(id).addEventListener('change', applyFilters);
    });

    // Close modal on outside click
    document.getElementById('userModal').addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });

    // Close dropdowns on outside click
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.actions-menu')) {
            document.querySelectorAll('.actions-dropdown.show').forEach(dropdown => {
                dropdown.classList.remove('show');
            });
        }
    });
}

// Load users from API
async function loadUsers(page = 1) {
    try {
        showLoading(true);
        
        const params = new URLSearchParams({
            page: page,
            per_page: 5,
            sort_field: sortField,
            sort_direction: sortDirection,
            ...currentFilters
        });

        const response = await fetch(`${ENDPOINTS.list}?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        displayUsers(data.users || []);
        updatePagination(data.pagination || {});
        updateStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading users:', error);
        showError('Error al cargar usuarios: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Display users in table
function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    
    if (users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron usuarios
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = users.map(user => `
        <tr>
            <td>
                <div class="user-info">
                    <div class="user-avatar">
                        ${getInitials(user.name, user.lastname)}
                    </div>
                    <div class="user-details">
                        <div class="user-name">${user.name || ''} ${user.lastname || ''}</div>
                        <div class="user-email">${user.email || ''}</div>
                    </div>
                </div>
            </td>
            <td>${user.email || ''}</td>
            <td>${user.user_type || 'Starter'}</td>
            <td>${user.is_professor ? 'Sí' : 'No'}</td>
            <td>${user.institute || '-'}</td>
            <td>${user.country || '-'}</td>
            <td>${formatDate(user.created_date)}</td>
            <td>
                <span class="status-badge ${getStatusClass(user)}">
                    ${getStatusText(user)}
                </span>
            </td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActionDropdown(${user.id})">
                         <i class="bi bi-grid"></i> Opciones
                    </button>
                    <div class="actions-dropdown" id="dropdown-${user.id}">
                        <a href="#" class="dropdown-item" onclick="editUser(${user.id})">Editar</a>
                        <a href="#" class="dropdown-item" onclick="toggleUserStatus(${user.id}, ${user.is_active})">
                            ${user.is_active ? 'Desactivar' : 'Activar'}
                        </a>
                        <a href="#" class="dropdown-item" onclick="viewUserDetails(${user.id})">Ver Detalles</a>
                        <a href="#" class="dropdown-item danger" onclick="deleteUser(${user.id})">Eliminar</a>
                    </div>
                </div>
            </td>
        </tr>
    `).join('');
}

// Helper functions
function getInitials(name, lastname) {
    const n = (name || '').charAt(0).toUpperCase();
    const l = (lastname || '').charAt(0).toUpperCase();
    return n + l || 'U';
}

function getStatusClass(user) {
    if (!user.is_active) return 'status-inactive';
    if (!user.confirmado) return 'status-pending';
    return 'status-active';
}

function getStatusText(user) {
    if (!user.is_active) return 'Inactivo';
    if (!user.confirmado) return 'Pendiente';
    return 'Activo';
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Pagination functions
function updatePagination(pagination) {
    totalPages = pagination.pages || 1;
    totalUsers = pagination.total || 0;
    
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => loadUsers(currentPage - 1);
    controls.appendChild(prevBtn);

    // Page numbers
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
            controls.appendChild(dotsSpan);
        }

        const lastBtn = document.createElement('button');
        lastBtn.className = 'pagination-btn';
        lastBtn.textContent = totalPages;
        lastBtn.onclick = () => loadUsers(totalPages);
        controls.appendChild(lastBtn);
    }

    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Siguiente →';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadUsers(currentPage + 1);
    controls.appendChild(nextBtn);
}

function updateStats(pagination) {
    const stats = document.getElementById('tableStats');
    const info = document.getElementById('paginationInfo');
    
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 20) + 1;
    const end = Math.min(start + (pagination.per_page || 20) - 1, pagination.total || 0);
    
    stats.textContent = `${pagination.total || 0} usuarios encontrados`;
    info.textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0} usuarios`;
}

// Función para cargar países
async function loadCountries() {
    try {
        const response = await fetch(ENDPOINTS.countries);
        const countries = await response.json();
        
        const select = document.getElementById('countryFilter');
        countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.country; // o country.id según tu necesidad
            option.textContent = country.country;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading countries:', error);
    }
}

// Función para cargar instituciones
async function loadInstitutions() {
    try {
        const response = await fetch(ENDPOINTS.institutions);
        const institutions = await response.json();
        
        const select = document.getElementById('institutionFilter');
        institutions.forEach(institution => {
            const option = document.createElement('option');
            option.value = institution.institution; // o institution.id
            option.textContent = institution.institution;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading institutions:', error);
    }
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const status = document.getElementById('statusFilter').value;
    const type = document.getElementById('typeFilter').value;
    const professor = document.getElementById('professorFilter').value;
    const country = document.getElementById('countryFilter').value;
    const institution = document.getElementById('institutionFilter').value; // Nuevo

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (status) currentFilters.status = status;
    if (type) currentFilters.user_type = type;
    if (country) currentFilters.country = country;
    if (institution) currentFilters.institution = institution; // Nuevo
    if (professor) currentFilters.is_professor = professor;

    currentPage = 1;
    loadUsers(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('typeFilter').value = '';
    document.getElementById('professorFilter').value = '';
    
    currentFilters = {};
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
    document.getElementById('userModal').classList.add('show');
}

function closeModal() {
    document.getElementById('userModal').classList.remove('show');
}

// CRUD operations
async function saveUser() {
    try {
        const formData = {
            name: document.getElementById('userName').value.trim(),
            lastname: document.getElementById('userLastname').value.trim(),
            email: document.getElementById('userEmail').value.trim(),
            user_type: document.getElementById('userType').value,
            institute: document.getElementById('userInstitute').value.trim(),
            country: document.getElementById('userCountry').value.trim(),
            is_professor: document.getElementById('isProfessor').checked,
            is_active: document.getElementById('isActive').checked,
            confirmado: document.getElementById('isConfirmed').checked
        };

        const password = document.getElementById('userPassword').value.trim();
        if (password) {
            formData._password_hash = password;
        }

        const userId = document.getElementById('userId').value;
        const isEdit = !!userId;

        const url = isEdit ? ENDPOINTS.update(userId) : ENDPOINTS.create;
        const method = isEdit ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al guardar usuario');
        }

        closeModal();
        loadUsers(currentPage);
        showSuccess(isEdit ? 'Usuario actualizado correctamente' : 'Usuario creado correctamente');

    } catch (error) {
        console.error('Error saving user:', error);
        showError('Error al guardar usuario: ' + error.message);
    }
}

async function editUser(userId) {
    try {
        const response = await fetch(ENDPOINTS.update(userId));
        
        if (!response.ok) {
            throw new Error('Error al cargar datos del usuario');
        }
        
        const user = await response.json();
        
        document.getElementById('modalTitle').textContent = 'Editar Usuario';
        document.getElementById('userId').value = user.id;
        document.getElementById('userName').value = user.name || '';
        document.getElementById('userLastname').value = user.lastname || '';
        document.getElementById('userEmail').value = user.email || '';
        document.getElementById('userType').value = user.user_type || 'Starter';
        document.getElementById('userInstitute').value = user.institute || '';
        document.getElementById('userCountry').value = user.country || '';
        document.getElementById('isProfessor').checked = user.is_professor || false;
        document.getElementById('isActive').checked = user.is_active || false;
        document.getElementById('isConfirmed').checked = user.confirmado || false;
        document.getElementById('userPassword').value = '';
        
        document.getElementById('userModal').classList.add('show');
        
    } catch (error) {
        console.error('Error loading user:', error);
        showError('Error al cargar datos del usuario: ' + error.message);
    }
}

async function deleteUser(userId) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer. ¿Deseas eliminar este usuario??',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        reverseButtons: true
    });

    if (!result.isConfirmed) {
        return;
    }


    try {
        const response = await fetch(ENDPOINTS.delete(userId), {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al eliminar usuario');
        }

        loadUsers(currentPage);
        showSuccess('Usuario eliminado correctamente');

    } catch (error) {
        console.error('Error deleting user:', error);
        showError('Error al eliminar usuario: ' + error.message);
    }
}

async function toggleUserStatus(userId, currentStatus) {
    try {
        const response = await fetch(ENDPOINTS.update(userId), {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                is_active: !currentStatus
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al cambiar estado del usuario');
        }

        loadUsers(currentPage);
        showSuccess(`Usuario ${!currentStatus ? 'activado' : 'desactivado'} correctamente`);

    } catch (error) {
        console.error('Error toggling user status:', error);
        showError('Error al cambiar estado del usuario: ' + error.message);
    }
}

function viewUserDetails(userId) {
    // Implement user details view - could open a new modal or navigate to detail page
    console.log('View details for user:', userId);
    showInfo('Función de detalles en desarrollo');
}

// Export function
async function exportUsers() {
    try {
        const response = await fetch(ENDPOINTS.export);
        
        if (!response.ok) {
            throw new Error('Error al exportar usuarios');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `usuarios_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

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
    
    // Close all other dropdowns
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
        loading.style.display = 'block';
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