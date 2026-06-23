// Global variables
let currentPage = 1;
let totalPages = 1;
let totalServices = 0;
let sortField = 'created_at';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints
const API_BASE = '/settings_bp/api/services';
const ENDPOINTS = {
    list: `${API_BASE}`,
    create: `${API_BASE}`,
    update: (id) => `${API_BASE}/${id}`,
    delete: (id) => `${API_BASE}/${id}`,
    get: (id) => `${API_BASE}/${id}`,
    export: `${API_BASE}/export`,
    stats: `${API_BASE}/stats`,
    types: `${API_BASE}/types`,
    test: (id) => `${API_BASE}/test/${id}`
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadServices();
    loadStats();
    loadServiceTypes();
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

    document.getElementById('dateFromFilter').addEventListener('change', applyFilters);
    document.getElementById('serviceTypeFilter').addEventListener('change', applyFilters);
    document.getElementById('isActiveFilter').addEventListener('change', applyFilters);
    document.getElementById('isMonitoredFilter').addEventListener('change', applyFilters);

    // Modal close events
    document.getElementById('serviceModal').addEventListener('click', function(e) {
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

// Load services from API
async function loadServices(page = 1) {
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
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        displayServices(data.services || []);
        updatePagination(data.pagination || {});
        updateTableStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading services:', error);
        showError('Error al cargar servicios: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(ENDPOINTS.stats);
        if (!response.ok) return;
        
        const stats = await response.json();
        
        document.getElementById('totalServices').textContent = stats.total || 0;
        document.getElementById('activeServices').textContent = stats.active || 0;
        document.getElementById('monitoredServices').textContent = stats.monitored || 0;
        document.getElementById('monthlyServices').textContent = stats.monthly || 0;
        document.getElementById('commonType').textContent = stats.most_common_type || '-';
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load service types dropdown
async function loadServiceTypes() {
    try {
        const response = await fetch(ENDPOINTS.types);
        if (!response.ok) return;
        
        const types = await response.json();
        const typeFilter = document.getElementById('serviceTypeFilter');
        const serviceTypeSelect = document.getElementById('serviceType');
        
        // Clear existing options except first one
        typeFilter.innerHTML = '<option value="">Todos los tipos</option>';
        serviceTypeSelect.innerHTML = '<option value="">Seleccionar tipo</option>';
        
        const commonTypes = ['HTTP', 'HTTPS', 'TCP', 'UDP', 'SSH', 'FTP', 'SMTP', 'Database', 'API', 'WebSocket'];
        
        // Add common types first
        commonTypes.forEach(type => {
            const option1 = new Option(type, type);
            const option2 = new Option(type, type);
            typeFilter.appendChild(option1);
            serviceTypeSelect.appendChild(option2);
        });
        
        // Add existing types from database
        types.forEach(type => {
            if (!commonTypes.includes(type)) {
                const option1 = new Option(type, type);
                const option2 = new Option(type, type);
                typeFilter.appendChild(option1);
                serviceTypeSelect.appendChild(option2);
            }
        });
        
    } catch (error) {
        console.error('Error loading service types:', error);
    }
}

// Display services in table
function displayServices(services) {
    const tbody = document.getElementById('servicesTableBody');
    
    if (services.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron servicios
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = services.map(service => `
        <tr>
            <td style="font-weight: 500; color: #495057;">${service.id}</td>
            <td>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 16px; margin-right: 8px;"><i class="${service.icon}"></i></span>
                    <div>
                        <div style="font-weight: 500; color: #212529;">${service.display_name || service.name}</div>
                        <div style="font-size: 12px; color: #6c757d;">${service.name}</div>
                    </div>
                </div>
            </td>
            <td>
                <div style="font-weight: 500; color: #495057;">${service.host}</div>
                <div style="font-size: 12px; color: #6c757d;">Puerto: ${service.port}</div>
            </td>
            <td>
                <span style="background-color: ${getServiceTypeColor(service.service_type)}; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 500;">
                    ${service.service_type}
                </span>
            </td>
            <td>
                <span class="status-badge ${service.is_active ? 'active' : 'inactive'}">
                    ${service.is_active ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td>
                <span class="status-badge ${service.is_monitored ? 'monitored' : 'not-monitored'}">
                    ${service.is_monitored ? 'Sí' : 'No'}
                </span>
            </td>
            <td>${formatDate(service.created_at)}</td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActionDropdown(${service.id})">
                          <i class="bi bi-grid"></i> Opciones
                    </button>
                    <div class="actions-dropdown" id="dropdown-${service.id}">
                        <a href="#" class="dropdown-item" onclick="testService(${service.id})">
                            <i class="bi bi-wifi"></i> Probar Conexión
                        </a>
                        <a href="#" class="dropdown-item" onclick="editService(${service.id})">
                            <i class="bi bi-pencil"></i> Editar
                        </a>
                        <a href="#" class="dropdown-item danger" onclick="deleteService(${service.id})">
                            <i class="bi bi-trash"></i> Eliminar
                        </a>
                    </div>
                </div>
            </td>
        </tr>
    `).join('');
}

// Helper functions
function getServiceTypeColor(type) {
    const colors = {
        'HTTP': '#e3f2fd; color: #1976d2',
        'HTTPS': '#e8f5e8; color: #2e7d32',
        'TCP': '#fff3e0; color: #f57c00',
        'UDP': '#fce4ec; color: #c2185b',
        'SSH': '#f3e5f5; color: #7b1fa2',
        'FTP': '#e0f2f1; color: #00695c',
        'SMTP': '#fff8e1; color: #f9a825',
        'Database': '#e8eaf6; color: #3f51b5',
        'API': '#e1f5fe; color: #0277bd',
        'WebSocket': '#f1f8e9; color: #558b2f'
    };
    return colors[type] || '#f5f5f5; color: #757575';
}

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

// Pagination functions
function updatePagination(pagination) {
    totalPages = pagination.pages || 1;
    totalServices = pagination.total || 0;
    
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.innerHTML = '<i class="bi bi-chevron-left"></i> Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => loadServices(currentPage - 1);
    controls.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => loadServices(1);
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
        pageBtn.onclick = () => loadServices(i);
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
        lastBtn.onclick = () => loadServices(totalPages);
        controls.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.innerHTML = 'Siguiente <i class="bi bi-chevron-right"></i>';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadServices(currentPage + 1);
    controls.appendChild(nextBtn);
}

function updateTableStats(pagination) {
    const stats = document.getElementById('tableStats');
    const info = document.getElementById('paginationInfo');
    
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 10) + 1;
    const end = Math.min(start + (pagination.per_page || 10) - 1, pagination.total || 0);
    
    stats.textContent = `${pagination.total || 0} servicios encontrados`;
    info.textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0} servicios`;
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const dateFrom = document.getElementById('dateFromFilter').value;
    const serviceType = document.getElementById('serviceTypeFilter').value;
    const isActive = document.getElementById('isActiveFilter').value;
    const isMonitored = document.getElementById('isMonitoredFilter').value;

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (dateFrom) currentFilters.date_from = dateFrom;
    if (serviceType) currentFilters.service_type = serviceType;
    if (isActive) currentFilters.is_active = isActive;
    if (isMonitored) currentFilters.is_monitored = isMonitored;

    currentPage = 1;
    loadServices(1);
}

// Show/Hide loading indicator
function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const servicesTable = document.getElementById('servicesTable');
    
    if (show) {
        loadingIndicator.style.display = 'flex';
        servicesTable.style.display = 'none';
    } else {
        loadingIndicator.style.display = 'none';
        servicesTable.style.display = 'table';
    }
}


// Show error message
function showError(message) {
    // Crear un toast o alert para mostrar errores
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger';
    errorDiv.style.position = 'fixed';
    errorDiv.style.top = '20px';
    errorDiv.style.right = '20px';
    errorDiv.style.zIndex = '9999';
    errorDiv.style.padding = '15px';
    errorDiv.style.backgroundColor = '#f8d7da';
    errorDiv.style.border = '1px solid #f5c6cb';
    errorDiv.style.borderRadius = '4px';
    errorDiv.style.color = '#721c24';
    errorDiv.innerHTML = `
        <strong>Error:</strong> ${message}
        <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; font-size: 18px; cursor: pointer;">&times;</button>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentElement) {
            errorDiv.remove();
        }
    }, 5000);
}

// Show success message
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'alert alert-success';
    successDiv.style.position = 'fixed';
    successDiv.style.top = '20px';
    successDiv.style.right = '20px';
    successDiv.style.zIndex = '9999';
    successDiv.style.padding = '15px';
    successDiv.style.backgroundColor = '#d4edda';
    successDiv.style.border = '1px solid #c3e6cb';
    successDiv.style.borderRadius = '4px';
    successDiv.style.color = '#155724';
    successDiv.innerHTML = `
        <strong>Éxito:</strong> ${message}
        <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; font-size: 18px; cursor: pointer;">&times;</button>
    `;
    
    document.body.appendChild(successDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (successDiv.parentElement) {
            successDiv.remove();
        }
    }, 3000);
}

// Clear all filters
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('dateFromFilter').value = '';
    document.getElementById('serviceTypeFilter').value = '';
    document.getElementById('isActiveFilter').value = '';
    document.getElementById('isMonitoredFilter').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadServices(1);
}

// Sort table functionality
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    currentPage = 1;
    loadServices(1);
}

// Toggle action dropdown
function toggleActionDropdown(serviceId) {
    const dropdown = document.getElementById(`dropdown-${serviceId}`);
    
    // Close all other dropdowns
    document.querySelectorAll('.actions-dropdown.show').forEach(d => {
        if (d !== dropdown) {
            d.classList.remove('show');
        }
    });
    
    // Toggle current dropdown
    dropdown.classList.toggle('show');
}

// Test service connection
async function testService(serviceId) {
    try {
        const response = await fetch(ENDPOINTS.test(serviceId), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess(result.message);
        } else {
            showError(result.message);
        }
        
    } catch (error) {
        showError('Error al probar la conexión: ' + error.message);
    }
}

// Open create modal
function openCreateModal() {
    document.getElementById('serviceId').value = '';
    document.getElementById('modalTitle').innerHTML = '<i class="bi bi-plus-square"></i> Nuevo Servicio';
    document.getElementById('serviceForm').reset();
    document.getElementById('isActive').checked = true;
    document.getElementById('isMonitored').checked = true;
    document.getElementById('serviceIcon').value = 'fas fa-server';
    document.getElementById('serviceTimeout').value = 5;
    document.getElementById('serviceModal').style.display = 'flex';
}

// Edit service
async function editService(serviceId) {
    try {
        const response = await fetch(ENDPOINTS.get(serviceId));
        if (!response.ok) {
            throw new Error('Error al cargar el servicio');
        }
        
        const service = await response.json();
        
        document.getElementById('serviceId').value = service.id;
        document.getElementById('serviceName').value = service.name || '';
        document.getElementById('displayName').value = service.display_name || '';
        document.getElementById('serviceHost').value = service.host || '';
        document.getElementById('servicePort').value = service.port || '';
        document.getElementById('serviceType').value = service.service_type || '';
        document.getElementById('serviceEndpoint').value = service.endpoint || '';
        document.getElementById('serviceTimeout').value = service.timeout || 5;
        document.getElementById('serviceIcon').value = service.icon || 'fas fa-server';
        document.getElementById('serviceUsername').value = service.username || '';
        document.getElementById('servicePassword').value = ''; // Por seguridad, no mostrar la contraseña
        document.getElementById('extraConfig').value = service.extra_config || '';
        document.getElementById('isActive').checked = service.is_active || false;
        document.getElementById('isMonitored').checked = service.is_monitored || false;
        
        document.getElementById('modalTitle').innerHTML = '<i class="bi bi-pencil"></i> Editar Servicio';
        document.getElementById('serviceModal').style.display = 'flex';
        
    } catch (error) {
        showError('Error al cargar el servicio: ' + error.message);
    }
}

// Save service (create or update)
async function saveService() {
    try {
        const serviceId = document.getElementById('serviceId').value;
        const isEditing = serviceId !== '';
        
        // Validar campos requeridos
        const requiredFields = ['serviceName', 'displayName', 'serviceHost', 'servicePort', 'serviceType'];
        for (const fieldId of requiredFields) {
            const field = document.getElementById(fieldId);
            if (!field.value.trim()) {
                showError(`El campo ${field.previousElementSibling.textContent} es requerido`);
                field.focus();
                return;
            }
        }
        
        // Validar JSON si se proporciona
        const extraConfig = document.getElementById('extraConfig').value.trim();
        if (extraConfig) {
            try {
                JSON.parse(extraConfig);
            } catch (e) {
                showError('La configuración extra debe ser un JSON válido');
                document.getElementById('extraConfig').focus();
                return;
            }
        }
        
        const data = {
            name: document.getElementById('serviceName').value.trim(),
            display_name: document.getElementById('displayName').value.trim(),
            host: document.getElementById('serviceHost').value.trim(),
            port: parseInt(document.getElementById('servicePort').value),
            service_type: document.getElementById('serviceType').value,
            endpoint: document.getElementById('serviceEndpoint').value.trim() || null,
            timeout: parseInt(document.getElementById('serviceTimeout').value) || 5,
            icon: document.getElementById('serviceIcon').value.trim() || 'fas fa-server',
            username: document.getElementById('serviceUsername').value.trim() || null,
            password: document.getElementById('servicePassword').value || null,
            extra_config: extraConfig || null,
            is_active: document.getElementById('isActive').checked,
            is_monitored: document.getElementById('isMonitored').checked
        };
        
        const url = isEditing ? ENDPOINTS.update(serviceId) : ENDPOINTS.create;
        const method = isEditing ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(result.message);
            closeModal();
            loadServices(currentPage);
            loadStats(); // Refresh stats
        } else {
            showError(result.error || 'Error al guardar el servicio');
        }
        
    } catch (error) {
        showError('Error al guardar el servicio: ' + error.message);
    }
}

// Delete service
async function deleteService(serviceId) {
    if (!confirm('¿Está seguro de que desea eliminar este servicio?')) {
        return;
    }
    
    try {
        const response = await fetch(ENDPOINTS.delete(serviceId), {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(result.message);
            loadServices(currentPage);
            loadStats(); // Refresh stats
        } else {
            showError(result.error || 'Error al eliminar el servicio');
        }
        
    } catch (error) {
        showError('Error al eliminar el servicio: ' + error.message);
    }
}

// Close modal
function closeModal() {
    document.getElementById('serviceModal').style.display = 'none';
}

// Export services
async function exportServices() {
    try {
        const response = await fetch(ENDPOINTS.export);
        if (!response.ok) {
            throw new Error('Error al exportar servicios');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `servicios_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showSuccess('Servicios exportados exitosamente');
        
    } catch (error) {
        showError('Error al exportar servicios: ' + error.message);
    }
}