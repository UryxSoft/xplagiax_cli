// Document Analysis Dashboard - JavaScript
document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const refreshBtn = document.getElementById('refreshBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const analysesTable = document.getElementById('analysesTable');
    const paginationContainer = document.getElementById('paginationContainer');
    const paginationInfo = document.getElementById('paginationInfo');
    
    // Elementos de estadísticas
    const totalAnalysesEl = document.getElementById('totalAnalyses');
    const successRateEl = document.getElementById('successRate');
    const totalParagraphsEl = document.getElementById('totalParagraphs');
    const humanPercentageEl = document.getElementById('humanPercentage');
    const aiPercentageEl = document.getElementById('aiPercentage');
    const avgConfidenceEl = document.getElementById('avgConfidence');
    
    // Filtros
    const searchInput = document.getElementById('searchInput');
    const formatFilter = document.getElementById('formatFilter');
    const dateFromFilter = document.getElementById('dateFromFilter');
    const dateToFilter = document.getElementById('dateToFilter');
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    
    // Modal y Offcanvas
    const analysisModal = new bootstrap.Modal(document.getElementById('analysisModal'));
    const paragraphsOffcanvas = new bootstrap.Offcanvas(document.getElementById('paragraphsOffcanvas'));
    const analysisModalBody = document.getElementById('analysisModalBody');
    const paragraphsList = document.getElementById('paragraphsList');
    const viewParagraphsBtn = document.getElementById('viewParagraphsBtn');
    const exportAnalysisBtn = document.getElementById('exportAnalysisBtn');
    
    // Filtros de párrafos
    const paragraphPageFilter = document.getElementById('paragraphPageFilter');
    const paragraphClassificationFilter = document.getElementById('paragraphClassificationFilter');
    const minConfidenceFilter = document.getElementById('minConfidenceFilter');
    const applyParagraphFiltersBtn = document.getElementById('applyParagraphFiltersBtn');
    const loadMoreParagraphsBtn = document.getElementById('loadMoreParagraphsBtn');
    
    // Variables globales
    let currentPage = 1;
    let currentAnalysisId = null;
    let currentParagraphPage = 1;
    let totalPages = 1;
    let totalParagraphPages = 1;
    let allStats = {};
    
    // Inicializar gráfico
    const contentChart = echarts.init(document.getElementById('contentChart'));
    
    // Configuración del gráfico
    const chartOption = {
        title: {
            text: 'Distribución de Contenido Humano vs IA',
            left: 'center',
            textStyle: { fontSize: 16, fontWeight: 'bold' }
        },
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            data: ['Contenido Humano', 'Contenido IA']
        },
        series: [
            {
                name: 'Distribución',
                type: 'pie',
                radius: '50%',
                data: [
                    { value: 0, name: 'Contenido Humano', itemStyle: { color: '#4ecdc4' } },
                    { value: 0, name: 'Contenido IA', itemStyle: { color: '#ffc107' } }
                ],
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }
        ]
    };
    contentChart.setOption(chartOption);

    // Funciones para mostrar/ocultar loading
    function showLoading(message = 'Cargando...') {
        if (loadingOverlay) {
            document.getElementById('loadingMessage').textContent = message;
            loadingOverlay.style.display = 'flex';
        }
    }

    function hideLoading() {
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }

    // Cargar estadísticas generales
    async function loadGeneralStats() {
        try {
            const response = await fetch('/document_analysis_bp/api/stats');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            allStats = data.stats;
            
            // Actualizar elementos de estadísticas
            if (totalAnalysesEl) totalAnalysesEl.textContent = allStats.total_analyses || 0;
            if (successRateEl) successRateEl.textContent = (allStats.success_rate || 0) + '%';
            if (totalParagraphsEl) totalParagraphsEl.textContent = formatNumber(allStats.total_paragraphs || 0);
            if (humanPercentageEl) humanPercentageEl.textContent = (allStats.human_percentage || 0) + '%';
            if (aiPercentageEl) aiPercentageEl.textContent = (allStats.ai_percentage || 0) + '%';
            if (avgConfidenceEl) avgConfidenceEl.textContent = (allStats.average_confidence || 0) + '%';
            
            // Actualizar gráfico
            updateContentChart(allStats);
            
        } catch (error) {
            console.error('Error al cargar estadísticas:', error);
            showNotification('Error al cargar estadísticas generales', 'error');
        }
    }

    // Actualizar gráfico de contenido
    function updateContentChart(stats) {
        const humanValue = stats.total_human || 0;
        const aiValue = stats.total_ai || 0;
        
        chartOption.series[0].data = [
            { value: humanValue, name: 'Contenido Humano' },
            { value: aiValue, name: 'Contenido IA' }
        ];
        
        contentChart.setOption(chartOption);
    }

    // Cargar análisis con filtros y paginación
    async function loadAnalyses(page = 1) {
        try {
            showLoading('Cargando análisis...');
            
            const params = new URLSearchParams({
                page: page,
                per_page: 20,
                search: searchInput.value || '',
                format: formatFilter.value || '',
                date_from: dateFromFilter.value || '',
                date_to: dateToFilter.value || ''
            });
            
            const response = await fetch(`/document_analysis_bp/api/analyses?${params}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            
            // Actualizar tabla
            updateAnalysesTable(data.analyses);
            
            // Actualizar paginación
            updatePagination(data.pagination);
            
            currentPage = page;
            totalPages = data.pagination.total_pages;
            
        } catch (error) {
            console.error('Error al cargar análisis:', error);
            showNotification('Error al cargar análisis de documentos', 'error');
        } finally {
            hideLoading();
        }
    }

    // Actualizar tabla de análisis
    function updateAnalysesTable(analyses) {
        if (!analysesTable) return;
        
        analysesTable.innerHTML = '';
        
        if (analyses.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="10" style="text-align: center; padding: 40px; color: #666;">No se encontraron análisis</td>';
            analysesTable.appendChild(row);
            return;
        }
        
        analyses.forEach(analysis => {
            const row = document.createElement('tr');
            row.className = 'analysis-row';
            row.dataset.analysisId = analysis.analysis_id;
            
            const confidenceClass = getConfidenceClass(analysis.average_confidence);
            const statusClass = analysis.success ? 'success' : 'failed';
            const statusText = analysis.success ? 'Exitoso' : 'Fallido';
            
            row.innerHTML = `
                <td>
                    <div title="${analysis.title || 'Sin título'}">${truncateText(analysis.title || 'Sin título', 35)}</div>
                </td>
                <td>${analysis.author || 'N/A'}</td>
                <td><span class="badge bg-secondary">${analysis.format || 'N/A'}</span></td>
                <td class="text-center">${analysis.pages || 0}</td>
                <td class="text-center">${analysis.total_paragraphs || 0}</td>
                <td>
                    <div class="d-flex align-items-center">
                        <span class="status-badge status-human me-1">${analysis.human_percentage}%</span>
                        <span class="status-badge status-ai">${analysis.ai_percentage}%</span>
                    </div>
                </td>
                <td>
                    <div class="confidence-bar">
                        <div class="confidence-fill confidence-${confidenceClass}" style="width: ${analysis.average_confidence}%"></div>
                    </div>
                    <small>${analysis.average_confidence}%</small>
                </td>
                <td>${formatDateTime(analysis.analysis_date)}</td>
                <td><span class="analysis-status status-${statusClass}">${statusText}</span></td>
                <td>
                    <button class="btn btn-action btn-info btn-sm view-details" data-analysis-id="${analysis.analysis_id}">
                        👁️ Ver
                    </button>
                </td>
            `;
            
            analysesTable.appendChild(row);
        });
        
        // Agregar eventos a los botones
        document.querySelectorAll('.view-details').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const analysisId = btn.dataset.analysisId;
                showAnalysisDetails(analysisId);
            });
        });
        
        // Agregar eventos a las filas
        document.querySelectorAll('.analysis-row').forEach(row => {
            row.addEventListener('click', () => {
                const analysisId = row.dataset.analysisId;
                showAnalysisDetails(analysisId);
            });
        });
    }

    // Mostrar detalles del análisis en modal
    async function showAnalysisDetails(analysisId) {
        try {
            showLoading('Cargando detalles...');
            
            const response = await fetch(`/document_analysis_bp/api/analysis/${analysisId}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            const analysis = data.analysis;
            
            currentAnalysisId = analysisId;
            
            // Generar contenido del modal
            const modalContent = `
                <div class="row">
                    <div class="col-md-6">
                        <h5>Información del Documento</h5>
                        <div class="metadata-grid">
                            <div class="metadata-item">
                                <div class="metadata-label">Título</div>
                                <div class="metadata-value">${analysis.title || 'Sin título'}</div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Autor</div>
                                <div class="metadata-value">${analysis.author || 'N/A'}</div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Formato</div>
                                <div class="metadata-value">${analysis.format || 'N/A'}</div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Páginas</div>
                                <div class="metadata-value">${analysis.pages || 0}</div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Idioma</div>
                                <div class="metadata-value">${analysis.language || 'N/A'}</div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Fecha de Creación</div>
                                <div class="metadata-value">${analysis.creation_date || 'N/A'}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h5>Estadísticas del Análisis</h5>
                        <div class="metadata-grid">
                            <div class="metadata-item">
                                <div class="metadata-label">Total Párrafos</div>
                                <div class="metadata-value">${analysis.total_paragraphs || 0}</div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Contenido Humano</div>
                                <div class="metadata-value">${analysis.human_count || 0} (${analysis.human_percentage}%)</div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Contenido IA</div>
                                <div class="metadata-value">${analysis.ai_count || 0} (${analysis.ai_percentage}%)</div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Confianza Promedio</div>
                                <div class="metadata-value">${analysis.average_confidence}%</div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Estado</div>
                                <div class="metadata-value">
                                    <span class="analysis-status status-${analysis.success ? 'success' : 'failed'}">
                                        ${analysis.success ? 'Exitoso' : 'Fallido'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${analysis.page_statistics && analysis.page_statistics.length > 0 ? `
                <div class="mt-4">
                    <h5>Estadísticas por Página</h5>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Página</th>
                                    <th>Párrafos</th>
                                    <th>Humano</th>
                                    <th>IA</th>
                                    <th>Confianza</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${analysis.page_statistics.map(stat => `
                                    <tr>
                                        <td>${stat.page_number}</td>
                                        <td>${stat.total_paragraphs}</td>
                                        <td>${stat.human_count} (${stat.human_percentage}%)</td>
                                        <td>${stat.ai_count} (${stat.ai_percentage}%)</td>
                                        <td>${stat.avg_confidence}%</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                ` : ''}
                
                ${analysis.models_used && analysis.models_used.length > 0 ? `
                <div class="mt-4">
                    <h5>Modelos Utilizados</h5>
                    <div class="row">
                        ${analysis.models_used.map(model => `
                            <div class="col-md-3">
                                <div class="metadata-item">
                                    <div class="metadata-label">${model.model}</div>
                                    <div class="metadata-value">${model.count} párrafos</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
            `;
            
            analysisModalBody.innerHTML = modalContent;
            
            // Configurar botones del modal
            viewParagraphsBtn.onclick = () => {
                analysisModal.hide();
                showParagraphs(analysisId);
            };
            
            exportAnalysisBtn.onclick = () => exportAnalysis(analysisId);
            
            analysisModal.show();
            
        } catch (error) {
            console.error('Error al cargar detalles:', error);
            showNotification('Error al cargar detalles del análisis', 'error');
        } finally {
            hideLoading();
        }
    }

    // Mostrar párrafos en offcanvas
    async function showParagraphs(analysisId) {
        try {
            currentAnalysisId = analysisId;
            currentParagraphPage = 1;
            
            // Limpiar filtros
            paragraphPageFilter.value = '';
            paragraphClassificationFilter.value = '';
            minConfidenceFilter.value = '';
            
            // Cargar páginas disponibles para el filtro
            await loadPageOptions(analysisId);
            
            // Cargar párrafos
            await loadParagraphs(analysisId, 1);
            
            paragraphsOffcanvas.show();
            
        } catch (error) {
            console.error('Error al mostrar párrafos:', error);
            showNotification('Error al cargar párrafos', 'error');
        }
    }

    // Cargar opciones de páginas para el filtro
    async function loadPageOptions(analysisId) {
        try {
            const response = await fetch(`/document_analysis_bp/api/analysis/${analysisId}`);
            if (!response.ok) return;
            
            const data = await response.json();
            const pageStats = data.analysis.page_statistics || [];
            
            paragraphPageFilter.innerHTML = '<option value="">Todas las páginas</option>';
            pageStats.forEach(stat => {
                const option = document.createElement('option');
                option.value = stat.page_number;
                option.textContent = `Página ${stat.page_number} (${stat.total_paragraphs} párrafos)`;
                paragraphPageFilter.appendChild(option);
            });
            
        } catch (error) {
            console.error('Error al cargar opciones de páginas:', error);
        }
    }

    // Cargar párrafos con filtros
    async function loadParagraphs(analysisId, page = 1, append = false) {
        try {
            showLoading('Cargando párrafos...');
            
            const params = new URLSearchParams({
                page: page,
                per_page: 20,
                page_number: paragraphPageFilter.value || '',
                classification: paragraphClassificationFilter.value || '',
                min_confidence: minConfidenceFilter.value || '',
            });
            
            const response = await fetch(`/document_analysis_bp/api/analysis/${analysisId}/paragraphs?${params}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            
            // Actualizar lista de párrafos
            updateParagraphsList(data.paragraphs, append);
            
            // Actualizar paginación
            totalParagraphPages = data.pagination.total_pages;
            currentParagraphPage = page;
            
            // Mostrar/ocultar botón "Cargar más"
            if (page < totalParagraphPages) {
                loadMoreParagraphsBtn.style.display = 'block';
            } else {
                loadMoreParagraphsBtn.style.display = 'none';
            }
            
        } catch (error) {
            console.error('Error al cargar párrafos:', error);
            showNotification('Error al cargar párrafos', 'error');
        } finally {
            hideLoading();
        }
    }

    // Actualizar lista de párrafos
    function updateParagraphsList(paragraphs, append = false) {
        if (!append) {
            paragraphsList.innerHTML = '';
        }
        
        if (paragraphs.length === 0 && !append) {
            paragraphsList.innerHTML = '<p class="text-center text-muted">No se encontraron párrafos con los filtros aplicados</p>';
            return;
        }
        
        paragraphs.forEach(paragraph => {
            const paragraphDiv = document.createElement('div');
            paragraphDiv.className = `paragraph-item ${paragraph.is_human ? 'human-classification' : 'ai-classification'}`;
            
            const confidenceClass = getConfidenceClass(paragraph.final_confidence * 100);
            
            paragraphDiv.innerHTML = `
                <div class="paragraph-header">
                    <div class="paragraph-info">
                        Página ${paragraph.page_number} - Párrafo ${paragraph.paragraph_number}
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <span class="status-badge status-${paragraph.is_human ? 'human' : 'ai'}">
                            ${paragraph.classification}
                        </span>
                        <small class="text-muted">${(paragraph.final_confidence * 100).toFixed(1)}%</small>
                    </div>
                </div>
                <div class="paragraph-text">${paragraph.text}</div>
                <div class="confidence-bar">
                    <div class="confidence-fill confidence-${confidenceClass}" 
                         style="width: ${paragraph.final_confidence * 100}%"></div>
                </div>
                ${paragraph.predicted_model ? `<small class="text-muted">Modelo: ${paragraph.predicted_model}</small>` : ''}
            `;
            
            paragraphsList.appendChild(paragraphDiv);
        });
    }

    // Exportar análisis
    async function exportAnalysis(analysisId) {
        try {
            showLoading('Preparando exportación...');
            
            const response = await fetch(`/document_analysis_bp/api/analysis/${analysisId}/export`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            
            // Crear y descargar archivo JSON
            const blob = new Blob([JSON.stringify(data.export_data, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `analysis_${analysisId}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showNotification('Análisis exportado correctamente', 'success');
            
        } catch (error) {
            console.error('Error al exportar:', error);
            showNotification('Error al exportar análisis', 'error');
        } finally {
            hideLoading();
        }
    }

    // Actualizar paginación
    function updatePagination(pagination) {
        if (!paginationContainer || !paginationInfo) return;
        
        // Actualizar información
        paginationInfo.textContent = `Mostrando ${pagination.current_page * pagination.per_page - pagination.per_page + 1}-${Math.min(pagination.current_page * pagination.per_page, pagination.total_items)} de ${pagination.total_items} resultados`;
        
        // Crear botones de paginación
        let paginationHTML = '<nav><ul class="pagination justify-content-center">';
        
        // Botón anterior
        if (pagination.has_prev) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.current_page - 1}">Anterior</a></li>`;
        }
        
        // Páginas
        const startPage = Math.max(1, pagination.current_page - 2);
        const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === pagination.current_page ? 'active' : '';
            paginationHTML += `<li class="page-item ${activeClass}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
        
        // Botón siguiente
        if (pagination.has_next) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.current_page + 1}">Siguiente</a></li>`;
        }
        
        paginationHTML += '</ul></nav>';
        paginationContainer.innerHTML = paginationHTML;
        
        // Agregar eventos a los botones
        paginationContainer.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(link.dataset.page);
                if (page) {
                    loadAnalyses(page);
                }
            });
        });
    }

    // Funciones helper
    function formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        try {
            return new Date(dateString).toLocaleString('es-ES', {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit'
            });
        } catch (error) {
            return 'N/A';
        }
    }

    function formatNumber(number) {
        return new Intl.NumberFormat('es-ES').format(number);
    }

    function truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) return text || 'N/A';
        return text.substring(0, maxLength) + '...';
    }

    function getConfidenceClass(confidence) {
        if (confidence >= 80) return 'high';
        if (confidence >= 60) return 'medium';
        return 'low';
    }

    function showNotification(message, type = 'info', duration = 4000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icons = {
            success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️'
        };
        
        const icon = icons[type] || icons.info;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.2em;">${icon}</span>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        notification.addEventListener('click', () => notification.remove());
        setTimeout(() => notification.parentNode && notification.remove(), duration);
    }

    // Event listeners
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadGeneralStats();
            loadAnalyses(currentPage);
        });
    }

    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', () => {
            currentPage = 1;
            loadAnalyses(1);
        });
    }

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            searchInput.value = '';
            formatFilter.value = '';
            dateFromFilter.value = '';
            dateToFilter.value = '';
            currentPage = 1;
            loadAnalyses(1);
        });
    }

    if (applyParagraphFiltersBtn) {
        applyParagraphFiltersBtn.addEventListener('click', () => {
            if (currentAnalysisId) {
                loadParagraphs(currentAnalysisId, 1, false);
            }
        });
    }

    if (loadMoreParagraphsBtn) {
        loadMoreParagraphsBtn.addEventListener('click', () => {
            if (currentAnalysisId && currentParagraphPage < totalParagraphPages) {
                loadParagraphs(currentAnalysisId, currentParagraphPage + 1, true);
            }
        });
    }

    // Eventos de teclado para filtros
    [searchInput, dateFromFilter, dateToFilter].forEach(input => {
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    currentPage = 1;
                    loadAnalyses(1);
                }
            });
        }
    });

    // Redimensionar gráfico
    window.addEventListener('resize', () => {
        contentChart.resize();
    });

    // Inicialización
    function initializeDashboard() {
        showNotification('Cargando dashboard de análisis...', 'info');
        
        loadGeneralStats();
        loadAnalyses(1);
        
        setTimeout(() => {
            showNotification('Dashboard cargado correctamente', 'success');
        }, 1500);
    }

    // Manejar visibilidad de la página
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            loadGeneralStats();
            loadAnalyses(currentPage);
        }
    });

    // Inicializar
    initializeDashboard();
});