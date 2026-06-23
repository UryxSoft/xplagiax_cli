
// Global variables
let currentPage = 1;
let totalPages = 1;
let totalSessions = 0;
let sortField = 'created_at';
let sortDirection = 'desc';
let currentFilters = {};

// API endpoints
const API_BASE = '/sessions_bp/api/sessions';
const ENDPOINTS = {
    list: `${API_BASE}`,
    create: `${API_BASE}`,
    update: (id) => `${API_BASE}/${id}`,
    delete: (id) => `${API_BASE}/${id}`,
    details: (id) => `${API_BASE}/${id}/details`,
    participants: (id) => `${API_BASE}/${id}/participants`,
    submissions: (id) => `${API_BASE}/${id}/submissions`,
    analyze: (id) => `${API_BASE}/${id}/analyze`,
    export: `${API_BASE}/export`,
    stats: `${API_BASE}/stats`,
    professors: '/api/professors'
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadSessions();
    loadStats();
    loadProfessors();
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

    ['statusFilter', 'professorFilter', 'analysisFilter', 'dateFromFilter'].forEach(id => {
        document.getElementById(id).addEventListener('change', applyFilters);
    });

    // Modal close events
    document.getElementById('sessionModal').addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });

    document.getElementById('detailsModal').addEventListener('click', function(e) {
        if (e.target === this) closeDetailsModal();
    });

    // Date validation
    document.getElementById('sessionStartDate').addEventListener('change', validateDates);
    document.getElementById('sessionEndDate').addEventListener('change', validateDates);

    // Close dropdowns on outside click
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.actions-menu')) {
            document.querySelectorAll('.actions-dropdown.show').forEach(dropdown => {
                dropdown.classList.remove('show');
            });
        }
    });
}

function validateDates() {
    const startDate = document.getElementById('sessionStartDate').value;
    const endDate = document.getElementById('sessionEndDate').value;
    
    if (startDate && endDate && new Date(startDate) >= new Date(endDate)) {
        document.getElementById('sessionEndDate').setCustomValidity('La fecha de fin debe ser posterior a la fecha de inicio');
    } else {
        document.getElementById('sessionEndDate').setCustomValidity('');
    }
}

// Load sessions from API
async function loadSessions(page = 1) {
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
        
        displaySessions(data.sessions || []);
        updatePagination(data.pagination || {});
        updateTableStats(data.pagination || {});
        
        currentPage = page;
        
    } catch (error) {
        console.error('Error loading sessions:', error);
        showError('Error al cargar sesiones: ' + error.message);
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
        
        document.getElementById('totalSessions').textContent = stats.total || 0;
        document.getElementById('activeSessions').textContent = stats.active || 0;
        document.getElementById('totalParticipants').textContent = stats.participants || 0;
        document.getElementById('totalSubmissions').textContent = stats.submissions || 0;
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load professors for dropdown
async function loadProfessors() {
    try {
        const response = await fetch(ENDPOINTS.professors);
        const professors = await response.json();

        const professorSelect = document.getElementById('sessionProfessor');
        const professorFilter = document.getElementById('professorFilter');
        
        // Clear existing options (except default)
        professorSelect.querySelectorAll('option:not([value=""])').forEach(option => option.remove());
        professorFilter.querySelectorAll('option:not([value=""])').forEach(option => option.remove());

        professors.forEach(prof => {
            // Modal select
            const option1 = document.createElement('option');
            option1.value = prof.id;
            option1.textContent = `${prof.name} ${prof.lastname} (${prof.email})`;
            professorSelect.appendChild(option1);
            
            // Filter select
            const option2 = document.createElement('option');
            option2.value = prof.id;
            option2.textContent = `${prof.name} ${prof.lastname}`;
            professorFilter.appendChild(option2);
        });

    } catch (error) {
        console.error('Error loading professors:', error);
    }
}

// Display sessions in table
function displaySessions(sessions) {
    const tbody = document.getElementById('sessionsTableBody');
    
    if (sessions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center; padding: 40px; color: #6c757d;">
                    No se encontraron sesiones
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = sessions.map(session => `
        <tr>
            <td>
                <div style="font-weight: 500; color: #212529;">
                    ${session.name}
                </div>
            </td>
            <td>${session.professor_name || '-'}</td>
            <td>${formatDateTime(session.start_date)}</td>
            <td>${formatDateTime(session.end_date)}</td>
            <td>
                <span class="status-badge ${getSessionStatusClass(session)}">
                    ${getSessionStatusText(session)}
                </span>
            </td>
            <td>
                <span class="status-badge status-active">
                    ${session.participants_count || 0}
                </span>
            </td>
            <td>
                <span class="status-badge ${session.submissions_count > 0 ? 'status-active' : 'status-inactive'}">
                    ${session.submissions_count || 0}
                </span>
            </td>
            <td>
                <span class="status-badge ${getAnalysisStatusClass(session)}">
                    ${getAnalysisStatusText(session)}
                </span>
            </td>
            <td>
                <div class="actions-menu">
                    <button class="actions-btn" onclick="toggleActionDropdown(${session.id})">
                          <i class="bi bi-grid"></i> Opciones
                    </button>
                    <div class="actions-dropdown" id="dropdown-${session.id}">
                        <a href="#" class="dropdown-item" onclick="viewSessionDetails(${session.id})"><i class="bi bi-list-nested"></i> Ver Detalles</a>
                        <a href="#" class="dropdown-item" onclick="editSession(${session.id})"><i class="bi bi-pencil"></i> Editar</a>
                        <a href="#" class="dropdown-item" onclick="manageParticipants(${session.id})"><i class="bi bi-people"></i> Participantes</a>
                        <a href="#" class="dropdown-item" onclick="viewSubmissions(${session.id})"><i class="bi bi-send"></i> Entregas</a>
                        ${!session.analysis_completed ? 
                            `<a href="#" class="dropdown-item" onclick="startAnalysis(${session.id})"><i class="bi bi-search"></i> Iniciar Análisis</a>` :
                            '<a href="#" class="dropdown-item" onclick="viewAnalysisResults(' + session.id + ')"><i class="bi bi-activity"></i> Ver Análisis</a>'
                        }
                        <a href="#" class="dropdown-item danger" onclick="deleteSession(${session.id})"><i class="bi bi-trash"></i>  Eliminar</a>
                    </div>
                </div>
            </td>
        </tr>
    `).join('');
}

// Helper functions
function formatDateTime(dateString) {
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

function getSessionStatusClass(session) {
    const now = new Date();
    const start = new Date(session.start_date);
    const end = new Date(session.end_date);
    
    if (now < start) return 'status-pending';
    if (now >= start && now <= end) return 'status-active';
    return 'status-inactive';
}

function getSessionStatusText(session) {
    const now = new Date();
    const start = new Date(session.start_date);
    const end = new Date(session.end_date);
    
    if (now < start) return 'Próxima';
    if (now >= start && now <= end) return 'Activa';
    return 'Finalizada';
}

function getAnalysisStatusClass(session) {
    if (session.analysis_completed) return 'status-active';
    if (session.analysis_started) return 'status-pending';
    return 'status-inactive';
}

function getAnalysisStatusText(session) {
    if (session.analysis_completed) return 'Completado';
    if (session.analysis_started) return 'En Progreso';
    return 'Pendiente';
}

// Pagination functions (same pattern as previous screens)
function updatePagination(pagination) {
    totalPages = pagination.pages || 1;
    totalSessions = pagination.total || 0;
    
    const controls = document.getElementById('paginationControls');
    controls.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '← Anterior';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => loadSessions(currentPage - 1);
    controls.appendChild(prevBtn);

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
        const firstBtn = document.createElement('button');
        firstBtn.className = 'pagination-btn';
        firstBtn.textContent = '1';
        firstBtn.onclick = () => loadSessions(1);
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
        pageBtn.onclick = () => loadSessions(i);
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
        lastBtn.onclick = () => loadSessions(totalPages);
        controls.appendChild(lastBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = 'Siguiente →';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => loadSessions(currentPage + 1);
    controls.appendChild(nextBtn);
}

function updateTableStats(pagination) {
    const stats = document.getElementById('tableStats');
    const info = document.getElementById('paginationInfo');
    
    const start = ((pagination.page || 1) - 1) * (pagination.per_page || 20) + 1;
    const end = Math.min(start + (pagination.per_page || 20) - 1, pagination.total || 0);
    
    stats.textContent = `${pagination.total || 0} sesiones encontradas`;
    info.textContent = `Mostrando ${start} - ${end} de ${pagination.total || 0} sesiones`;
}

// Filter functions
function applyFilters() {
    const search = document.getElementById('searchInput').value.trim();
    const status = document.getElementById('statusFilter').value;
    const professor = document.getElementById('professorFilter').value;
    const analysis = document.getElementById('analysisFilter').value;
    const dateFrom = document.getElementById('dateFromFilter').value;

    currentFilters = {};
    
    if (search) currentFilters.search = search;
    if (status) currentFilters.status = status;
    if (professor) currentFilters.professor_id = professor;
    if (analysis) currentFilters.analysis_status = analysis;
    if (dateFrom) currentFilters.date_from = dateFrom;

    currentPage = 1;
    loadSessions(1);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('professorFilter').value = '';
    document.getElementById('analysisFilter').value = '';
    document.getElementById('dateFromFilter').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadSessions(1);
}

// Sort functions
function sortTable(field) {
    if (sortField === field) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        sortField = field;
        sortDirection = 'asc';
    }
    
    loadSessions(currentPage);
}

// Modal functions
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Nueva Sesión';
    document.getElementById('sessionForm').reset();
    document.getElementById('sessionId').value = '';
    
    // Set default dates (start: now, end: +1 week)
    const now = new Date();
    const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    
    document.getElementById('sessionStartDate').value = now.toISOString().slice(0, 16);
    document.getElementById('sessionEndDate').value = nextWeek.toISOString().slice(0, 16);
    
    document.getElementById('sessionModal').classList.add('show');
}

function closeModal() {
    document.getElementById('sessionModal').classList.remove('show');
}

function closeDetailsModal() {
    document.getElementById('detailsModal').classList.remove('show');
}

// CRUD operations continue in next part...
// [Continue with CRUD operations, session management functions, etc.]

// Utility functions
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('sessionsTable');
    
    if (show) {
        loading.style.display = 'block';
        table.style.display = 'none';
    } else {
        loading.style.display = 'none';
        table.style.display = 'table';
    }
}

function showSuccess(message) {
    alert('✅ ' + message);
}

function showError(message) {
    alert('❌ ' + message);
}

function showInfo(message) {
    alert('ℹ️ ' + message);
}

// Action dropdown functions
function toggleActionDropdown(sessionId) {
    const dropdown = document.getElementById(`dropdown-${sessionId}`);
    const allDropdowns = document.querySelectorAll('.actions-dropdown');
    
    allDropdowns.forEach(d => {
        if (d !== dropdown) d.classList.remove('show');
    });
    
    dropdown.classList.toggle('show');
}

// Session management functions - will continue with these...
async function saveSession() {
    // Implementation for saving sessions
}

async function editSession(sessionId) {
    // Implementation for editing sessions
}

async function deleteSession(sessionId) {
    // Implementation for deleting sessions
}

async function viewSessionDetails(sessionId) {
    // Implementation for viewing session details
}

async function startAnalysis(sessionId) {
    // Implementation for starting analysis
}

// Export function
async function exportSessions() {
    // Implementation for exporting sessions
}
