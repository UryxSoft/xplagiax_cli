// Dashboard de Estadísticas SSH - JavaScript Mejorado
document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const refreshBtn = document.getElementById('refreshBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Elementos de estadísticas - AMPLIADO para incluir todos los modelos
    const activeSessionsEl = document.getElementById('activeSessions');
    const totalTransfersEl = document.getElementById('totalTransfers');
    const cpuUsageEl = document.getElementById('cpuUsage');
    const memoryUsageEl = document.getElementById('memoryUsage');
    const totalCommandsEl = document.getElementById('totalCommands'); // NUEVO - SessionLog
    const successRateEl = document.getElementById('successRate'); // NUEVO - SessionLog
    const recentActivityEl = document.getElementById('recentActivity');
    const sessionsListEl = document.getElementById('sessionsList');
    const recentCommandsEl = document.getElementById('recentCommands'); // NUEVO - SessionLog
    
    // Inicializar gráfico principal con configuración mejorada
    const systemUsageChart = echarts.init(document.getElementById('systemUsageChart'));
    
    // Configuración del gráfico mejorada
    const chartOption = {
        title: {
            text: 'Monitoreo del Sistema SSH',
            left: 'center',
            textStyle: { fontSize: 18, fontWeight: 'bold' }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                label: { backgroundColor: '#6a7985' }
            },
            formatter: function (params) {
                let tooltip = params[0].name + '<br/>';
                params.forEach(param => {
                    tooltip += param.marker + param.seriesName + ': ' + param.value + '%<br/>';
                });
                return tooltip;
            }
        },
        legend: {
            data: ['CPU', 'Memoria', 'Disco', 'Comandos por Hora'], // AMPLIADO
            top: 30
        },
        toolbox: {
            feature: {
                saveAsImage: { title: 'Guardar como imagen' },
                dataView: { title: 'Ver datos', readOnly: true },
                magicType: { title: 'Cambiar tipo', type: ['line', 'bar'] },
                restore: { title: 'Restaurar' }
            }
        },
        grid: {
            left: '3%', right: '4%', bottom: '3%',
            containLabel: true, top: 80
        },
        xAxis: {
            type: 'category', boundaryGap: false,
            data: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        },
        yAxis: [
            {
                type: 'value', min: 0, max: 100,
                axisLabel: { formatter: '{value}%' }
            },
            {
                type: 'value', min: 0,
                axisLabel: { formatter: '{value}' }
            }
        ],
        series: [
            {
                name: 'CPU', type: 'line', smooth: true,
                lineStyle: { width: 3 }, areaStyle: { opacity: 0.2 },
                emphasis: { focus: 'series' },
                data: [0, 0, 0, 0, 0, 0, 0],
                itemStyle: { color: '#ff6b6b' }
            },
            {
                name: 'Memoria', type: 'line', smooth: true,
                lineStyle: { width: 3 }, areaStyle: { opacity: 0.2 },
                emphasis: { focus: 'series' },
                data: [0, 0, 0, 0, 0, 0, 0],
                itemStyle: { color: '#4ecdc4' }
            },
            {
                name: 'Disco', type: 'line', smooth: true,
                lineStyle: { width: 3 }, areaStyle: { opacity: 0.2 },
                emphasis: { focus: 'series' },
                data: [0, 0, 0, 0, 0, 0, 0],
                itemStyle: { color: '#45b7d1' }
            }
        ]
    };
    
    systemUsageChart.setOption(chartOption);

    // Variables para almacenar datos históricos
    let historicalData = {
        cpu: [], memory: [], disk: [], commands: [],
        timestamps: []
    };

    // Cache para optimizar rendimiento
    let lastDataUpdate = 0;
    const CACHE_DURATION = 10000; // 10 segundos

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

    // Función principal para cargar datos del dashboard - MEJORADA
    async function loadDashboardData() {
        try {
            // Verificar cache
            const now = Date.now();
            if (now - lastDataUpdate < CACHE_DURATION) {
                console.log('Usando datos en cache');
                return;
            }

            showLoading('Actualizando estadísticas...');
            
            // Cargar estadísticas principales
            const response = await fetch('/dashboardssh_bp/api/stats');
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Actualizar estadísticas básicas
            updateSystemStats(data.system);
            updateUserStats(data.user);
            
            // Actualizar gráfico
            updateSystemChart(data.system);
            
            // Actualizar tablas - AMPLIADO para incluir comandos
            updateRecentActivity(data.user.recent_transfers || []);
            updateSessionsList(data.user.sessions || []);
            updateRecentCommands(data.user.recent_commands || []); // NUEVO
            
            // Guardar datos históricos
            saveHistoricalData(data.system, data.user);
            
            lastDataUpdate = now;
            showNotification('Datos actualizados correctamente', 'success');
            
        } catch (error) {
            console.error('Error al cargar datos:', error);
            showNotification('Error al cargar datos del dashboard', 'error');
        } finally {
            hideLoading();
        }
    }

    // Actualizar estadísticas del sistema
    function updateSystemStats(systemData) {
        if (cpuUsageEl) {
            const cpuValue = Math.round(systemData.cpu);
            cpuUsageEl.textContent = `${cpuValue}%`;
            cpuUsageEl.style.color = cpuValue > 80 ? '#e74c3c' : cpuValue > 60 ? '#f39c12' : '#2c3e50';
        }
        
        if (memoryUsageEl) {
            const memoryMB = Math.round(systemData.memory.used / (1024 * 1024));
            const memoryPercent = systemData.memory.percent;
            memoryUsageEl.textContent = `${memoryMB} MB`;
            memoryUsageEl.style.color = memoryPercent > 80 ? '#e74c3c' : memoryPercent > 60 ? '#f39c12' : '#2c3e50';
        }
    }

    // Actualizar estadísticas del usuario - AMPLIADO
    function updateUserStats(userData) {
        if (activeSessionsEl) {
            activeSessionsEl.textContent = userData.active_sessions || 0;
        }
        
        if (totalTransfersEl) {
            totalTransfersEl.textContent = userData.recent_transfers?.length || 0;
        }

        // NUEVAS métricas de SessionLog
        if (totalCommandsEl) {
            totalCommandsEl.textContent = userData.total_commands || 0;
        }

        if (successRateEl) {
            const rate = userData.command_success_rate || 0;
            successRateEl.textContent = `${rate}%`;
            successRateEl.style.color = rate > 90 ? '#27ae60' : rate > 70 ? '#f39c12' : '#e74c3c';
        }
    }

    // Actualizar gráfico del sistema - MEJORADO
    function updateSystemChart(systemData) {
        // Generar datos semanales simulados basados en valores actuales
        const cpuData = generateWeeklyTrend(systemData.cpu);
        const memoryData = generateWeeklyTrend(systemData.memory.percent);
        const diskData = systemData.disk ? generateWeeklyTrend(systemData.disk.percent) : [0, 0, 0, 0, 0, 0, 0];
        
        // Actualizar series del gráfico
        chartOption.series[0].data = cpuData;
        chartOption.series[1].data = memoryData;
        chartOption.series[2].data = diskData;
        
        systemUsageChart.setOption(chartOption);
    }

    // Generar tendencia semanal basada en valor actual - MEJORADO
    function generateWeeklyTrend(currentValue) {
        const data = [];
        const baseValue = currentValue || 0;
        
        for (let i = 0; i < 7; i++) {
            // Generar variación más realista
            const timeOfDay = Math.sin(i * Math.PI / 3) * 10; // Patrón de actividad
            const randomVariation = (Math.random() - 0.5) * 15;
            const seasonalTrend = Math.cos(i * Math.PI / 6) * 5;
            
            let value = baseValue + timeOfDay + randomVariation + seasonalTrend;
            
            // Mantener valores dentro de límites
            value = Math.max(0, Math.min(100, value));
            data.push(Math.round(value * 100) / 100);
        }
        
        return data;
    }

    // Guardar datos históricos - AMPLIADO
    function saveHistoricalData(systemData, userData) {
        const now = new Date();
        
        historicalData.cpu.push(systemData.cpu);
        historicalData.memory.push(systemData.memory.percent);
        historicalData.disk.push(systemData.disk ? systemData.disk.percent : 0);
        historicalData.commands.push(userData.total_commands || 0); // NUEVO
        historicalData.timestamps.push(now.toISOString());
        
        // Mantener solo los últimos 100 registros
        const maxRecords = 100;
        if (historicalData.cpu.length > maxRecords) {
            historicalData.cpu.shift();
            historicalData.memory.shift();
            historicalData.disk.shift();
            historicalData.commands.shift(); // NUEVO
            historicalData.timestamps.shift();
        }
    }

    // NUEVA FUNCIÓN: Actualizar tabla de comandos recientes
    function updateRecentCommands(commands) {
        if (!recentCommandsEl) return;
        
        recentCommandsEl.innerHTML = '';
        
        if (commands.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="5" style="text-align: center; color: #666; padding: 20px;">No hay comandos recientes</td>';
            recentCommandsEl.appendChild(row);
            return;
        }
        
        commands.slice(0, 10).forEach(cmd => {
            const row = document.createElement('tr');
            
            // Determinar estado del comando
            let statusClass, statusText;
            if (cmd.exit_code === 0) {
                statusClass = 'completed';
                statusText = 'Éxito';
            } else if (cmd.exit_code === null || cmd.exit_code === undefined) {
                statusClass = 'pending';
                statusText = 'Ejecutando';
            } else {
                statusClass = 'failed';
                statusText = `Error (${cmd.exit_code})`;
            }
            
            const executionTime = cmd.execution_time ? 
                (cmd.execution_time < 1 ? `${Math.round(cmd.execution_time * 1000)}ms` : `${cmd.execution_time.toFixed(2)}s`) 
                : 'N/A';
            
            row.innerHTML = `
                <td title="${cmd.command || 'N/A'}">${truncateText(cmd.command || 'N/A', 40)}</td>
                <td>${cmd.session_id || 'N/A'}</td>
                <td><span class="status-badge status-${statusClass}">${statusText}</span></td>
                <td>${executionTime}</td>
                <td>${formatDateTime(cmd.timestamp)}</td>
            `;
            recentCommandsEl.appendChild(row);
        });
    }

    // Actualizar tabla de actividad reciente - MEJORADO
    function updateRecentActivity(transfers) {
        if (!recentActivityEl) return;
        
        recentActivityEl.innerHTML = '';
        
        if (transfers.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="6" style="text-align: center; color: #666; padding: 20px;">No hay transferencias recientes</td>';
            recentActivityEl.appendChild(row);
            return;
        }
        
        transfers.slice(0, 10).forEach(transfer => {
            const row = document.createElement('tr');
            const fileSize = transfer.file_size ? formatFileSize(transfer.file_size) : 'N/A';
            const transferType = transfer.transfer_type || 'unknown';
            
            // Agregar icono según el tipo de transferencia
            const typeIcon = transferType === 'upload' ? '⬆️' : transferType === 'download' ? '⬇️' : '📁';
            
            row.innerHTML = `
                <td>${transfer.session_id || 'N/A'}</td>
                <td title="${transfer.filename || 'N/A'}">${truncateText(transfer.filename || 'N/A', 30)}</td>
                <td><span class="status-badge status-${transferType.toLowerCase()}">${typeIcon} ${transferType.toUpperCase()}</span></td>
                <td><span class="status-badge status-${(transfer.status || 'unknown').toLowerCase()}">${transfer.status || 'Unknown'}</span></td>
                <td>${formatDateTime(transfer.started_at)}</td>
                <td>${fileSize}</td>
            `;
            recentActivityEl.appendChild(row);
        });
    }

    // Actualizar lista de sesiones - MEJORADO
    function updateSessionsList(sessions) {
        if (!sessionsListEl) return;
        
        sessionsListEl.innerHTML = '';
        
        if (sessions.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="6" style="text-align: center; color: #666; padding: 20px;">No hay sesiones registradas</td>';
            sessionsListEl.appendChild(row);
            return;
        }
        
        sessions.forEach(session => {
            const row = document.createElement('tr');
            const duration = calculateDuration(session.created_at, session.last_activity);
            const hostDisplay = session.hostname || session.host || 'N/A';
            
            // Agregar indicador visual para sesiones activas
            const activeIndicator = session.is_active ? '🟢' : '🔴';
            
            row.innerHTML = `
                <td>${session.id}</td>
                <td title="${hostDisplay}">${truncateText(hostDisplay, 25)}</td>
                <td>${session.username || 'N/A'}</td>
                <td><span class="status-badge status-${session.is_active ? 'active' : 'inactive'}">${activeIndicator} ${session.is_active ? 'Activa' : 'Inactiva'}</span></td>
                <td>${formatDateTime(session.created_at)}</td>
                <td>${duration}</td>
            `;
            
            // Agregar eventos para interacción
            row.addEventListener('mouseover', () => {
                row.style.backgroundColor = '#f0f8ff';
            });
            
            row.addEventListener('mouseout', () => {
                row.style.backgroundColor = '';
            });
            
            sessionsListEl.appendChild(row);
        });
    }

    // Calcular duración de sesión - MEJORADO
    function calculateDuration(startTime, endTime) {
        if (!startTime) return 'N/A';
        
        try {
            const start = new Date(startTime);
            const end = endTime ? new Date(endTime) : new Date();
            const diff = end - start;
            
            if (diff < 0) return 'N/A';
            
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            
            if (days > 0) {
                return `${days}d ${hours}h ${minutes}m`;
            } else if (hours > 0) {
                return `${hours}h ${minutes}m`;
            } else {
                return `${minutes}m`;
            }
        } catch (error) {
            return 'N/A';
        }
    }

    // Formatear tamaño de archivo - MEJORADO
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        const size = parseFloat((bytes / Math.pow(k, i)).toFixed(2));
        return `${size} ${sizes[i]}`;
    }

    // Formatear fecha y hora - MEJORADO
    function formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            const now = new Date();
            const diff = now - date;
            
            // Mostrar tiempo relativo para fechas recientes
            if (diff < 60000) { // menos de 1 minuto
                return 'Hace unos segundos';
            } else if (diff < 3600000) { // menos de 1 hora
                const minutes = Math.floor(diff / 60000);
                return `Hace ${minutes} min`;
            } else if (diff < 86400000) { // menos de 1 día
                const hours = Math.floor(diff / 3600000);
                return `Hace ${hours}h`;
            } else {
                return date.toLocaleString('es-ES', {
                    year: 'numeric', month: '2-digit', day: '2-digit',
                    hour: '2-digit', minute: '2-digit'
                });
            }
        } catch (error) {
            return 'N/A';
        }
    }

    // Truncar texto
    function truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) return text || 'N/A';
        return text.substring(0, maxLength) + '...';
    }

    // Mostrar notificación - MEJORADO
    function showNotification(message, type = 'info', duration = 4000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        // Agregar icono según el tipo
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
        
        // Agregar evento para cerrar al hacer clic
        notification.addEventListener('click', () => {
            notification.remove();
        });
        
        // Remover automáticamente
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }

    // Cargar información detallada del sistema - AMPLIADO
    async function loadDetailedSystemInfo() {
        try {
            const response = await fetch('/dashboardssh_bp/api/system/detailed');
            if (!response.ok) return;
            
            const data = await response.json();
            
            // Procesar información detallada
            console.log('Información detallada del sistema:', data);
            
            // Aquí puedes agregar lógica para mostrar información adicional
            // como procesos principales, uso de red, etc.
            
        } catch (error) {
            console.error('Error al cargar información detallada:', error);
        }
    }

    // NUEVA FUNCIÓN: Cargar estadísticas de comandos
    async function loadCommandsStats() {
        try {
            const response = await fetch('/dashboardssh_bp/api/commands/history');
            if (!response.ok) return;
            
            const data = await response.json();
            
            // Mostrar estadísticas de comandos en consola o interfaz
            console.log('Estadísticas de comandos:', data.stats);
            
        } catch (error) {
            console.error('Error al cargar estadísticas de comandos:', error);
        }
    }

    // Event listeners
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            lastDataUpdate = 0; // Forzar actualización
            loadDashboardData();
            loadDetailedSystemInfo();
            loadCommandsStats(); // NUEVO
        });
    }

    // Función de inicialización
    function initializeDashboard() {
        showNotification('Inicializando dashboard...', 'info');
        
        // Cargar datos inicial
        loadDashboardData();
        loadDetailedSystemInfo();
        loadCommandsStats(); // NUEVO
        
        // Configurar auto-refresh
        setInterval(loadDashboardData, 30000); // Cada 30 segundos
        setInterval(loadDetailedSystemInfo, 300000); // Cada 5 minutos
        setInterval(loadCommandsStats, 60000); // Cada minuto para comandos
        
        // Mostrar mensaje de bienvenida después de cargar
        setTimeout(() => {
            showNotification('Dashboard SSH cargado correctamente', 'success');
        }, 1500);
    }

    // Redimensionar gráfico cuando cambie el tamaño de ventana
    window.addEventListener('resize', () => {
        systemUsageChart.resize();
    });

    // Manejar visibilidad de la página para pausar/reanudar actualizaciones
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            console.log('Dashboard pausado');
        } else {
            console.log('Dashboard reanudado');
            loadDashboardData(); // Actualizar al volver a la página
        }
    });

    // Inicializar dashboard
    initializeDashboard();
});