// Global variables
let currentPage = 1;
let totalPages = 1;
let totalInstitutions = 0;
let sortField = 'created_date';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints
const API_BASE = '/institutions_bp/api/institutions';
const ENDPOINTS = {
    list: `${API_BASE}`,
    create: `${API_BASE}`,
    update: (id) => `${API_BASE}/${id}`,
    delete: (id) => `${API_BASE}/${id}`,
    export: `${API_BASE}/export`,
    stats: `${API_BASE}/stats`,
    types: '/institution_types_bp/api/institution_types/dropdown',
    countries: '/countries_bp/api/countries/dropdown',
    cities: (countryId) => `/cities_bp/api/cities/dropdown/${countryId}`
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadInstitutions();
    loadStats();
    loadFilterOptions();
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

    ['typeFilter', 'countryFilter', 'cityFilter'].forEach(id => {
        document.getElementById(id).addEventListener('change', applyFilters);
    });

    // Country change for city filtering
    document.getElementById('countryFilter').addEventListener('change', function() {
        const countryId = this.value;
        loadCitiesForFilter(countryId);
    });

    // Modal close events
    document.getElementById('institutionModal').addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });

    document.getElementById('typesModal').addEventListener('click', function(e) {
        if (e.target === this) closeTypesModal();
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

// Load institutions from API
async function loadInstitutions(page = 1) {
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
        
        displayInstitutions(data.institutions || []);
        updatePagination(data.pagination || {});
        updateTableStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading institutions:', error);
        showError('Error al cargar instituciones: ' + error.message);
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
        
        document.getElementById('totalInstitutions').textContent = stats.total || 0;
        document.getElementById('countriesCount').textContent = stats.countries || 0;
        document.getElementById('typesCount').textContent = stats.types || 0;
        document.getElementById('monthlyInstitutions').textContent = stats.monthly || 0;
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load filter options
async function loadFilterOptions() {
    try {
        const [types, countries] = await Promise.all([
            fetch(ENDPOINTS.types).then(r => r.json()),
            fetch(ENDPOINTS.countries).then(r => r.json())
        ]);

        populateSelect('typeFilter', types, 'institution_type');
        populateSelect('countryFilter', countries, 'country');

        // Also populate modal selects
        populateSelect('institutionType', types, 'institution_type');
        populateSelect('institutionCountry', countries, 'country');

    } catch (error) {
        console.error('Error loading filter options:', error);
    }
}

async function loadCitiesForFilter(countryId) {
    const cityFilter = document.getElementById('cityFilter');
    cityFilter.innerHTML = '<option value="">Todas</option>';
    
    if (!countryId) return;
    
    try {
        const response = await fetch(ENDPOINTS.cities(countryId));
        const cities = await response.json();
        
        cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city.id;
            option.textContent = city.city;
            cityFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading cities:', error);
    }
}

async function loadCities() {
    const countryId = document.getElementById('institutionCountry').value;
    const citySelect = document.getElementById('institutionCity');
    
    citySelect.innerHTML = '<option value="">Seleccionar ciudad...</option>';
    
    if (!countryId) return;
    
    try {
        const response = await fetch(ENDPOINTS.cities(countryId));
        const cities = await response.json();
        
        cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city.id;
            option.textContent = city.city;
            citySelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading cities:', error);
    }
}

function populateSelect(selectId, options, textField) {
    const select = document.getElementById(selectId);
    const currentOptions = select.querySelectorAll('option:not([value=""])');
    currentOptions.forEach(option => option.remove());

    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option.id;
        optionElement.textContent = option[textField];
        select.appendChild(optionElement);
    });
}

// Display institutions in table
function displayInstitutions(institutions) {
    const tbody = document.getElementById('institutionsTableBody');
    
    if (institutions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron instituciones
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = institutions.map(inst => `
        <tr>
            <td>
                <div style="font-weight: 500; color: #212529;">
                    ${inst.institution || 'Sin nombre'}
                </div>
            </td>
            <td>${inst.type_name || '-'}</td>
            <td>${inst.city_name || '-'}</td>
            <td>${inst.country_name || '-'}</td>
            <td>${formatDate(inst.created_date)}</td>
            <td>
                <span class="status-badge status-active">
                    ${inst.documents_count || 0} docs
                </span>
            </td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActionDropdown(${inst.id})">
                         <i class="bi bi-grid"></i> Opciones
                    </button>
                    <div class="actions-dropdown" id="dropdown-${inst.id}">
                        <a href="#" class="dropdown-item" onclick="editInstitution(${inst.id})"><i class="bi bi-pencil"></i> Editar</a>
                        <a href="#" class="dropdown-item" onclick="viewDocuments(${inst.id})"><i class="bi bi-file-earmark-text"></i> Ver Documentos</a>
                        <a href="#" class="dropdown-item" onclick="openTypesModal()"><i class="bi bi-files"></i> Gestionar Tipos</a>
                        <a href="#" class="dropdown-item danger" onclick="deleteInstitution(${inst.id})">i class="bi bi-trash"></i> Eliminar</a>
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
        day: 'numeric'
    });
}

// Pagination functions
function updatePagination(pagination) {
    totalPages = pagination.pages || 1;
    totalInstitutions = pagination.total || 0;
    
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => loadInstitutions(currentPage - 1);
    controls.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => loadInstitutions(1);
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
        pageBtn.onclick = () => loadInstitutions(i);
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
        lastBtn.onclick = () => loadInstitutions(totalPages);
        controls.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Siguiente →';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadInstitutions(currentPage + 1);
    controls.appendChild(nextBtn);
}

function updateTableStats(pagination) {
    const stats = document.getElementById('tableStats');
    const info = document.getElementById('paginationInfo');
    
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 20) + 1;
    const end = Math.min(start + (pagination.per_page || 20) - 1, pagination.total || 0);
    
    stats.textContent = `${pagination.total || 0} instituciones encontradas`;
    info.textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0} instituciones`;
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const type = document.getElementById('typeFilter').value;
    const country = document.getElementById('countryFilter').value;
    const city = document.getElementById('cityFilter').value;

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (type) currentFilters.institution_type = type;
    if (country) currentFilters.country_id = country;
    if (city) currentFilters.city_id = city;

    currentPage = 1;
    loadInstitutions(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('typeFilter').value = '';
    document.getElementById('countryFilter').value = '';
    document.getElementById('cityFilter').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadInstitutions(1);
}

// Sort functions
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    loadInstitutions(currentPage);
}

// Modal functions
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Nueva Institución';
    document.getElementById('institutionForm').reset();
    document.getElementById('institutionId').value = '';
    document.getElementById('institutionModal').classList.add('show');
}

function closeModal() {
    document.getElementById('institutionModal').classList.remove('show');
}

function openTypesModal() {
    document.getElementById('typesModal').classList.add('show');
    loadInstitutionTypes();
}

function closeTypesModal() {
    document.getElementById('typesModal').classList.remove('show');
}

// CRUD operations
async function saveInstitution() {
    try {
        const formData = {
            institution: document.getElementById('institutionName').value.trim(),
            institution_type: document.getElementById('institutionType').value || null,
            country_id: document.getElementById('institutionCountry').value || null,
            city_id: document.getElementById('institutionCity').value || null
        };

        const institutionId = document.getElementById('institutionId').value;
        const isEdit = !!institutionId;

        const url = isEdit ? ENDPOINTS.update(institutionId) : ENDPOINTS.create;
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
            throw new Error(error.message || 'Error al guardar institución');
        }

        closeModal();
        loadInstitutions(currentPage);
        loadStats();
        showSuccess(isEdit ? 'Institución actualizada correctamente' : 'Institución creada correctamente');

    } catch (error) {
        console.error('Error saving institution:', error);
        showError('Error al guardar institución: ' + error.message);
    }
}

async function editInstitution(institutionId) {
    try {
        const response = await fetch(ENDPOINTS.update(institutionId));
        
        if (!response.ok) {
            throw new Error('Error al cargar datos de la institución');
        }
        
        const institution = await response.json();
        
        document.getElementById('modalTitle').textContent = 'Editar Institución';
        document.getElementById('institutionId').value = institution.id;
        document.getElementById('institutionName').value = institution.institution || '';
        document.getElementById('institutionType').value = institution.institution_type || '';
        document.getElementById('institutionCountry').value = institution.country_id || '';
        
        // Load cities for the selected country
        if (institution.country_id) {
            await loadCities();
            document.getElementById('institutionCity').value = institution.city_id || '';
        }
        
        document.getElementById('institutionModal').classList.add('show');
        
    } catch (error) {
        console.error('Error loading institution:', error);
        showError('Error al cargar datos de la institución: ' + error.message);
    }
}

async function deleteInstitution(institutionId) {

    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer. ¿Deseas eliminar esta institución?',
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
        const response = await fetch(ENDPOINTS.delete(institutionId), {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al eliminar institución');
        }

        loadInstitutions(currentPage);
        loadStats();
        showSuccess('Institución eliminada correctamente');

    } catch (error) {
        console.error('Error deleting institution:', error);
        showError('Error al eliminar institución: ' + error.message);
    }
}

function viewDocuments(institutionId) {
    // Navigate to documents page with institution filter
    window.location.href = `/documents?institution=${institutionId}`;
}

// Institution Types Management
async function loadInstitutionTypes() {
    try {
        const response = await fetch(ENDPOINTS.types);
        const types = await response.json();
        
        const typesList = document.getElementById('typesList');
        
        if (types.length === 0) {
            typesList.innerHTML = '<p style="text-align: center; color: #6c757d; padding: 20px;">No hay tipos de institución registrados</p>';
            return;
        }
        
        typesList.innerHTML = types.map(type => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f8f9fa;">
                <span>${type.institution_type}</span>
                <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 12px;" onclick="deleteInstitutionType(${type.id})">
                    Eliminar
                </button>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading institution types:', error);
    }
}

async function addInstitutionType() {
    try {
        const typeName = document.getElementById('newTypeName').value.trim();
        
        if (!typeName) {
            showError('Ingresa un nombre para el tipo de institución');
            return;
        }
        
        const response = await fetch(ENDPOINTS.types, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                institution_type: typeName
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al crear tipo de institución');
        }
        
        document.getElementById('newTypeName').value = '';
        loadInstitutionTypes();
        loadFilterOptions(); // Refresh dropdowns
        showSuccess('Tipo de institución creado correctamente');
        
    } catch (error) {
        console.error('Error adding institution type:', error);
        showError('Error al crear tipo de institución: ' + error.message);
    }
}

async function deleteInstitutionType(typeId) {
    if (!confirm('¿Estás seguro de que quieres eliminar este tipo de institución?')) {
        return;
    }
    
    try {
        const response = await fetch(`${ENDPOINTS.types}/${typeId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al eliminar tipo de institución');
        }
        
        loadInstitutionTypes();
        loadFilterOptions(); // Refresh dropdowns
        showSuccess('Tipo de institución eliminado correctamente');
        
    } catch (error) {
        console.error('Error deleting institution type:', error);
        showError('Error al eliminar tipo de institución: ' + error.message);
    }
}

// Export function
async function exportInstitutions() {
    try {
        const response = await fetch(ENDPOINTS.export);
        
        if (!response.ok) {
            throw new Error('Error al exportar instituciones');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `instituciones_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess('Instituciones exportadas correctamente');

    } catch (error) {
        console.error('Error exporting institutions:', error);
        showError('Error al exportar instituciones: ' + error.message);
    }
}

// Action dropdown functions
function toggleActionDropdown(institutionId) {
    const dropdown = document.getElementById(`dropdown-${institutionId}`);
    const allDropdowns = document.querySelectorAll('.actions-dropdown');
    
    allDropdowns.forEach(d => {
        if (d !== dropdown) d.classList.remove('show');
    });
    
    dropdown.classList.toggle('show');
}

// Utility functions
function showLoading(show) {
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
