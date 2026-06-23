// Variables globales
let autoRefreshInterval = null;
let currentRefreshRate = 60; // segundos
let selectedContainer = null;
let pendingAction = null;

// Configuración de contenedores
const CONTAINER_ICONS = {
    'qdrant': 'bi-search',
    'mysql': 'bi-database',
    'redis-server': 'bi-lightning',
    'minio': 'bi-archive',
    'elasticsearch-server': 'bi-search',
    'clamav': 'bi-shield-check'
};

const CONTAINER_COLORS = {
    'qdrant': '#6366f1',
    'mysql': '#f59e0b',
    'redis-server': '#ef4444',
    'minio': '#06b6d4',
    'elasticsearch-server': '#8b5cf6',
    'clamav': '#10b981'
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    loadContainersStatus();
    updateLastUpdateTime();
    
    // Configurar auto-refresh por defecto
    document.getElementById('autoRefreshToggle').checked = true;
    startAutoRefresh();
});

// Función principal para cargar estado de contenedores
async function loadContainersStatus() {
    try {
        showLoading(true);
        
        const response = await fetch('/containers_bp/api/containers/status');
        const data = await response.json();
        
        if (response.ok) {
            updateSystemStats(data);
            renderContainersGrid(data.containers);
            updateLastUpdateTime();
        } else {
            showError('Error al cargar estado de contenedores: ' + data.error);
        }
    } catch (error) {
        showError('Error de conexión: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Actualizar estadísticas del sistema
function updateSystemStats(data) {
    document.getElementById('totalContainers').textContent = data.total_containers;
    document.getElementById('runningContainers').textContent = data.running_containers;
    document.getElementById('stoppedContainers').textContent = data.stopped_containers;
    document.getElementById('missingContainers').textContent = data.missing_containers;
}

// Renderizar grid de contenedores
function renderContainersGrid(containers) {
    const grid = document.getElementById('containersGrid');
    grid.innerHTML = '';
    
    containers.forEach(container => {
        const card = createContainerCard(container);
        grid.appendChild(card);
    });
}

// Crear card de contenedor
function createContainerCard(container) {
    const card = document.createElement('div');
    card.className = `container-card ${getStatusClass(container.status)}`;
    card.setAttribute('data-container', container.key);
    
    const icon = CONTAINER_ICONS[container.key] || 'bi-box-seam';
    const color =// Continuación desde donde se cortó el archivo...

CONTAINER_COLORS[container.key] || '#6b7280';
    
    const statusInfo = getStatusInfo(container);
    const resourceInfo = getResourceInfo(container);
    
    card.innerHTML = `
        <div class="container-card-header">
            <div class="container-info">
                <div class="container-icon" style="background-color: ${color}20; color: ${color};">
                    <i class="${icon}"></i>
                </div>
                <div class="container-meta">
                    <h3 class="container-name">${container.name}</h3>
                    <p class="container-description">${container.description}</p>
                </div>
            </div>
            <div class="container-status">
                <span class="status-badge status-${container.status}">
                    <i class="${statusInfo.icon}"></i>
                    ${statusInfo.text}
                </span>
            </div>
        </div>
        
        <div class="container-card-body">
            <div class="container-details-summary">
                <div class="detail-item">
                    <span class="detail-label">Puerto:</span>
                    <span class="detail-value">${container.port}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Imagen:</span>
                    <span class="detail-value">${container.image}</span>
                </div>
                ${container.running ? `
                    <div class="detail-item">
                        <span class="detail-label">Uptime:</span>
                        <span class="detail-value">${container.details.uptime || 'N/A'}</span>
                    </div>
                ` : ''}
            </div>
            
            ${container.running ? `
                <div class="resource-usage">
                    <div class="resource-item">
                        <span class="resource-label">CPU:</span>
                        <div class="resource-bar">
                            <div class="resource-fill" style="width: ${container.details.cpu_usage || 0}%"></div>
                        </div>
                        <span class="resource-value">${container.details.cpu_usage || 0}%</span>
                    </div>
                    <div class="resource-item">
                        <span class="resource-label">RAM:</span>
                        <div class="resource-bar">
                            <div class="resource-fill" style="width: ${container.details.memory_usage || 0}%"></div>
                        </div>
                        <span class="resource-value">${container.details.memory_usage || 0}%</span>
                    </div>
                </div>
            ` : ''}
        </div>
        
        <div class="container-card-footer">
            <div class="container-actions">
                <button class="btn btn-sm btn-info" onclick="showContainerDetails('${container.key}')" 
                        title="Ver detalles">
                    <i class="bi bi-info-circle"></i>
                </button>
                <button class="btn btn-sm btn-secondary" onclick="showContainerLogs('${container.key}')" 
                        title="Ver logs">
                    <i class="bi bi-file-text"></i>
                </button>
                ${getActionButtons(container)}
            </div>
        </div>
    `;
    
    return card;
}

// Obtener información de estado
function getStatusInfo(container) {
    const statusMap = {
        'running': { icon: 'bi-play-circle-fill', text: 'En Ejecución', class: 'running' },
        'exited': { icon: 'bi-stop-circle-fill', text: 'Detenido', class: 'stopped' },
        'stopped': { icon: 'bi-stop-circle-fill', text: 'Detenido', class: 'stopped' },
        'not_found': { icon: 'bi-exclamation-triangle-fill', text: 'No Encontrado', class: 'missing' },
        'error': { icon: 'bi-x-circle-fill', text: 'Error', class: 'error' }
    };
    
    return statusMap[container.status] || { icon: 'bi-question-circle-fill', text: 'Desconocido', class: 'unknown' };
}

// Obtener información de recursos
function getResourceInfo(container) {
    if (!container.running || !container.details) {
        return { cpu: 0, memory: 0, network: { rx: 0, tx: 0 } };
    }
    
    return {
        cpu: container.details.cpu_usage || 0,
        memory: container.details.memory_usage || 0,
        network: {
            rx: container.details.network_rx_mb || 0,
            tx: container.details.network_tx_mb || 0
        }
    };
}

// Obtener clase de estado
function getStatusClass(status) {
    const classMap = {
        'running': 'status-running',
        'exited': 'status-stopped',
        'stopped': 'status-stopped',
        'not_found': 'status-missing',
        'error': 'status-error'
    };
    
    return classMap[status] || 'status-unknown';
}

// Obtener botones de acción
function getActionButtons(container) {
    if (container.status === 'not_found') {
        return `
            <button class="btn btn-sm btn-success" onclick="confirmAction('${container.key}', 'create')" 
                    title="Crear contenedor">
                <i class="bi bi-plus-circle"></i>
            </button>
        `;
    }
    
    if (container.running) {
        return `
            <button class="btn btn-sm btn-warning" onclick="confirmAction('${container.key}', 'restart')" 
                    title="Reiniciar">
                <i class="bi bi-arrow-clockwise"></i>
            </button>
            <button class="btn btn-sm btn-danger" onclick="confirmAction('${container.key}', 'stop')" 
                    title="Detener">
                <i class="bi bi-stop-circle"></i>
            </button>
        `;
    } else {
        return `
            <button class="btn btn-sm btn-success" onclick="confirmAction('${container.key}', 'start')" 
                    title="Iniciar">
                <i class="bi bi-play-circle"></i>
            </button>
            <button class="btn btn-sm btn-warning" onclick="confirmAction('${container.key}', 'restart')" 
                    title="Reiniciar">
                <i class="bi bi-arrow-clockwise"></i>
            </button>
        `;
    }
}

// Mostrar detalles del contenedor
async function showContainerDetails(containerKey) {
    try {
        selectedContainer = containerKey;
        const response = await fetch(`/containers_bp/api/containers/${containerKey}/status`);
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('modalTitle').textContent = `Detalles: ${data.container.name}`;
            document.getElementById('containerDetails').innerHTML = renderContainerDetails(data.container, data.config);
            document.getElementById('containerModal').style.display = 'flex';
        } else {
            showError('Error al cargar detalles: ' + data.error);
        }
    } catch (error) {
        showError('Error de conexión: ' + error.message);
    }
}

// Renderizar detalles del contenedor
function renderContainerDetails(container, config) {
    return `
        <div class="details-grid">
            <div class="detail-section">
                <h4>Información General</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>ID:</label>
                        <span>${container.short_id}</span>
                    </div>
                    <div class="detail-item">
                        <label>Nombre:</label>
                        <span>${container.name}</span>
                    </div>
                    <div class="detail-item">
                        <label>Imagen:</label>
                        <span>${container.image}</span>
                    </div>
                    <div class="detail-item">
                        <label>Estado:</label>
                        <span class="status-badge status-${container.status}">${container.status}</span>
                    </div>
                    <div class="detail-item">
                        <label>Ejecutándose:</label>
                        <span>${container.running ? 'Sí' : 'No'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Reinicios:</label>
                        <span>${container.restart_count}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h4>Tiempos</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Creado:</label>
                        <span>${new Date(container.created).toLocaleString()}</span>
                    </div>
                    <div class="detail-item">
                        <label>Iniciado:</label>
                        <span>${container.started_at ? new Date(container.started_at).toLocaleString() : 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Uptime:</label>
                        <span>${container.uptime || 'N/A'}</span>
                    </div>
                </div>
            </div>
            
            ${container.running ? `
                <div class="detail-section">
                    <h4>Recursos</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>CPU:</label>
                            <span>${container.cpu_usage}%</span>
                        </div>
                        <div class="detail-item">
                            <label>Memoria:</label>
                            <span>${container.memory_usage_mb} MB (${container.memory_usage}%)</span>
                        </div>
                        <div class="detail-item">
                            <label>Red RX:</label>
                            <span>${container.network_rx_mb} MB</span>
                        </div>
                        <div class="detail-item">
                            <label>Red TX:</label>
                            <span>${container.network_tx_mb} MB</span>
                        </div>
                    </div>
                </div>
            ` : ''}
            
            <div class="detail-section">
                <h4>Configuración</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Puerto:</label>
                        <span>${config.port}</span>
                    </div>
                    <div class="detail-item">
                        <label>Health Check:</label>
                        <span>${config.health_check}</span>
                    </div>
                    <div class="detail-item">
                        <label>Descripción:</label>
                        <span>${config.description}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Mostrar logs del contenedor
async function showContainerLogs(containerKey) {
    try {
        selectedContainer = containerKey;
        const lines = document.getElementById('logsLines')?.value || 50;
        const response = await fetch(`/containers_bp/api/containers/${containerKey}/logs?lines=${lines}`);
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('logsModalTitle').textContent = `Logs: ${data.container_name}`;
            document.getElementById('logsContent').textContent = data.logs || 'No hay logs disponibles';
            document.getElementById('logsModal').style.display = 'flex';
        } else {
            showError('Error al cargar logs: ' + data.error);
        }
    } catch (error) {
        showError('Error de conexión: ' + error.message);
    }
}

// Confirmar acción
function confirmAction(containerKey, action) {
    selectedContainer = containerKey;
    pendingAction = action;
    
    const actionTexts = {
        'start': 'iniciar',
        'stop': 'detener',
        'restart': 'reiniciar',
        'create': 'crear'
    };
    
    document.getElementById('confirmModalTitle').textContent = `Confirmar ${actionTexts[action]}`;
    document.getElementById('confirmMessage').textContent = 
        `¿Estás seguro de que deseas ${actionTexts[action]} el contenedor ${containerKey}?`;
    
    const confirmBtn = document.getElementById('confirmActionBtn');
    confirmBtn.className = `btn ${action === 'stop' ? 'btn-danger' : 'btn-primary'}`;
    confirmBtn.innerHTML = `<i class="bi bi-check"></i> ${actionTexts[action].charAt(0).toUpperCase() + actionTexts[action].slice(1)}`;
    
    document.getElementById('confirmModal').style.display = 'flex';
}

// Ejecutar acción
async function executeAction() {
    if (!selectedContainer || !pendingAction) return;
    
    try {
        closeConfirmModal();
        showLoading(true);
        
        const response = await fetch(`/containers_bp/api/containers/${selectedContainer}/action`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: pendingAction })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showSuccess(data.message);
            await loadContainersStatus();
        } else {
            showError('Error ejecutando acción: ' + data.error);
        }
    } catch (error) {
        showError('Error de conexión: ' + error.message);
    } finally {
        showLoading(false);
        selectedContainer = null;
        pendingAction = null;
    }
}

// Actualizar detalles del contenedor
async function refreshContainerDetails() {
    if (selectedContainer) {
        await showContainerDetails(selectedContainer);
    }
}

// Actualizar logs
async function refreshLogs() {
    if (selectedContainer) {
        await showContainerLogs(selectedContainer);
    }
}

// Actualizar todo
async function refreshAll() {
    await loadContainersStatus();
}

// Mostrar información del sistema
async function showSystemInfo() {
    try {
        const response = await fetch('/containers_bp/api/containers/stats');
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('systemInfoContent').innerHTML = renderSystemInfo(data);
            document.getElementById('systemInfoSection').style.display = 'block';
        } else {
            showError('Error al cargar información del sistema: ' + data.error);
        }
    } catch (error) {
        showError('Error de conexión: ' + error.message);
    }
}

// Renderizar información del sistema
function renderSystemInfo(stats) {
    return `
        <div class="system-info-grid">
            <div class="info-section">
                <h4>Resumen General</h4>
                <ul>
                    <li>Total monitoreados: ${stats.total_monitored}</li>
                    <li>En ejecución: ${stats.running}</li>
                    <li>Detenidos: ${stats.stopped}</li>
                    <li>No encontrados: ${stats.missing}</li>
                    <li>No saludables: ${stats.unhealthy}</li>
                </ul>
            </div>
            
            <div class="info-section">
                <h4>Uso de Recursos</h4>
                <ul>
                    <li>CPU Total: ${stats.resource_usage.total_cpu.toFixed(2)}%</li>
                    <li>Memoria Total: ${stats.resource_usage.total_memory_mb.toFixed(2)} MB</li>
                    <li>Red RX: ${stats.resource_usage.total_network_rx_mb.toFixed(2)} MB</li>
                    <li>Red TX: ${stats.resource_usage.total_network_tx_mb.toFixed(2)} MB</li>
                </ul>
            </div>
            
            ${stats.uptime_summary.length > 0 ? `
                <div class="info-section">
                    <h4>Uptime</h4>
                    <ul>
                        ${stats.uptime_summary.map(item => `<li>${item.name}: ${item.uptime}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

// Ocultar información del sistema
function hideSystemInfo() {
    document.getElementById('systemInfoSection').style.display = 'none';
}

// Exportar reporte
async function exportReport() {
    try {
        const response = await fetch('/containers_bp/api/containers/status');
        const data = await response.json();
        
        if (response.ok) {
            const csvContent = generateCSVReport(data);
            downloadCSV(csvContent, `containers_report_${new Date().toISOString().split('T')[0]}.csv`);
        } else {
            showError('Error al generar reporte: ' + data.error);
        }
    } catch (error) {
        showError('Error de conexión: ' + error.message);
    }
}

// Generar reporte CSV
function generateCSVReport(data) {
    const headers = ['Nombre', 'Estado', 'Ejecutándose', 'Imagen', 'Puerto', 'CPU %', 'Memoria MB', 'Uptime', 'Descripción'];
    const rows = data.containers.map(container => [
        container.name,
        container.status,
        container.running ? 'Sí' : 'No',
        container.image,
        container.port,
        container.details?.cpu_usage || 0,
        container.details?.memory_usage_mb || 0,
        container.details?.uptime || 'N/A',
        container.description
    ]);
    
    const csvContent = [headers, ...rows]
        .map(row => row.map(cell => `"${cell}"`).join(','))
        .join('\n');
    
    return csvContent;
}

// Descargar CSV
function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Auto-refresh functions
function toggleAutoRefresh() {
    const toggle = document.getElementById('autoRefreshToggle');
    if (toggle.checked) {
        startAutoRefresh();
    } else {
        stopAutoRefresh();
    }
}

function setRefreshInterval() {
    const interval = parseInt(document.getElementById('refreshInterval').value);
    currentRefreshRate = interval;
    
    if (autoRefreshInterval) {
        stopAutoRefresh();
        startAutoRefresh();
    }
}

function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(() => {
        loadContainersStatus();
    }, currentRefreshRate * 1000);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Modal functions
function closeModal() {
    document.getElementById('containerModal').style.display = 'none';
    selectedContainer = null;
}

function closeLogsModal() {
    document.getElementById('logsModal').style.display = 'none';
    selectedContainer = null;
}

function closeConfirmModal() {
    document.getElementById('confirmModal').style.display = 'none';
    selectedContainer = null;
    pendingAction = null;
}

// Utility functions
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = show ? 'flex' : 'none';
}

function showError(message) {
    // Aquí podrías implementar un sistema de notificaciones más sofisticado
    alert('Error: ' + message);
    console.error('Error:', message);
}

function showSuccess(message) {
    // Aquí podrías implementar un sistema de notificaciones más sofisticado
    console.log('Success:', message);
}

function updateLastUpdateTime() {
    const now = new Date();
    document.getElementById('lastUpdateTime').textContent = now.toLocaleTimeString();
}

// Event listeners para cerrar modals al hacer clic fuera
document.addEventListener('click', function(event) {
    const modals = ['containerModal', 'logsModal', 'confirmModal'];
    
    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// Limpiar intervalos al salir de la página
window.addEventListener('beforeunload', function() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
});