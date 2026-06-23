// Global variables
let currentPage = 1;
let totalPages = 1;
let totalDocuments = 0;
let sortField = 'created_date';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints
const API_BASE = '/documents_bp/api/documents';
const ENDPOINTS = {
    list: `${API_BASE}`,
    create: `${API_BASE}`,
    update: (id) => `${API_BASE}/${id}`,
    delete: (id) => `${API_BASE}/${id}`,
    export: `${API_BASE}/export`,
    stats: `${API_BASE}/stats`,
    doctypes: '/documents_bp/api/doctypes',        // ✅ Correcto
    countries: '/documents_bp/api/countries',      // ✅ Correcto
    institutions: '/documents_bp/api/institutions', // ✅ Correcto
    languages: '/documents_bp/api/languages'       // ✅ Correcto
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadDocuments();
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

    ['doctypeFilter', 'countryFilter', 'institutionFilter', 'languageFilter', 'dateFromFilter'].forEach(id => {
        document.getElementById(id).addEventListener('change', applyFilters);
    });

    // Modal close events
    document.getElementById('documentModal').addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });

    document.getElementById('contentModal').addEventListener('click', function(e) {
        if (e.target === this) closeContentModal();
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

// Load documents from API
async function loadDocuments(page = 1) {
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
        
        displayDocuments(data.documents || []);
        updatePagination(data.pagination || {});
        updateTableStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading documents:', error);
        showError('Error al cargar documentos: ' + error.message);
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
        
        document.getElementById('totalDocuments').textContent = stats.total || 0;
        document.getElementById('monthlyDocuments').textContent = stats.monthly || 0;
        document.getElementById('analyzedDocuments').textContent = stats.analyzed || 0;
        document.getElementById('totalSize').textContent = formatFileSize(stats.total_size || 0);
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// ✅ CORRECTO - Con manejo de errores
async function loadFilterOptions() {
    try {
        const requests = [
            fetch(ENDPOINTS.doctypes),
            fetch(ENDPOINTS.countries),
            fetch(ENDPOINTS.institutions),
            fetch(ENDPOINTS.languages)
        ];

        const responses = await Promise.all(requests);
        
        // Verificar que todas las respuestas sean exitosas
        for (let i = 0; i < responses.length; i++) {
            if (!responses[i].ok) {
                console.error(`Error loading filter option ${i}: ${responses[i].status}`);
                return;
            }
        }

        const [doctypes, countries, institutions, languages] = await Promise.all(
            responses.map(r => r.json())
        );

        populateSelect('doctypeFilter', doctypes, 'doctype');
        populateSelect('countryFilter', countries, 'country');
        populateSelect('institutionFilter', institutions, 'institution');
        populateSelect('languageFilter', languages, 'lenguage_name');

        // También poblar los selects del modal
        populateSelect('documentDoctype', doctypes, 'doctype');
        populateSelect('documentCountry', countries, 'country');
        populateSelect('documentInstitution', institutions, 'institution');
        populateSelect('documentLanguage', languages, 'lenguage_name');

    } catch (error) {
        console.error('Error loading filter options:', error);
        showError('Error al cargar opciones de filtro');
    }
}

function populateSelect(selectId, options, textField) {
    const select = document.getElementById(selectId);
    
    if (!select) {
        console.error(`Select element with id '${selectId}' not found`);
        return;
    }

    if (!Array.isArray(options)) {
        console.error(`Options for ${selectId} is not an array:`, options);
        return;
    }

    // Remover opciones existentes (excepto la primera opción vacía)
    const currentOptions = select.querySelectorAll('option:not([value=""])');
    currentOptions.forEach(option => option.remove());

    // Agregar nuevas opciones
    options.forEach(option => {
        if (!option || typeof option !== 'object') {
            console.warn(`Invalid option for ${selectId}:`, option);
            return;
        }

        const optionElement = document.createElement('option');
        optionElement.value = option.id || '';
        optionElement.textContent = option[textField] || 'Sin nombre';
        select.appendChild(optionElement);
    });

    console.log(`Populated ${selectId} with ${options.length} options`);
}


// Display documents in table
function displayDocuments(documents) {
    const tbody = document.getElementById('documentsTableBody');
    
    if (documents.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron documentos
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = documents.map(doc => `
        <tr>
            <td>
                <div style="max-width: 200px;">
                    <div style="font-weight: 500; color: #212529; margin-bottom: 4px;">
                        ${truncateText(doc.title || 'Sin título', 50)}
                    </div>
                    ${doc.content ? `<button class="btn-link" onclick="viewContent(${doc.id}, '${escapeHtml(doc.title || 'Sin título')}')">Ver contenido</button>` : ''}
                </div>
            </td>
            <td>${doc.author || '-'}</td>
            <td>${doc.doctype_name || '-'}</td>
            <td>${doc.theme || '-'}</td>
            <td>${doc.institution_name || '-'}</td>
            <td>${doc.country_name || '-'}</td>
            <td>${doc.language_name || '-'}</td>
            <td>${formatDate(doc.created_date)}</td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActionDropdown(${doc.id})">
                       <i class="bi bi-grid"></i> Opciones
                    </button>
                    <div class="actions-dropdown" id="dropdown-${doc.id}">
                        <a href="#" class="dropdown-item" onclick="editDocument(${doc.id})"><i class="bi bi-pencil"></i> Editar</a>
                        <a href="#" class="dropdown-item" onclick="viewContent(${doc.id}, '${escapeHtml(doc.title || 'Sin título')}')"><i class="bi bi-card-text"></i> Ver Contenido</a>
                        <a href="#" class="dropdown-item" onclick="analyzeDocument(${doc.id})"><i class="bi bi-graph-up"></i> Analizar</a>
                        <a href="#" class="dropdown-item danger" onclick="deleteDocument(${doc.id})"><i class="bi bi-trash"></i> Eliminar</a>
                    </div>
                </div>
            </td>
        </tr>
    `).join('');
}

// Helper functions
function truncateText(text, maxLength) {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/'/g, '&apos;');
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

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Pagination functions (same as users)
function updatePagination(pagination) {
    totalPages = pagination.pages || 1;
    totalDocuments = pagination.total || 0;
    
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => loadDocuments(currentPage - 1);
    controls.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => loadDocuments(1);
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
        pageBtn.onclick = () => loadDocuments(i);
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
        lastBtn.onclick = () => loadDocuments(totalPages);
        controls.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Siguiente →';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadDocuments(currentPage + 1);
    controls.appendChild(nextBtn);
}

function updateTableStats(pagination) {
    const stats = document.getElementById('tableStats');
    const info = document.getElementById('paginationInfo');
    
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 20) + 1;
    const end = Math.min(start + (pagination.per_page || 20) - 1, pagination.total || 0);
    
    stats.textContent = `${pagination.total || 0} documentos encontrados`;
    info.textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0} documentos`;
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const doctype = document.getElementById('doctypeFilter').value;
    const country = document.getElementById('countryFilter').value;
    const institution = document.getElementById('institutionFilter').value;
    const language = document.getElementById('languageFilter').value;
    const dateFrom = document.getElementById('dateFromFilter').value;

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (doctype) currentFilters.doctype_id = doctype;
    if (country) currentFilters.country_id = country;
    if (institution) currentFilters.institution_id = institution;
    if (language) currentFilters.lenguage_id = language;
    if (dateFrom) currentFilters.date_from = dateFrom;

    currentPage = 1;
    loadDocuments(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('doctypeFilter').value = '';
    document.getElementById('countryFilter').value = '';
    document.getElementById('institutionFilter').value = '';
    document.getElementById('languageFilter').value = '';
    document.getElementById('dateFromFilter').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadDocuments(1);
}

// Sort functions
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    loadDocuments(currentPage);
}

// Modal functions
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Nuevo Documento';
    document.getElementById('documentForm').reset();
    document.getElementById('documentId').value = '';
    document.getElementById('documentModal').classList.add('show');
}

function closeModal() {
    document.getElementById('documentModal').classList.remove('show');
}

function closeContentModal() {
    document.getElementById('contentModal').classList.remove('show');
}

// CRUD operations
async function saveDocument() {
    try {
        const formData = {
            title: document.getElementById('documentTitle').value.trim(),
            author: document.getElementById('documentAuthor').value.trim(),
            content: document.getElementById('documentContent').value.trim(),
            rena: document.getElementById('documentRena').value.trim(),
            theme: document.getElementById('documentTheme').value.trim(),
            doctype_id: document.getElementById('documentDoctype').value || null,
            country_id: document.getElementById('documentCountry').value || null,
            institution_id: document.getElementById('documentInstitution').value || null,
            lenguage_id: document.getElementById('documentLanguage').value || null
        };

        const documentId = document.getElementById('documentId').value;
        const isEdit = !!documentId;

        const url = isEdit ? ENDPOINTS.update(documentId) : ENDPOINTS.create;
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
            throw new Error(error.message || 'Error al guardar documento');
        }

        closeModal();
        loadDocuments(currentPage);
        loadStats();
        showSuccess(isEdit ? 'Documento actualizado correctamente' : 'Documento creado correctamente');

    } catch (error) {
        console.error('Error saving document:', error);
        showError('Error al guardar documento: ' + error.message);
    }
}

async function editDocument(documentId) {
    try {
        const response = await fetch(ENDPOINTS.update(documentId));
        
        if (!response.ok) {
            throw new Error('Error al cargar datos del documento');
        }
        
        const doc = await response.json();
        
        document.getElementById('modalTitle').textContent = 'Editar Documento';
        document.getElementById('documentId').value = doc.id;
        document.getElementById('documentTitle').value = doc.title || '';
        document.getElementById('documentAuthor').value = doc.author || '';
        document.getElementById('documentContent').value = doc.content || '';
        document.getElementById('documentRena').value = doc.rena || '';
        document.getElementById('documentTheme').value = doc.theme || '';
        document.getElementById('documentDoctype').value = doc.doctype_id || '';
        document.getElementById('documentCountry').value = doc.country_id || '';
        document.getElementById('documentInstitution').value = doc.institution_id || '';
        document.getElementById('documentLanguage').value = doc.lenguage_id || '';
        
        document.getElementById('documentModal').classList.add('show');
        
    } catch (error) {
        console.error('Error loading document:', error);
        showError('Error al cargar datos del documento: ' + error.message);
    }
}

async function deleteDocument(documentId) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: 'Esta acción no se puede deshacer. ¿Deseas eliminar esta documento?',
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
        const response = await fetch(ENDPOINTS.delete(documentId), {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al eliminar documento');
        }

        loadDocuments(currentPage);
        loadStats();
        showSuccess('Documento eliminado correctamente');

    } catch (error) {
        console.error('Error deleting document:', error);
        showError('Error al eliminar documento: ' + error.message);
    }
}

async function viewContent(documentId, title) {
    try {
        const response = await fetch(ENDPOINTS.update(documentId));
        
        if (!response.ok) {
            throw new Error('Error al cargar contenido del documento');
        }
        
        const doc = await response.json();
        
        document.getElementById('contentModalTitle').textContent = title;
        document.getElementById('documentContentPreview').textContent = doc.content || 'Sin contenido disponible';
        document.getElementById('contentModal').classList.add('show');
        
    } catch (error) {
        console.error('Error loading document content:', error);
        showError('Error al cargar contenido del documento: ' + error.message);
    }
}

async function analyzeDocument(documentId) {
    try {
        const response = await fetch(`${API_BASE}/${documentId}/analyze`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Error al analizar documento');
        }

        showSuccess('Análisis iniciado correctamente');

    } catch (error) {
        console.error('Error analyzing document:', error);
        showError('Error al analizar documento: ' + error.message);
    }
}

// Export function
async function exportDocuments() {
    try {
        const response = await fetch(ENDPOINTS.export);
        
        if (!response.ok) {
            throw new Error('Error al exportar documentos');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `documentos_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showSuccess('Documentos exportados correctamente');

    } catch (error) {
        console.error('Error exporting documents:', error);
        showError('Error al exportar documentos: ' + error.message);
    }
}

// Action dropdown functions
function toggleActionDropdown(documentId) {
    const dropdown = document.getElementById(`dropdown-${documentId}`);
    const allDropdowns = document.querySelectorAll('.actions-dropdown');
    
    allDropdowns.forEach(d => {
        if (d !== dropdown) d.classList.remove('show');
    });
    
    dropdown.classList.toggle('show');
}

// Utility functions
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('documentsTable');
    
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
