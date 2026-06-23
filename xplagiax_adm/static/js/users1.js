// Global variables
let currentPage = 1;
let totalPages = 1;
let totalUsers = 0;
let sortField = 'created_at';
let sortDirection = 'desc';
let currentFilters = {};
let currentUserId = null;
let globalInstitutions = []; // Para almacenar todas las instituciones
let globalCountries = [];    // Para almacenar todos los países

// API endpoints
const API_BASE = '/users_bp/api/users';
const ENDPOINTS = {
    list: API_BASE,
    create: API_BASE,
    update: (id) => `${API_BASE}/${id}`,
    delete: (id) => `${API_BASE}/${id}`,
    export: `${API_BASE}/export`,
    stats: `${API_BASE}/stats`,
    storagePlans: '/users_bp/api/storage-plans',
    storageAddons: '/users_bp/api/storage-addons',
    institutions: '/users_bp/api/institutions',
    countries: '/users_bp/api/countries',
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadUsers();
    loadStats();
    loadStoragePlans();
    setupEventListeners();
    loadCountries();
    loadInstitutions();

    // Precargar datos para modales
    loadInstitutionsForModal();
    loadCountriesForModal();

    // Cargar datos globales para instituciones y países
    loadGlobalData();
});

// Cargar datos globales para instituciones y países
async function loadGlobalData() {
    try {
        const [institutionsRes, countriesRes] = await Promise.all([
            fetch(ENDPOINTS.institutions),
            fetch(ENDPOINTS.countries)
        ]);
        globalInstitutions = await institutionsRes.json();
        globalCountries = await countriesRes.json();
    } catch (error) {
        console.error('Error loading global data:', error);
    }
}

function setupEventListeners() {
    // Search input with debounce
    let searchTimeout;
    document.getElementById('searchInput').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            applyFilters();
        }, 500);
    });

    // Filter changes
    ['typeFilter', 'countryFilter', 'statusFilter'].forEach(id => {
        document.getElementById(id).addEventListener('change', applyFilters);
    });

    // Modal close
    document.getElementById('userModal').addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });
}

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
        
        if (!response.ok) throw new Error('Error loading users');
        
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

async function loadStats() {
    try {
        const response = await fetch(ENDPOINTS.stats);
        if (!response.ok) return;
        
        const stats = await response.json();
        
        document.getElementById('totalUsers').textContent = stats.total || 0;
        document.getElementById('activeUsers').textContent = stats.active || 0;
        document.getElementById('confirmedUsers').textContent = stats.confirmed || 0;
        document.getElementById('monthlyUsers').textContent = stats.monthly || 0;
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
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

async function loadStoragePlans() {
    try {
        const response = await fetch(ENDPOINTS.storagePlans);
        const plans = await response.json();
        
        const select = document.getElementById('userStoragePlan');
        select.innerHTML = '<option value="">Seleccionar plan...</option>';
        
        plans.forEach(plan => {
            const option = document.createElement('option');
            option.value = plan.id;
            option.textContent = `${plan.name} (${plan.storage_mb} MB)`;
            select.appendChild(option);
        });
        
        return plans; // Devuelve la promesa
        
    } catch (error) {
        console.error('Error loading storage plans:', error);
        throw error;
    }
}

function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    
    if (users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="no-results">
                    No se encontraron usuarios
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.name || '-'}</td>
            <td>${user.email || '-'}</td>
            <td>${user.institute || '-'}</td>
            <td>${user.country || '-'}</td>
            <td>${user.user_type || '-'}</td>
            <td>
                <span class="status-badge ${user.is_active ? 'status-active' : 'status-inactive'}">
                    ${user.is_active ? 'Activo' : 'Inactivo'}
                    ${user.confirmado ? '✓' : ''}
                </span>
            </td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                <div class="storage-progress">
                    <div class="progress-bar" style="width: ${user.storage_percentage}%"></div>
                    <div class="progress-text">${Math.round(user.storage_percentage)}%</div>
                </div>
                <small>${formatBytes(user.used_storage)} / ${formatBytes(user.total_storage)}</small>
            </td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActions(${user.id})">⋮</button>
                    <div class="actions-dropdown" id="actions-${user.id}">
                        <a href="#" onclick="editUser(${user.id})">Editar</a>
                        <a href="#" onclick="viewUserDetails(${user.id})">Detalles</a>
                        <a href="#" class="danger" onclick="deleteUser(${user.id})">Eliminar</a>
                    </div>
                </div>
            </td>
        </tr>
    `).join('');
}

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES');
}

// Pagination
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
            const dots = document.createElement('span');
            dots.textContent = '...';
            controls.appendChild(dots);
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
            const dots = document.createElement('span');
            dots.textContent = '...';
            controls.appendChild(dots);
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

function updateTableStats(pagination) {
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 10) + 1;
    const end = Math.min(start + (pagination.per_page || 10) - 1, pagination.total || 0);
    
    document.getElementById('tableStats').textContent = `${pagination.total || 0} usuarios encontrados`;
    document.getElementById('paginationInfo').textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0}`;
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const type = document.getElementById('typeFilter').value;
    const status = document.getElementById('statusFilter').value;
    const country = document.getElementById('countryFilter').value;
    const institution = document.getElementById('institutionFilter').value;

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (type) currentFilters.user_type = type;
    if (country) currentFilters.country = country;
    if (status) currentFilters.status = status;
    if (institution) currentFilters.institution = institution;

    currentPage = 1;
    loadUsers(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('typeFilter').value = '';
    document.getElementById('countryFilter').value = '';
    document.getElementById('institutionFilter').value = '';
    document.getElementById('statusFilter').value = '';
    
    currentFilters = {};
    loadUsers(1);
}

// Sort function
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    loadUsers(currentPage);
}

// User CRUD operations
async function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Nuevo Usuario';
    document.getElementById('userForm').reset();
    document.getElementById('userId').value = '';

    // Cargar datos en los selects antes de mostrar el modal
    await Promise.all([
        loadInstitutionsForModal(),
        loadCountriesForModal(),
        loadStoragePlans()
    ]);

    document.getElementById('userModal').classList.add('show');
}

async function editUser(userId) {
    try {
        const response = await fetch(ENDPOINTS.update(userId));
        if (!response.ok) throw new Error('Error loading user');
        
        const data = await response.json();
        const user = data.user;
        
        document.getElementById('modalTitle').textContent = 'Editar Usuario';
        document.getElementById('userId').value = user.id;
        document.getElementById('userEmail').value = user.email;
        document.getElementById('userName').value = user.name;
        document.getElementById('userLastname').value = user.lastname;
        
        // Cargar datos en los selects y ESPERAR a que terminen
        await Promise.all([
            loadInstitutionsForModal(),
            loadCountriesForModal(),
            loadStoragePlans()
        ]);
        
        // Ahora establecer los valores - después de que los selects están cargados
        document.getElementById('userInstitute').value = user.institute || '';
        document.getElementById('userCountry').value = user.country || '';
        document.getElementById('userType').value = user.user_type || '';
        document.getElementById('userStoragePlan').value = user.storage_plan_id || '';
        document.getElementById('userActive').checked = user.is_active;
        document.getElementById('userConfirmed').checked = user.confirmado;
        
        document.getElementById('userModal').classList.add('show');
        
    } catch (error) {
        console.error('Error loading user:', error);
        showError('Error al cargar usuario: ' + error.message);
    }
}

// Modificar las funciones de carga para que devuelvan la promesa
async function loadInstitutionsForModal() {
    try {
        const response = await fetch(ENDPOINTS.institutions);
        const institutions = await response.json();
        
        const select = document.getElementById('userInstitute');
        select.innerHTML = '<option value="">Seleccionar institución...</option>';
        
        institutions.forEach(institution => {
            const option = document.createElement('option');
            option.value = institution.id;
            option.textContent = institution.institution;
            select.appendChild(option);
        });
        
        return institutions; // Devuelve la promesa
        
    } catch (error) {
        console.error('Error loading institutions:', error);
        throw error;
    }
}

async function loadCountriesForModal() {
    try {
        const response = await fetch(ENDPOINTS.countries);
        const countries = await response.json();
        
        const select = document.getElementById('userCountry');
        select.innerHTML = '<option value="">Seleccionar país...</option>';
        
        countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.id;
            option.textContent = country.country;
            select.appendChild(option);
        });
        
        return countries; // Devuelve la promesa
        
    } catch (error) {
        console.error('Error loading countries:', error);
        throw error;
    }
}

async function saveUser() {
    try {
        const userId = document.getElementById('userId').value;
        const isEdit = !!userId;
        
        const userData = {
            email: document.getElementById('userEmail').value,
            name: document.getElementById('userName').value,
            lastname: document.getElementById('userLastname').value,
            institute: document.getElementById('userInstitute').value,
            country: document.getElementById('userCountry').value,
            user_type: document.getElementById('userType').value,
            is_active: document.getElementById('userActive').checked,
            confirmado: document.getElementById('userConfirmed').checked,
            storage_plan_id: document.getElementById('userStoragePlan').value || null,
            password: document.getElementById('userPassword').value
        };
        
        const url = isEdit ? ENDPOINTS.update(userId) : ENDPOINTS.create;
        const method = isEdit ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(userData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error saving user');
        }
        
        closeModal();
        loadUsers(currentPage);
        loadStats();
        showSuccess(isEdit ? 'Usuario actualizado' : 'Usuario creado');
        
    } catch (error) {
        console.error('Error saving user:', error);
        showError('Error: ' + error.message);
    }
}

async function deleteUser(userId) {
    if (!confirm('¿Estás seguro de eliminar este usuario? Esta acción no se puede deshacer.')) return;
    
    try {
        const response = await fetch(ENDPOINTS.delete(userId), {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Error deleting user');
        
        loadUsers(currentPage);
        loadStats();
        showSuccess('Usuario eliminado');
        
    } catch (error) {
        console.error('Error deleting user:', error);
        showError('Error al eliminar usuario: ' + error.message);
    }
}

async function viewUserDetails(userId) {
    try {
        currentUserId = userId;
        const response = await fetch(ENDPOINTS.update(userId));
        if (!response.ok) throw new Error('Error loading user details');
        
        const data = await response.json();
        const user = data.user;
        
        // Buscar el nombre de la institución y país usando los IDs
        const institution = globalInstitutions.find(inst => inst.id == user.institute);
        const country = globalCountries.find(c => c.id == user.country);
        
        document.getElementById('offcanvasTitle').textContent = `Detalles: ${user.name} ${user.lastname}`;
        
        // Build details HTML
        let html = `
            <div class="user-details">
                <div class="detail-row">
                    <span class="detail-label">Email:</span>
                    <span class="detail-value">${user.email}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Institución:</span>
                    <span class="detail-value">${institution ? institution.institution : user.institute || '-'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">País:</span>
                    <span class="detail-value">${country ? country.country : user.country || '-'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Tipo:</span>
                    <span class="detail-value">${user.user_type || '-'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Estado:</span>
                    <span class="detail-value">
                        ${user.is_active ? 'Activo' : 'Inactivo'} | 
                        ${user.confirmado ? 'Confirmado' : 'No confirmado'}
                    </span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Registro:</span>
                    <span class="detail-value">${formatDate(user.created_at)}</span>
                </div>
                
                <h4>Almacenamiento</h4>
                <div class="storage-info">
                    <div class="storage-plan">
                        <span class="detail-label">Plan:</span>
                        <span class="detail-value">${user.storage_plan || 'Ninguno'}</span>
                    </div>
                    <div class="progress-container">
                        <div class="progress-bar" style="width: ${data.storage_info.percentage}%"></div>
                        <div class="progress-text">${Math.round(data.storage_info.percentage)}%</div>
                    </div>
                    <div class="storage-usage">
                        ${formatBytes(data.storage_info.used)} / ${formatBytes(data.storage_info.total)}
                    </div>
                </div>
                
                <h4>Complementos</h4>
                <div class="addons-list">
        `;
        
        if (data.addons.length > 0) {
            data.addons.forEach(addon => {
                html += `
                    <div class="addon-item">
                        <div class="addon-name">${addon.name}</div>
                        <div class="addon-storage">+${addon.storage_mb} MB</div>
                        ${addon.expiry_date ? `<div class="addon-expiry">Expira: ${formatDate(addon.expiry_date)}</div>` : ''}
                    </div>
                `;
            });
        } else {
            html += '<p>No hay complementos activos</p>';
        }
        
        html += `
                </div>
                <div class="offcanvas-actions">
                    <button class="btn btn-primary" onclick="editUser(${user.id})">Editar Usuario</button>
                    <button class="btn btn-secondary" onclick="manageStorage(${user.id})">Gestionar Almacenamiento</button>
                </div>
            </div>
        `;
        
        document.getElementById('offcanvasContent').innerHTML = html;
        document.getElementById('detailsOffcanvas').classList.add('show');
        
    } catch (error) {
        console.error('Error loading user details:', error);
        showError('Error al cargar detalles: ' + error.message);
    }
}

async function manageStorage(userId) {
    // Close current offcanvas
    closeOffcanvas();
    
    // Open storage management offcanvas
    currentUserId = userId;
    
    try {
        // Fetch storage plans and addons
        const [plansResponse, addonsResponse] = await Promise.all([
            fetch(ENDPOINTS.storagePlans),
            fetch(ENDPOINTS.storageAddons),
        ]);
        
        const plans = await plansResponse.json();
        const addons = await addonsResponse.json();
        
        // Get current user storage info
        const userResponse = await fetch(ENDPOINTS.update(userId));
        const userData = await userResponse.json();
        const user = userData.user;
        
        // Build storage management UI
        let html = `
            <div class="storage-management">
                <h4>Plan Actual</h4>
                <div class="current-plan">
                    ${user.storage_plan ? user.storage_plan : 'Ningún plan seleccionado'}
                </div>
                
                <h4>Seleccionar Plan</h4>
                <div class="plans-grid">
        `;
        
        plans.forEach(plan => {
            html += `
                <div class="plan-card ${user.storage_plan_id === plan.id ? 'selected' : ''}" 
                     onclick="selectPlan(${plan.id})">
                    <div class="plan-name">${plan.name}</div>
                    <div class="plan-storage">${plan.storage_mb} MB</div>
                </div>
            `;
        });
        
        html += `
                </div>
                
                <h4>Complementos</h4>
                <div class="addons-grid">
        `;
        
        addons.forEach(addon => {
            // Check if user has this addon
            const hasAddon = userData.addons.some(a => a.id === addon.id);
            
            html += `
                <div class="addon-card ${hasAddon ? 'active' : ''}">
                    <div class="addon-header">
                        <div class="addon-name">${addon.name}</div>
                        <div class="addon-price">$${addon.price}/mes</div>
                    </div>
                    <div class="addon-storage">+${addon.storage_mb} MB</div>
                    <div class="addon-actions">
                        <button class="btn ${hasAddon ? 'btn-danger' : 'btn-primary'}" 
                                onclick="${hasAddon ? 'removeAddon' : 'addAddon'}(${addon.id})">
                            ${hasAddon ? 'Remover' : 'Agregar'}
                        </button>
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
                <div class="storage-actions">
                    <button class="btn btn-cancel" onclick="closeOffcanvas()">Cancelar</button>
                    <button class="btn btn-primary" onclick="saveStorageChanges()">Guardar Cambios</button>
                </div>
            </div>
        `;
        
        document.getElementById('offcanvasTitle').textContent = 'Gestión de Almacenamiento';
        document.getElementById('offcanvasContent').innerHTML = html;
        document.getElementById('detailsOffcanvas').classList.add('show');
        
    } catch (error) {
        console.error('Error loading storage options:', error);
        showError('Error al cargar opciones de almacenamiento');
    }
}

function closeOffcanvas() {
    document.getElementById('detailsOffcanvas').classList.remove('show');
}

function closeModal() {
    document.getElementById('userModal').classList.remove('show');
}

function toggleActions(userId) {
    const dropdown = document.getElementById(`actions-${userId}`);
    dropdown.classList.toggle('show');
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('.actions-menu')) {
        document.querySelectorAll('.actions-dropdown.show').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
    
});

// Utility functions
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('usersTable');
    loading.style.display = show ? 'flex' : 'none';
    table.style.display = show ? 'none' : 'table';
}

function showLoading2(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('institutionsTable');
    
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

async function exportUsers() {
    try {
        const response = await fetch(ENDPOINTS.export);
        if (!response.ok) throw new Error('Error exporting');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'usuarios.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('Export error:', error);
        showError('Error al exportar usuarios');
    }
}