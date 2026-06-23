// Global variables
let currentPage = 1;
let totalPages = 1;
let totalCities = 0;
let sortField = 'created_date';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints
const API_BASE = '/cities_bp/api/cities';
const ENDPOINTS = {
    list: `${API_BASE}`,
    create: `${API_BASE}`,
    update: (id) => `${API_BASE}/${id}`,
    delete: (id) => `${API_BASE}/${id}`,
    export: `${API_BASE}/export`,
    stats: `${API_BASE}/stats`,
    dropdown: `${API_BASE}/dropdown`,
    byState: (stateId) => `${API_BASE}/by-state/${stateId}`,
    search: `${API_BASE}/search`
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadCities();
    loadStats();
    loadStatesDropdown();
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
    document.getElementById('stateFilter').addEventListener('change', applyFilters);

    // Modal close events
    document.getElementById('cityModal').addEventListener('click', function(e) {
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

// Load cities from API
async function loadCities(page = 1) {
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
        
        displayCities(data.cities || []);
        updatePagination(data.pagination || {});
        updateTableStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading cities:', error);
        showError('Error al cargar ciudades: ' + error.message);
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
        
        document.getElementById('totalCities').textContent = stats.total || 0;
        document.getElementById('monthlyCities').textContent = stats.monthly || 0;
        document.getElementById('latestCity').textContent = stats.latest || '-';
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load states dropdown
async function loadStatesDropdown() {
    try {
        // Asumiendo que tienes un endpoint para estados/provincias
        const response = await fetch('/states_bp/api/states/dropdown');
        if (!response.ok) return;
        
        const states = await response.json();
        const stateFilter = document.getElementById('stateFilter');
        const cityStateSelect = document.getElementById('cityState');
        
        // Clear existing options except first one
        stateFilter.innerHTML = '<option value="">Todos los estados</option>';
        cityStateSelect.innerHTML = '<option value="">Seleccionar estado</option>';
        
        states.forEach(state => {
            const option1 = new Option(state.province_state, state.id);
            const option2 = new Option(state.province_state, state.id);
            stateFilter.appendChild(option1);
            cityStateSelect.appendChild(option2);
        });
        
    } catch (error) {
        console.error('Error loading states:', error);
    }
}

// Display cities in table
function displayCities(cities) {
    const tbody = document.getElementById('citiesTableBody');
    
    if (cities.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron ciudades
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = cities.map(city => `
        <tr>
            <td style="font-weight: 500; color: #495057;">${city.id}</td>
            <td>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 8px;"><i class="bi bi-buildings"></i></span>
                    <span style="font-weight: 500; color: #212529;">${city.city || 'Sin nombre'}</span>
                </div>
            </td>
            <td>
                <span style="background-color: #e3f2fd; color: #1976d2; padding: 2px 8px; border-radius: 12px; font-size: 12px;">
                    ${city.state_name || 'Sin estado'}
                </span>
            </td>
            <td>${formatDate(city.created_date)}</td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActionDropdown(${city.id})">
                         <i class="bi bi-grid"></i> Opciones
                    </button>
                    <div class="actions-dropdown" id="dropdown-${city.id}">
                        <a href="#" class="dropdown-item" onclick="editCity(${city.id})"><i class="bi bi-pencil"></i> Editar</a>
                        <a href="#" class="dropdown-item danger" onclick="deleteCity(${city.id})"><i class="bi bi-trash"></i>  Eliminar</a>
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
    totalCities = pagination.total || 0;
    
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => loadCities(currentPage - 1);
    controls.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => loadCities(1);
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
        pageBtn.onclick = () => loadCities(i);
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
        lastBtn.onclick = () => loadCities(totalPages);
        controls.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Siguiente →';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadCities(currentPage + 1);
    controls.appendChild(nextBtn);
}

function updateTableStats(pagination) {
    const stats = document.getElementById('tableStats');
    const info = document.getElementById('paginationInfo');
    
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 20) + 1;
    const end = Math.min(start + (pagination.per_page || 20) - 1, pagination.total || 0);
    
    stats.textContent = `${pagination.total || 0} ciudades encontradas`;
    info.textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0} ciudades`;
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const dateFrom = document.getElementById('dateFromFilter').value;
    const stateId = document.getElementById('stateFilter').value;

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (dateFrom) currentFilters.date_from = dateFrom;
    if (stateId) currentFilters.state_id = stateId;

    currentPage = 1;
    loadCities(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('dateFromFilter').value = '';
    document.getElementById('stateFilter').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadCities(1);
}

// Sort functions
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    loadCities(currentPage);
}

// Modal functions
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Nueva Ciudad';
    document.getElementById('cityForm').reset();
    document.getElementById('cityId').value = '';
    document.getElementById('cityModal').classList.add('show');
    document.getElementById('cityName').focus();
}

function closeModal() {
    document.getElementById('cityModal').classList.remove('show');
}

// CRUD operations
async function saveCity() {
    try {
        const formData = {
            city: document.getElementById('cityName').value.trim(),
            state_id: document.getElementById('cityState').value || null,
            user_id: document.getElementById('cityUserId').value || null
        };

        if (!formData.city) {
            showError('El nombre de la ciudad es requerido');
            return;
        }

        const cityId = document.getElementById('cityId').value;
        const isEdit = !!cityId;

        const url = isEdit ? ENDPOINTS.update(cityId) : ENDPOINTS.create;
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
            throw new Error(error.error || 'Error al guardar ciudad');
        }

        closeModal();
        loadCities(currentPage);
        loadStats();
        showSuccess(isEdit ? 'Ciudad actualizada correctamente' : 'Ciudad creada correctamente');

    } catch (error) {
        console.error('Error saving city:', error);
        showError('Error al guardar ciudad: ' + error.message);
    }
}

async function editCity(cityId) {
    try {
        const response = await fetch(ENDPOINTS.update(cityId));
        
        if (!response.ok) {
            throw new Error('Error al cargar datos de la ciudad');
        }
        
        const city = await response.json();
        
        document.getElementById('modalTitle').textContent = 'Editar Ciudad';
        document.getElementById('cityId').value = city.id;
        document.getElementById('cityName').value = city.city || '';
        document.getElementById('cityState').value = city.state_id || '';
        document.getElementById('cityUserId').value = city.user_id || '';
        
        document.getElementById('cityModal').classList.add('show');
        document.getElementById('cityName').focus();
        
    } catch (error) {
        console.error('Error loading city:', error);
        showError('Error al cargar datos de la ciudad: ' + error.message);
    }
}

async function deleteCity(cityId) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer. ¿Deseas eliminar esta ciudad?',
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
        const response = await fetch(ENDPOINTS.delete(cityId), {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error al eliminar ciudad');
        }

        loadCities(currentPage);
        loadStats();
        showSuccess('Ciudad eliminada correctamente');

    } catch (error) {
        console.error('Error deleting city:', error);
        showError('Error al eliminar ciudad: ' + error.message);
    }
}

// Export function
async function exportCities() {
    try {
        const response = await fetch(ENDPOINTS.export);
        
        if (!response.ok) {
            throw new Error('Error al exportar ciudades');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ciudades_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess('Ciudades exportadas correctamente');

    } catch (error) {
        console.error('Error exporting cities:', error);
        showError('Error al exportar ciudades: ' + error.message);
    }
}

// Action dropdown functions
function toggleActionDropdown(cityId) {
    const dropdown = document.getElementById(`dropdown-${cityId}`);
    const allDropdowns = document.querySelectorAll('.actions-dropdown');
    
    allDropdowns.forEach(d => {
        if (d !== dropdown) d.classList.remove('show');
    });
    
    dropdown.classList.toggle('show');
}

// Helper functions for cities by state
async function loadCitiesByState(stateId) {
    try {
        const response = await fetch(ENDPOINTS.byState(stateId));
        if (!response.ok) return [];
        
        return await response.json();
    } catch (error) {
        console.error('Error loading cities by state:', error);
        return [];
    }
}

// Search cities function (for autocomplete/dropdowns)
async function searchCities(searchTerm, stateId = null, limit = 10) {
    try {
        const params = new URLSearchParams({
            search: searchTerm,
            limit: limit
        });
        
        if (stateId) params.append('state_id', stateId);

        const response = await fetch(`${ENDPOINTS.search}?${params}`);
        if (!response.ok) return [];
        
        return await response.json();
    } catch (error) {
        console.error('Error searching cities:', error);
        return [];
    }
}

// Utility functions
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('citiesTable');
    
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