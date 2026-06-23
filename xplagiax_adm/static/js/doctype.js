// Global variables
let currentPage = 1;
let totalPages = 1;
let totalTypes = 0;
let sortField = 'created_date';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints
const API_BASE = '/doctype_bp/api/doctypes';
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
    loadDoctypes();
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
    document.getElementById('doctypeModal').addEventListener('click', function(e) {
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

    // Character counter for doctype field
    document.getElementById('doctypeName').addEventListener('input', function() {
        const value = this.value.toUpperCase();
        this.value = value.slice(0, 4); // Limit to 4 characters
    });
}

// Load doctypes from API
async function loadDoctypes(page = 1) {
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
        
        displayDoctypes(data.doctypes || []);
        updatePagination(data.pagination || {});
        updateTableStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading doctypes:', error);
        showError('Error al cargar tipos de documento: ' + error.message);
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

// Display doctypes in table
function displayDoctypes(doctypes) {
    const tbody = document.getElementById('doctypesTableBody');
    
    if (doctypes.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron tipos de documento
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = doctypes.map(type => `
        <tr>
            <td>${type.id}</td>
            <td>
                <div style="font-weight: 500; color: #212529;">
                    <span class="badge" style="background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                        ${type.doctype || 'N/A'}
                    </span>
                </div>
            </td>
            <td>${formatDate(type.created_date)}</td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActionDropdown(${type.id})">
                          <i class="bi bi-grid"></i> Opciones
                    </button>
                    <div class="actions-dropdown" id="dropdown-${type.id}">
                        <a href="#" class="dropdown-item" onclick="editDoctype(${type.id})"><i class="bi bi-pencil"></i>  Editar</a>
                        <a href="#" class="dropdown-item danger" onclick="deleteDoctype(${type.id})"><i class="bi bi-trash"></i>  Eliminar</a>
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
    prevBtn.onclick = () => loadDoctypes(currentPage - 1);
    controls.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => loadDoctypes(1);
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
        pageBtn.onclick = () => loadDoctypes(i);
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
        lastBtn.onclick = () => loadDoctypes(totalPages);
        controls.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Siguiente →';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadDoctypes(currentPage + 1);
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
    loadDoctypes(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('dateFromFilter').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadDoctypes(1);
}

// Sort functions
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    loadDoctypes(currentPage);
}

// Modal functions
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Nuevo Tipo de Documento';
    document.getElementById('doctypeForm').reset();
    document.getElementById('doctypeId').value = '';
    document.getElementById('doctypeModal').classList.add('show');
    document.getElementById('doctypeName').focus();
}

function closeModal() {
    document.getElementById('doctypeModal').classList.remove('show');
}

// CRUD operations
async function saveDoctype() {
    try {
        const formData = {
            doctype: document.getElementById('doctypeName').value.trim().toUpperCase()
        };

        if (!formData.doctype) {
            showError('El tipo de documento es requerido');
            return;
        }

        if (formData.doctype.length > 4) {
            showError('El tipo de documento no puede tener más de 4 caracteres');
            return;
        }

        const doctypeId = document.getElementById('doctypeId').value;
        const isEdit = !!doctypeId;

        const url = isEdit ? ENDPOINTS.update(doctypeId) : ENDPOINTS.create;
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
            throw new Error(error.error || 'Error al guardar tipo de documento');
        }

        closeModal();
        loadDoctypes(currentPage);
        loadStats();
        showSuccess(isEdit ? 'Tipo de documento actualizado correctamente' : 'Tipo de documento creado correctamente');

    } catch (error) {
        console.error('Error saving doctype:', error);
        showError('Error al guardar tipo de documento: ' + error.message);
    }
}

async function editDoctype(doctypeId) {
    try {
        const response = await fetch(ENDPOINTS.update(doctypeId));
        
        if (!response.ok) {
            throw new Error('Error al cargar datos del tipo de documento');
        }
        
        const doctype = await response.json();
        
        document.getElementById('modalTitle').textContent = 'Editar Tipo de Documento';
        document.getElementById('doctypeId').value = doctype.id;
        document.getElementById('doctypeName').value = doctype.doctype || '';
        
        document.getElementById('doctypeModal').classList.add('show');
        document.getElementById('doctypeName').focus();
        
    } catch (error) {
        console.error('Error loading doctype:', error);
        showError('Error al cargar datos del tipo de documento: ' + error.message);
    }
}

async function deleteDoctype(doctypeId) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer. ¿Deseas eliminar este tipo de documento?',
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
        const response = await fetch(ENDPOINTS.delete(doctypeId), {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error al eliminar tipo de documento');
        }

        loadDoctypes(currentPage);
        loadStats();
        showSuccess('Tipo de documento eliminado correctamente');

    } catch (error) {
        console.error('Error deleting doctype:', error);
        showError('Error al eliminar tipo de documento: ' + error.message);
    }
}

// Export function
async function exportDoctypes() {
    try {
        const response = await fetch(ENDPOINTS.export);
        
        if (!response.ok) {
            throw new Error('Error al exportar tipos de documento');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tipos_documento_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess('Tipos de documento exportados correctamente');

    } catch (error) {
        console.error('Error exporting doctypes:', error);
        showError('Error al exportar tipos de documento: ' + error.message);
    }
}

// Action dropdown functions
function toggleActionDropdown(doctypeId) {
    const dropdown = document.getElementById(`dropdown-${doctypeId}`);
    const allDropdowns = document.querySelectorAll('.actions-dropdown');
    
    allDropdowns.forEach(d => {
        if (d !== dropdown) d.classList.remove('show');
    });
    
    dropdown.classList.toggle('show');
}

// Utility functions
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('doctypesTable');
    
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
