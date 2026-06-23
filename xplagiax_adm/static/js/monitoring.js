document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('startMonitoring');
    const stopBtn = document.getElementById('stopMonitoring');
    const cpuChartCtx = document.getElementById('cpuChart').getContext('2d');
    const memoryChartCtx = document.getElementById('memoryChart').getContext('2d');
    const activeSessionsList = document.getElementById('activeSessionsList');
    
    let cpuChart, memoryChart;
    let socket;
    let isMonitoring = false;
    
    // Initialize charts
    function initCharts() {
        cpuChart = new Chart(cpuChartCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Uso de CPU (%)',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Uso de CPU en Tiempo Real'
                    }
                }
            }
        });
        
        memoryChart = new Chart(memoryChartCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Uso de Memoria (%)',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Uso de Memoria en Tiempo Real'
                    }
                }
            }
        });
    }
    
    // Initialize WebSocket connection
    function initWebSocket() {
        if (typeof io !== 'undefined') {
            socket = io();
            
            // Handle connection events
            socket.on('connect', () => {
                console.log('Conectado al servidor WebSocket');
            });
            
            socket.on('disconnect', () => {
                console.log('Desconectado del servidor WebSocket');
            });
            
            // Handle monitoring events
            socket.on('system_stats', (data) => {
                updateCharts(data);
                updateActiveSessions(data.active_sessions);
            });
            
            socket.on('monitoring_started', (data) => {
                console.log('Monitoreo iniciado:', data);
            });
            
            socket.on('monitoring_stopped', (data) => {
                console.log('Monitoreo detenido:', data);
            });
            
            socket.on('monitoring_error', (data) => {
                console.error('Error en monitoreo:', data);
                showError('Error en el monitoreo: ' + data.error);
            });
        } else {
            console.error('Socket.IO no está disponible');
            showError('Socket.IO no está disponible. Verifique que la librería esté cargada.');
        }
    }
    
    // Start monitoring
    startBtn.addEventListener('click', () => {
        if (!socket) {
            initWebSocket();
        }
        
        if (socket && socket.connected) {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            isMonitoring = true;
            
            // Emit start monitoring event
            socket.emit('start_monitoring');
            
            // Update button text
            startBtn.innerHTML = '<span>⏳</span> Iniciando...';
            
            // Clear previous data
            clearCharts();
            
            console.log('Monitoreo iniciado');
        } else {
            showError('No se pudo conectar al servidor WebSocket');
        }
    });
    
    // Stop monitoring
    stopBtn.addEventListener('click', () => {
        if (socket && isMonitoring) {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            isMonitoring = false;
            
            // Emit stop monitoring event
            socket.emit('stop_monitoring');
            
            // Update button text
            startBtn.innerHTML = '<span>▶️</span> Iniciar';
            
            console.log('Monitoreo detenido');
        }
    });
    
    // Update charts with new data
    function updateCharts(data) {
        if (!data || !cpuChart || !memoryChart) return;
        
        const now = new Date().toLocaleTimeString();
        
        // Update CPU chart
        cpuChart.data.labels.push(now);
        cpuChart.data.datasets[0].data.push(data.cpu || 0);
        
        // Keep only last 20 data points
        if (cpuChart.data.labels.length > 20) {
            cpuChart.data.labels.shift();
            cpuChart.data.datasets[0].data.shift();
        }
        cpuChart.update('none'); // No animation for better performance
        
        // Update memory chart
        const memoryPercent = data.memory ? data.memory.percent : 0;
        memoryChart.data.labels.push(now);
        memoryChart.data.datasets[0].data.push(memoryPercent);
        
        // Keep only last 20 data points
        if (memoryChart.data.labels.length > 20) {
            memoryChart.data.labels.shift();
            memoryChart.data.datasets[0].data.shift();
        }
        memoryChart.update('none'); // No animation for better performance
    }
    
    // Update active sessions table
    function updateActiveSessions(sessions) {
        if (!sessions || !Array.isArray(sessions)) {
            activeSessionsList.innerHTML = '<tr><td colspan="5">No hay sesiones activas</td></tr>';
            return;
        }
        
        activeSessionsList.innerHTML = '';
        
        if (sessions.length === 0) {
            activeSessionsList.innerHTML = '<tr><td colspan="5">No hay sesiones activas</td></tr>';
            return;
        }
        
        sessions.forEach(session => {
            try {
                const connectedAt = session.connected_at ? new Date(session.connected_at) : new Date();
                const duration = Math.floor((new Date() - connectedAt) / 60000);
                
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${session.id || 'N/A'}</td>
                    <td>${session.hostname || 'N/A'}</td>
                    <td>${session.username || 'N/A'}</td>
                    <td>${duration >= 0 ? duration : 0} min</td>
                    <td>${session.traffic || '0'} KB</td>
                `;
                activeSessionsList.appendChild(row);
            } catch (error) {
                console.error('Error procesando sesión:', error);
            }
        });
    }
    
    // Clear charts data
    function clearCharts() {
        if (cpuChart) {
            cpuChart.data.labels = [];
            cpuChart.data.datasets[0].data = [];
            cpuChart.update();
        }
        
        if (memoryChart) {
            memoryChart.data.labels = [];
            memoryChart.data.datasets[0].data = [];
            memoryChart.update();
        }
        
        activeSessionsList.innerHTML = '';
    }
    
    // Show error message
    function showError(message) {
        // You can implement a proper error display system here
        console.error(message);
        alert(message); // Simple alert for now
    }
    
    // Initialize everything
    initCharts();
    
    // Handle page unload
    window.addEventListener('beforeunload', () => {
        if (socket && isMonitoring) {
            socket.emit('stop_monitoring');
        }
    });
});