document.addEventListener('DOMContentLoaded', () => {
    const generateReportBtn = document.getElementById('generateReport');
    const applyFiltersBtn = document.getElementById('applyFilters');
    const resetFiltersBtn = document.getElementById('resetFilters');
    const exportCSVBtn = document.getElementById('exportCSV');
    const exportPDFBtn = document.getElementById('exportPDF');
    const reportResults = document.getElementById('reportResults');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const reportTypeSelect = document.getElementById('reportType');
    const reportChart = echarts.init(document.getElementById('reportChart'));

    // Set default dates (last 30 days)
    const today = new Date();
    const lastMonth = new Date();
    lastMonth.setDate(lastMonth.getDate() - 30);
    
    startDateInput.valueAsDate = lastMonth;
    endDateInput.valueAsDate = today;

    // Generate report
    generateReportBtn.addEventListener('click', generateReport);
    applyFiltersBtn.addEventListener('click', generateReport);

    // Reset filters
    resetFiltersBtn.addEventListener('click', () => {
        startDateInput.valueAsDate = lastMonth;
        endDateInput.valueAsDate = today;
        reportTypeSelect.value = 'activity';
        generateReport();
    });

    // Export buttons
    exportCSVBtn.addEventListener('click', () => exportReport('csv'));
    exportPDFBtn.addEventListener('click', () => exportReport('pdf'));

    async function generateReport() {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        const reportType = reportTypeSelect.value;
        
        try {
            const response = await fetch(`/reports_bp/api/reports?type=${reportType}&start=${startDate}&end=${endDate}`);
            const reportData = await response.json();
            
            renderReport(reportData, reportType);
            renderChart(reportData, reportType);
        } catch (error) {
            console.error('Error generating report:', error);
        }
    }
    
    function renderChart(data, type) {
        if (type === 'activity') {
            // Group by session and count commands
            const sessionCommands = {};
            data.forEach(item => {
                if (!sessionCommands[item.session_id]) {
                    sessionCommands[item.session_id] = 0;
                }
                sessionCommands[item.session_id]++;
            });
            
            const chartOption = {
                title: {
                    text: 'Comandos por Sesión',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'item'
                },
                legend: {
                    orient: 'vertical',
                    left: 'left'
                },
                series: [
                    {
                        name: 'Comandos',
                        type: 'pie',
                        radius: '50%',
                        data: Object.keys(sessionCommands).map(sessionId => ({
                            value: sessionCommands[sessionId],
                            name: `Sesión ${sessionId}`
                        })),
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
            
            reportChart.setOption(chartOption);
        } else if (type === 'transfers') {
            // Group by status
            const statusCount = {
                completed: 0,
                failed: 0,
                pending: 0,
                in_progress: 0
            };
            
            data.forEach(transfer => {
                statusCount[transfer.status]++;
            });
            
            const chartOption = {
                title: {
                    text: 'Transferencias por Estado',
                    left: 'center'
                },
                tooltip: {
                    trigger: 'item'
                },
                legend: {
                    orient: 'vertical',
                    left: 'left'
                },
                series: [
                    {
                        name: 'Transferencias',
                        type: 'pie',
                        radius: '50%',
                        data: Object.keys(statusCount).map(status => ({
                            value: statusCount[status],
                            name: status
                        })),
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
            
            reportChart.setOption(chartOption);
        }
    }
    
    function renderReport(data, type) {
        // Clear existing content
        reportResults.innerHTML = '';
        
        // Create header based on report type
        const thead = document.createElement('thead');
        let headerHTML = '';
        
        switch(type) {
            case 'activity':
                headerHTML = `
                    <tr>
                        <th>Sesión ID</th>
                        <th>Comando</th>
                        <th>Resultado</th>
                        <th>Timestamp</th>
                        <th>Tiempo Ejecución</th>
                        <th>Exit Code</th>
                    </tr>
                `;
                break;
                
            case 'transfers':
                headerHTML = `
                    <tr>
                        <th>ID Transferencia</th>
                        <th>Archivo</th>
                        <th>Ruta Remota</th>
                        <th>Tipo</th>
                        <th>Tamaño (MB)</th>
                        <th>Estado</th>
                        <th>Iniciado</th>
                        <th>Completado</th>
                    </tr>
                `;
                break;
                
            case 'security':
                headerHTML = `
                    <tr>
                        <th>Timestamp</th>
                        <th>Evento</th>
                        <th>Usuario</th>
                        <th>IP</th>
                        <th>Detalles</th>
                    </tr>
                `;
                break;
        }
        
        thead.innerHTML = headerHTML;
        reportResults.appendChild(thead);
        
        // Create body with data
        const tbody = document.createElement('tbody');
        data.forEach(item => {
            const row = document.createElement('tr');
            let rowHTML = '';
            
            switch(type) {
                case 'activity':
                    rowHTML = `
                        <td>${item.session_id}</td>
                        <td>${item.command}</td>
                        <td>${item.output}</td>
                        <td>${item.timestamp}</td>
                        <td>${item.execution_time || 'N/A'}</td>
                        <td>${item.exit_code || 'N/A'}</td>
                    `;
                    break;
                    
                case 'transfers':
                    const sizeMB = item.file_size ? (item.file_size / (1024 * 1024)).toFixed(2) : 'N/A';
                    rowHTML = `
                        <td>${item.id}</td>
                        <td>${item.filename}</td>
                        <td>${item.remote_path}</td>
                        <td>${item.transfer_type}</td>
                        <td>${sizeMB}</td>
                        <td>${item.status}</td>
                        <td>${item.started_at}</td>
                        <td>${item.completed_at || 'N/A'}</td>
                    `;
                    break;
                    
                case 'security':
                    rowHTML = `
                        <td>${item.timestamp}</td>
                        <td>${item.event_type}</td>
                        <td>${item.username}</td>
                        <td>${item.ip_address}</td>
                        <td>${item.details}</td>
                    `;
                    break;
            }
            
            row.innerHTML = rowHTML;
            tbody.appendChild(row);
        });
        
        reportResults.appendChild(tbody);
    }
    
    async function exportReport(format) {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        const reportType = reportTypeSelect.value;
        
        try {
            const response = await fetch(`/reports_bp/api/reports/export?type=${reportType}&format=${format}&start=${startDate}&end=${endDate}`);
            const blob = await response.blob();
            
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `reporte_ssh_${new Date().toISOString().slice(0,10)}.${format}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (error) {
            console.error('Error exporting report:', error);
        }
    }

    // Generate initial report
    generateReport();
    
    // Resize chart on window resize
    window.addEventListener('resize', () => {
        reportChart.resize();
    });
});