// Global variables
let currentPage = 1;
let totalPages = 1;
let totalTypes = 0;
let sortField = 'created_date';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints
const API_BASE = '/institution_types_bp/api/institution_types';
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
    loadInstitutionTypes();
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
    document.getElementById('institutionTypeModal').addEventListener('click', function(e) {
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

// Load institution types from API
async function loadInstitutionTypes(page = 1) {
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
        
        displayInstitutionTypes(data.institution_types || []);
        updatePagination(data.pagination || {});
        updateTableStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading institution types:', error);
        showError('Error al cargar tipos de institución: ' + error.message);
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
        
        document.getElementById('totalTypes').textContent = stats.total || 0;
        document.getElementById('monthlyTypes').textContent = stats.monthly || 0;
        document.getElementById('activeTypes').textContent = stats.active || 0;
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Display institution types in table
function displayInstitutionTypes(institutionTypes) {
    const tbody = document.getElementById('institutionTypesTableBody');
    
    if (institutionTypes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron tipos de institución
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = institutionTypes.map(type => `
        <tr>
            <td>${type.id}</td>
            <td>
                <div style="font-weight: 500; color: #212529;">
                    ${type.institution_type || 'Sin nombre'}
                </div>
            </td>
            <td>${formatDate(type.created_date)}</td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActionDropdown(${type.id})">
                          <i class="bi bi-grid"></i> Opciones
                    </button>
                    <div class="actions-dropdown" id="dropdown-${type.id}">
                        <a href="#" class="dropdown-item" onclick="editInstitutionType(${type.id})"><i class="bi bi-pencil"></i> Editar</a>
                        <a href="#" class="dropdown-item danger" onclick="deleteInstitutionType(${type.id})"><i class="bi bi-trash"></i> Eliminar</a>
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
    totalTypes = pagination.total || 0;
    
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => loadInstitutionTypes(currentPage - 1);
    controls.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => loadInstitutionTypes(1);
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
        pageBtn.onclick = () => loadInstitutionTypes(i);
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
        lastBtn.onclick = () => loadInstitutionTypes(totalPages);
        controls.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Siguiente →';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadInstitutionTypes(currentPage + 1);
    controls.appendChild(nextBtn);
}

function updateTableStats(pagination) {
    const stats = document.getElementById('tableStats');
    const info = document.getElementById('paginationInfo');
    
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 20) + 1;
    const end = Math.min(start + (pagination.per_page || 20) - 1, pagination.total || 0);
    
    stats.textContent = `${pagination.total || 0} tipos encontrados`;
    info.textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0} tipos`;
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const dateFrom = document.getElementById('dateFromFilter').value;

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (dateFrom) currentFilters.date_from = dateFrom;

    currentPage = 1;
    loadInstitutionTypes(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('dateFromFilter').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadInstitutionTypes(1);
}

// Sort functions
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    loadInstitutionTypes(currentPage);
}

// Modal functions
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Nuevo Tipo de Institución';
    document.getElementById('institutionTypeForm').reset();
    document.getElementById('institutionTypeId').value = '';
    document.getElementById('institutionTypeModal').classList.add('show');
}

function closeModal() {
    document.getElementById('institutionTypeModal').classList.remove('show');
}

// CRUD operations
async function saveInstitutionType() {
    try {
        const formData = {
            institution_type: document.getElementById('institutionTypeName').value.trim()
        };

        if (!formData.institution_type) {
            showError('El nombre del tipo de institución es requerido');
            return;
        }

        const institutionTypeId = document.getElementById('institutionTypeId').value;
        const isEdit = !!institutionTypeId;

        const url = isEdit ? ENDPOINTS.update(institutionTypeId) : ENDPOINTS.create;
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
            throw new Error(error.message || 'Error al guardar tipo de institución');
        }

        closeModal();
        loadInstitutionTypes(currentPage);
        loadStats();
        showSuccess(isEdit ? 'Tipo de institución actualizado correctamente' : 'Tipo de institución creado correctamente');

    } catch (error) {
        console.error('Error saving institution type:', error);
        showError('Error al guardar tipo de institución: ' + error.message);
    }
}

async function editInstitutionType(institutionTypeId) {
    try {
        const response = await fetch(ENDPOINTS.update(institutionTypeId));
        
        if (!response.ok) {
            throw new Error('Error al cargar datos del tipo de institución');
        }
        
        const institutionType = await response.json();
        
        document.getElementById('modalTitle').textContent = 'Editar Tipo de Institución';
        document.getElementById('institutionTypeId').value = institutionType.id;
        document.getElementById('institutionTypeName').value = institutionType.institution_type || '';
        
        document.getElementById('institutionTypeModal').classList.add('show');
        
    } catch (error) {
        console.error('Error loading institution type:', error);
        showError('Error al cargar datos del tipo de institución: ' + error.message);
    }
}

async function deleteInstitutionType(institutionTypeId) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer. ¿Deseas eliminar este tipo de institución?',
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
        const response = await fetch(ENDPOINTS.delete(institutionTypeId), {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al eliminar tipo de institución');
        }

        loadInstitutionTypes(currentPage);
        loadStats();
        showSuccess('Tipo de institución eliminado correctamente');

    } catch (error) {
        console.error('Error deleting institution type:', error);
        showError('Error al eliminar tipo de institución: ' + error.message);
    }
}

// Export function
async function exportInstitutionTypes() {
    try {
        const response = await fetch(ENDPOINTS.export);
        
        if (!response.ok) {
            throw new Error('Error al exportar tipos de institución');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tipos_institucion_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess('Tipos de institución exportados correctamente');

    } catch (error) {
        console.error('Error exporting institution types:', error);
        showError('Error al exportar tipos de institución: ' + error.message);
    }
}

// Action dropdown functions
function toggleActionDropdown(institutionTypeId) {
    const dropdown = document.getElementById(`dropdown-${institutionTypeId}`);
    const allDropdowns = document.querySelectorAll('.actions-dropdown');
    
    allDropdowns.forEach(d => {
        if (d !== dropdown) d.classList.remove('show');
    });
    
    dropdown.classList.toggle('show');
}

// Utility functions
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('institutionTypesTable');
    
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
