// Global variables
let currentPage = 1;
let totalPages = 1;
let totalProvinces = 0;
let sortField = 'created_date';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints
const API_BASE = '/provinces_bp/api/provinces';
const ENDPOINTS = {
    list: `${API_BASE}`,
    create: `${API_BASE}`,
    update: (id) => `${API_BASE}/${id}`,
    delete: (id) => `${API_BASE}/${id}`,
    export: `${API_BASE}/export`,
    stats: `${API_BASE}/stats`,
    countries: '/countries_bp/api/countries/dropdown'
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadProvinces();
    loadStats();
    loadCountries();
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

    document.getElementById('countryFilter').addEventListener('change', applyFilters);
    document.getElementById('dateFromFilter').addEventListener('change', applyFilters);

    // Modal close events
    document.getElementById('provinceModal').addEventListener('click', function(e) {
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

// Load provinces from API
async function loadProvinces(page = 1) {
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
        
        displayProvinces(data.provinces || []);
        updatePagination(data.pagination || {});
        updateTableStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading provinces:', error);
        showError('Error al cargar provincias/estados: ' + error.message);
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
        
        document.getElementById('totalProvinces').textContent = stats.total || 0;
        document.getElementById('monthlyProvinces').textContent = stats.monthly || 0;
        document.getElementById('latestProvince').textContent = stats.latest || '-';
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load countries for dropdowns
async function loadCountries() {
    try {
        const response = await fetch(ENDPOINTS.countries);
        if (!response.ok) return;
        
        const countries = await response.json();
        
        // Populate filter dropdown
        const filterSelect = document.getElementById('countryFilter');
        filterSelect.innerHTML = '<option value="">Todos los países</option>';
        
        // Populate modal dropdown
        const modalSelect = document.getElementById('provinceCountry');
        modalSelect.innerHTML = '<option value="">Seleccionar país</option>';
        
        countries.forEach(country => {
            const filterOption = document.createElement('option');
            filterOption.value = country.id;
            filterOption.textContent = country.country;
            filterSelect.appendChild(filterOption);
            
            const modalOption = document.createElement('option');
            modalOption.value = country.id;
            modalOption.textContent = country.country;
            modalSelect.appendChild(modalOption);
        });
        
    } catch (error) {
        console.error('Error loading countries:', error);
    }
}

// Display provinces in table
function displayProvinces(provinces) {
    const tbody = document.getElementById('provincesTableBody');
    
    if (provinces.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron provincias/estados
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = provinces.map(province => `
        <tr>
            <td style="font-weight: 500; color: #495057;">${province.id}</td>
            <td>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 8px;"><i class="bi bi-globe-americas-fill"></i></span>
                    <span style="font-weight: 500; color: #212529;">${province.province_state || 'Sin nombre'}</span>
                </div>
            </td>
            <td>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 16px; margin-right: 6px;"><i class="bi bi-globe-americas-fill"></i></span>
                    <span style="color: #495057;">${province.country_name || 'Sin país'}</span>
                </div>
            </td>
            <td>${formatDate(province.created_date)}</td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActionDropdown(${province.id})">
                          <i class="bi bi-grid"></i> Opciones
                    </button>
                    <div class="actions-dropdown" id="dropdown-${province.id}">
                        <a href="#" class="dropdown-item" onclick="editProvince(${province.id})"><i class="bi bi-pencil"></i>  Editar</a>
                        <a href="#" class="dropdown-item danger" onclick="deleteProvince(${province.id})"><i class="bi bi-trash"></i>  Eliminar</a>
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

// Pagination functions
function updatePagination(pagination) {
    totalPages = pagination.pages || 1;
    totalProvinces = pagination.total || 0;
    
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => loadProvinces(currentPage - 1);
    controls.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => loadProvinces(1);
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
        pageBtn.onclick = () => loadProvinces(i);
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
        lastBtn.onclick = () => loadProvinces(totalPages);
        controls.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Siguiente →';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadProvinces(currentPage + 1);
    controls.appendChild(nextBtn);
}

function updateTableStats(pagination) {
    const stats = document.getElementById('tableStats');
    const info = document.getElementById('paginationInfo');
    
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 20) + 1;
    const end = Math.min(start + (pagination.per_page || 20) - 1, pagination.total || 0);
    
    stats.textContent = `${pagination.total || 0} provincias/estados encontradas`;
    info.textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0} provincias/estados`;
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const countryId = document.getElementById('countryFilter').value;
    const dateFrom = document.getElementById('dateFromFilter').value;

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (countryId) currentFilters.country_id = countryId;
    if (dateFrom) currentFilters.date_from = dateFrom;

    currentPage = 1;
    loadProvinces(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('countryFilter').value = '';
    document.getElementById('dateFromFilter').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadProvinces(1);
}

// Sort functions
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    loadProvinces(currentPage);
}

// Modal functions
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Nueva Provincia/Estado';
    document.getElementById('provinceForm').reset();
    document.getElementById('provinceId').value = '';
    document.getElementById('provinceModal').classList.add('show');
    document.getElementById('provinceName').focus();
}

function closeModal() {
    document.getElementById('provinceModal').classList.remove('show');
}

// CRUD operations
async function saveProvince() {
    try {
        const formData = {
            province_state: document.getElementById('provinceName').value.trim(),
            country_id: document.getElementById('provinceCountry').value
        };

        if (!formData.province_state) {
            showError('El nombre de la provincia/estado es requerido');
            return;
        }

        if (!formData.country_id) {
            showError('El país es requerido');
            return;
        }

        const provinceId = document.getElementById('provinceId').value;
        const isEdit = !!provinceId;

        const url = isEdit ? ENDPOINTS.update(provinceId) : ENDPOINTS.create;
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
            throw new Error(error.message || 'Error al guardar provincia/estado');
        }

        closeModal();
        loadProvinces(currentPage);
        loadStats();
        showSuccess(isEdit ? 'Provincia/estado actualizada correctamente' : 'Provincia/estado creada correctamente');

    } catch (error) {
        console.error('Error saving province:', error);
        showError('Error al guardar provincia/estado: ' + error.message);
    }
}

async function editProvince(provinceId) {
    try {
        const response = await fetch(ENDPOINTS.update(provinceId));
        
        if (!response.ok) {
            throw new Error('Error al cargar datos de la provincia/estado');
        }
        
        const province = await response.json();
        
        document.getElementById('modalTitle').textContent = 'Editar Provincia/Estado';
        document.getElementById('provinceId').value = province.id;
        document.getElementById('provinceName').value = province.province_state || '';
        document.getElementById('provinceCountry').value = province.country_id || '';
        
        document.getElementById('provinceModal').classList.add('show');
        document.getElementById('provinceName').focus();
        
    } catch (error) {
        console.error('Error loading province:', error);
        showError('Error al cargar datos de la provincia/estado: ' + error.message);
    }
}

async function deleteProvince(provinceId) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer. ¿Deseas eliminar esta provincia/estado?',
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
        const response = await fetch(ENDPOINTS.delete(provinceId), {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al eliminar provincia/estado');
        }

        loadProvinces(currentPage);
        loadStats();
        showSuccess('Provincia/estado eliminada correctamente');

    } catch (error) {
        console.error('Error deleting province:', error);
        showError('Error al eliminar provincia/estado: ' + error.message);
    }
}

// Export function
async function exportProvinces() {
    try {
        const response = await fetch(ENDPOINTS.export);
        
        if (!response.ok) {
            throw new Error('Error al exportar provincias/estados');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `provincias_estados_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess('Provincias/estados exportadas correctamente');

    } catch (error) {
        console.error('Error exporting provinces:', error);
        showError('Error al exportar provincias/estados: ' + error.message);
    }
}

// Action dropdown functions
function toggleActionDropdown(provinceId) {
    const dropdown = document.getElementById(`dropdown-${provinceId}`);
    const allDropdowns = document.querySelectorAll('.actions-dropdown');
    
    allDropdowns.forEach(d => {
        if (d !== dropdown) d.classList.remove('show');
    });
    
    dropdown.classList.toggle('show');
}

// Utility functions
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('provincesTable');
    
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