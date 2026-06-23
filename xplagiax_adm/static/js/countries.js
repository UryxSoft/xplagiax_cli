// Global variables
let currentPage = 1;
let totalPages = 1;
let totalCountries = 0;
let sortField = 'created_date';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints
const API_BASE = '/countries_bp/api/countries';
const ENDPOINTS = {
    list: `${API_BASE}`,
    create: `${API_BASE}`,
    update: (id) => `${API_BASE}/${id}`,
    delete: (id) => `${API_BASE}/${id}`,
    export: `${API_BASE}/export`,
    stats: `${API_BASE}/stats`
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadCountries();
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

    document.getElementById('dateFromFilter').addEventListener('change', applyFilters);

    // Modal close events
    document.getElementById('countryModal').addEventListener('click', function(e) {
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

// Load countries from API
async function loadCountries(page = 1) {
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
        
        displayCountries(data.countries || []);
        updatePagination(data.pagination || {});
        updateTableStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading countries:', error);
        showError('Error al cargar países: ' + error.message);
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
        
        document.getElementById('totalCountries').textContent = stats.total || 0;
        document.getElementById('monthlyCountries').textContent = stats.monthly || 0;
        document.getElementById('latestCountry').textContent = stats.latest || '-';
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Display countries in table
function displayCountries(countries) {
    const tbody = document.getElementById('countriesTableBody');
    
    if (countries.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron países
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = countries.map(country => `
        <tr>
            <td style="font-weight: 500; color: #495057;">${country.id}</td>
            <td>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 20px; margin-right: 8px;"><i class="bi bi-globe-americas-fill"></i></span>
                    <span style="font-weight: 500; color: #212529;">${country.country || 'Sin nombre'}</span>
                </div>
            </td>
            <td>${formatDate(country.created_date)}</td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActionDropdown(${country.id})">
                          <i class="bi bi-grid"></i> Opciones
                    </button>
                    <div class="actions-dropdown" id="dropdown-${country.id}">
                        <a href="#" class="dropdown-item" onclick="editCountry(${country.id})"><i class="bi bi-pencil"></i>  Editar</a>
                        <a href="#" class="dropdown-item danger" onclick="deleteCountry(${country.id})"><i class="bi bi-trash"></i> Eliminar</a>
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
    totalCountries = pagination.total || 0;
    
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => loadCountries(currentPage - 1);
    controls.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => loadCountries(1);
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
        pageBtn.onclick = () => loadCountries(i);
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
        lastBtn.onclick = () => loadCountries(totalPages);
        controls.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Siguiente →';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadCountries(currentPage + 1);
    controls.appendChild(nextBtn);
}

function updateTableStats(pagination) {
    const stats = document.getElementById('tableStats');
    const info = document.getElementById('paginationInfo');
    
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 20) + 1;
    const end = Math.min(start + (pagination.per_page || 20) - 1, pagination.total || 0);
    
    stats.textContent = `${pagination.total || 0} países encontrados`;
    info.textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0} países`;
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const dateFrom = document.getElementById('dateFromFilter').value;

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (dateFrom) currentFilters.date_from = dateFrom;

    currentPage = 1;
    loadCountries(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('dateFromFilter').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadCountries(1);
}

// Sort functions
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    loadCountries(currentPage);
}

// Modal functions
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Nuevo País';
    document.getElementById('countryForm').reset();
    document.getElementById('countryId').value = '';
    document.getElementById('countryModal').classList.add('show');
    document.getElementById('countryName').focus();
}

function closeModal() {
    document.getElementById('countryModal').classList.remove('show');
}

// CRUD operations
async function saveCountry() {
    try {
        const formData = {
            country: document.getElementById('countryName').value.trim()
        };

        if (!formData.country) {
            showError('El nombre del país es requerido');
            return;
        }

        const countryId = document.getElementById('countryId').value;
        const isEdit = !!countryId;

        const url = isEdit ? ENDPOINTS.update(countryId) : ENDPOINTS.create;
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
            throw new Error(error.message || 'Error al guardar país');
        }

        closeModal();
        loadCountries(currentPage);
        loadStats();
        showSuccess(isEdit ? 'País actualizado correctamente' : 'País creado correctamente');

    } catch (error) {
        console.error('Error saving country:', error);
        showError('Error al guardar país: ' + error.message);
    }
}

async function editCountry(countryId) {
    try {
        const response = await fetch(ENDPOINTS.update(countryId));
        
        if (!response.ok) {
            throw new Error('Error al cargar datos del país');
        }
        
        const country = await response.json();
        
        document.getElementById('modalTitle').textContent = 'Editar País';
        document.getElementById('countryId').value = country.id;
        document.getElementById('countryName').value = country.country || '';
        
        document.getElementById('countryModal').classList.add('show');
        document.getElementById('countryName').focus();
        
    } catch (error) {
        console.error('Error loading country:', error);
        showError('Error al cargar datos del país: ' + error.message);
    }
}

async function deleteCountry(countryId) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer. ¿Deseas eliminar este país?',
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
        const response = await fetch(ENDPOINTS.delete(countryId), {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al eliminar país');
        }

        loadCountries(currentPage);
        loadStats();
        showSuccess('País eliminado correctamente');

    } catch (error) {
        console.error('Error deleting country:', error);
        showError('Error al eliminar país: ' + error.message);
    }
}

// Export function
async function exportCountries() {
    try {
        const response = await fetch(ENDPOINTS.export);
        
        if (!response.ok) {
            throw new Error('Error al exportar países');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `paises_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess('Países exportados correctamente');

    } catch (error) {
        console.error('Error exporting countries:', error);
        showError('Error al exportar países: ' + error.message);
    }
}

// Action dropdown functions
function toggleActionDropdown(countryId) {
    const dropdown = document.getElementById(`dropdown-${countryId}`);
    const allDropdowns = document.querySelectorAll('.actions-dropdown');
    
    allDropdowns.forEach(d => {
        if (d !== dropdown) d.classList.remove('show');
    });
    
    dropdown.classList.toggle('show');
}

// Utility functions
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('countriesTable');
    
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
