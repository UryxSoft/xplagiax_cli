// Global variables
let currentPage = 1;
let totalPages = 1;
let totalLanguages = 0;
let sortField = 'created_date';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints
const API_BASE = '/languages_bp/api/languages';
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
    loadLanguages();
    //loadStats();
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

    document.getElementById('codeFilter').addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            applyFilters();
        }, 500);
    });

    // Modal close events
    document.getElementById('languageModal').addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });

    // Language code input formatting
    document.getElementById('languageCode').addEventListener('input', function() {
        this.value = this.value.toLowerCase().replace(/[^a-z]/g, '');
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

// Load languages from API
async function loadLanguages(page = 1) {
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
        
        displayLanguages(data.languages || []);
        updatePagination(data.pagination || {});
        updateTableStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading languages:', error);
        showError('Error al cargar idiomas: ' + error.message);
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
        
        document.getElementById('totalLanguages').textContent = stats.total || 0;
        document.getElementById('documentsLinked').textContent = stats.documents_linked || 0;
        document.getElementById('mostUsed').textContent = stats.most_used || '-';
        document.getElementById('monthlyLanguages').textContent = stats.monthly || 0;
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Display languages in table
function displayLanguages(languages) {
    const tbody = document.getElementById('languagesTableBody');
    
    if (languages.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron idiomas
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = languages.map(lang => `
        <tr>
            <td>
                <div style="display: flex; align-items: center;">
                    <div style="width: 24px; height: 16px; border: 1px solid #ddd; border-radius: 2px; margin-right: 8px; background: linear-gradient(45deg, #f0f0f0 25%, transparent 25%), linear-gradient(-45deg, #f0f0f0 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #f0f0f0 75%), linear-gradient(-45deg, transparent 75%, #f0f0f0 75%); background-size: 4px 4px; background-position: 0 0, 0 2px, 2px -2px, -2px 0px;"></div>
                    <div>
                        <div style="font-weight: 500; color: #212529;">
                            ${lang.lenguage_name}
                        </div>
                    </div>
                </div>
            </td>
            <td>
                <span style="background: #e9ecef; padding: 2px 8px; border-radius: 12px; font-family: monospace; font-weight: 500;">
                    ${lang.lenguage}
                </span>
            </td>
            <td>${formatDate(lang.created_date)}</td>
            <td>
                <span class="status-badge status-active">
                    ${lang.documents_count || 0} docs
                </span>
            </td>
            <td>
                <div style="width: 100px; background: #f8f9fa; border-radius: 4px; height: 8px; position: relative;">
                    <div style="background: #1976d2; height: 100%; border-radius: 4px; width: ${Math.min((lang.documents_count || 0) / Math.max(languages.reduce((max, l) => Math.max(max, l.documents_count || 0), 1), 1) * 100, 100)}%;"></div>
                </div>
                <div style="font-size: 11px; color: #6c757d; margin-top: 2px;">
                    ${((lang.documents_count || 0) / Math.max(languages.reduce((sum, l) => sum + (l.documents_count || 0), 0), 1) * 100).toFixed(1)}%
                </div>
            </td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActionDropdown(${lang.id})">
                          <i class="bi bi-grid"></i> Opciones
                    </button>
                    <div class="actions-dropdown" id="dropdown-${lang.id}">
                        <a href="#" class="dropdown-item" onclick="editLanguage(${lang.id})"><i class="bi bi-pencil"></i>  Editar</a>
                        <a href="#" class="dropdown-item" onclick="viewDocuments(${lang.id})"><i class="bi bi-file-earmark-richtext"></i> Ver Documentos</a>
                        ${lang.documents_count > 0 ? 
                            '<a href="#" class="dropdown-item" style="color: #6c757d; cursor: not-allowed;">No se puede eliminar</a>' :
                            `<a href="#" class="dropdown-item danger" onclick="deleteLanguage(${lang.id})"><i class="bi bi-trash"></i>  Eliminar</a>`
                        }
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
    totalLanguages = pagination.total || 0;
    
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => loadLanguages(currentPage - 1);
    controls.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => loadLanguages(1);
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
        pageBtn.onclick = () => loadLanguages(i);
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
        lastBtn.onclick = () => loadLanguages(totalPages);
        controls.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Siguiente →';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadLanguages(currentPage + 1);
    controls.appendChild(nextBtn);
}

function updateTableStats(pagination) {
    const stats = document.getElementById('tableStats');
    const info = document.getElementById('paginationInfo');
    
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 20) + 1;
    const end = Math.min(start + (pagination.per_page || 20) - 1, pagination.total || 0);
    
    stats.textContent = `${pagination.total || 0} idiomas encontrados`;
    info.textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0} idiomas`;
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const code = document.getElementById('codeFilter').value.trim();

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (code) currentFilters.code = code;

    currentPage = 1;
    loadLanguages(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('codeFilter').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadLanguages(1);
}

// Sort functions
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    loadLanguages(currentPage);
}

// Modal functions
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Nuevo Idioma';
    document.getElementById('languageForm').reset();
    document.getElementById('languageId').value = '';
    document.getElementById('languageModal').classList.add('show');
}

function closeModal() {
    document.getElementById('languageModal').classList.remove('show');
}

// CRUD operations
async function saveLanguage() {
    try {
        const formData = {
            lenguage_name: document.getElementById('languageName').value.trim(),
            lenguage: document.getElementById('languageCode').value.trim().toLowerCase()
        };

        // Validation
        if (!formData.lenguage_name) {
            showError('El nombre del idioma es requerido');
            return;
        }

        if (!formData.lenguage || formData.lenguage.length !== 2) {
            showError('El código ISO debe tener exactamente 2 letras');
            return;
        }

        const languageId = document.getElementById('languageId').value;
        const isEdit = !!languageId;

        const url = isEdit ? ENDPOINTS.update(languageId) : ENDPOINTS.create;
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
            throw new Error(error.message || 'Error al guardar idioma');
        }

        closeModal();
        loadLanguages(currentPage);
        //loadStats();
        showSuccess(isEdit ? 'Idioma actualizado correctamente' : 'Idioma creado correctamente');

    } catch (error) {
        console.error('Error saving language:', error);
        showError('Error al guardar idioma: ' + error.message);
    }
}

async function editLanguage(languageId) {
    try {
        const response = await fetch(ENDPOINTS.update(languageId));
        
        if (!response.ok) {
            throw new Error('Error al cargar datos del idioma');
        }
        
        const language = await response.json();
        
        document.getElementById('modalTitle').textContent = 'Editar Idioma';
        document.getElementById('languageId').value = language.id;
        document.getElementById('languageName').value = language.lenguage_name || '';
        document.getElementById('languageCode').value = language.lenguage || '';
        
        document.getElementById('languageModal').classList.add('show');
        
    } catch (error) {
        console.error('Error loading language:', error);
        showError('Error al cargar datos del idioma: ' + error.message);
    }
}

async function deleteLanguage(languageId) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer. ¿Deseas eliminar este idioma?',
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
        const response = await fetch(ENDPOINTS.delete(languageId), {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al eliminar idioma');
        }

        loadLanguages(currentPage);
        //loadStats();
        showSuccess('Idioma eliminado correctamente');

    } catch (error) {
        console.error('Error deleting language:', error);
        showError('Error al eliminar idioma: ' + error.message);
    }
}

function viewDocuments(languageId) {
    // Navigate to documents page with language filter
    window.location.href = `/documents?language=${languageId}`;
}

// Export function
async function exportLanguages() {
    try {
        const response = await fetch(ENDPOINTS.export);
        
        if (!response.ok) {
            throw new Error('Error al exportar idiomas');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `idiomas_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess('Idiomas exportados correctamente');

    } catch (error) {
        console.error('Error exporting languages:', error);
        showError('Error al exportar idiomas: ' + error.message);
    }
}

// Action dropdown functions
function toggleActionDropdown(languageId) {
    const dropdown = document.getElementById(`dropdown-${languageId}`);
    const allDropdowns = document.querySelectorAll('.actions-dropdown');
    
    allDropdowns.forEach(d => {
        if (d !== dropdown) d.classList.remove('show');
    });
    
    dropdown.classList.toggle('show');
}

// Utility functions
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('languagesTable');
    
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
