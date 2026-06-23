// services-monitor.js - Advanced Services Monitor JavaScript

class AdvancedServicesMonitor {
    constructor() {
        this.services = {};
        this.serviceHistory = {};
        this.autoRefreshInterval = null;
        this.isRefreshing = false;
        this.notifications = [];
        this.soundEnabled = true;
        this.filters = {
            status: 'all', // all, online, offline
            service: 'all'
        };
        
        this.init();
    }
    
    init() {
        this.loadServices();
        this.setupEventListeners();
        this.startAutoRefresh();
        this.initializeNotifications();
        this.loadUserPreferences();
    }
    
    setupEventListeners() {
        // Auto-refresh controls
        const autoRefreshCheckbox = document.getElementById('autoRefresh');
        const refreshInterval = document.getElementById('refreshInterval');
        
        autoRefreshCheckbox?.addEventListener('change', () => {
            if (autoRefreshCheckbox.checked) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
            this.saveUserPreferences();
        });
        
        refreshInterval?.addEventListener('change', () => {
            if (autoRefreshCheckbox?.checked) {
                this.startAutoRefresh();
            }
            this.saveUserPreferences();
        });
        
        // Filter controls
        document.addEventListener('change', (e) => {
            if (e.target.matches('.status-filter') || e.target.matches('.service-filter')) {
                this.applyFilters();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'r':
                        e.preventDefault();
                        this.loadServices();
                        break;
                    case 'e':
                        e.preventDefault();
                        this.exportReport();
                        break;
                }
            }
        });
        
        // Window visibility change - pause/resume auto-refresh
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else if (document.getElementById('autoRefresh')?.checked) {
                this.startAutoRefresh();
            }
        });
    }
    
    async loadServices() {
        if (this.isRefreshing) return;
        
        this.isRefreshing = true;
        this.showLoadingState(true);
        
        try {
            const response = await fetch('/services_bp/api/status');
            const data = await response.json();
            
            if (data.success) {
                this.processServicesData(data);
                this.updateOverview(data.summary);
                this.renderServices();
                this.updateLastRefreshTime();
                this.checkForStatusChanges(data.services);
            } else {
                this.showError('Failed to load services status: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error loading services:', error);
            this.showError('Error connecting to server: ' + error.message);
        } finally {
            this.isRefreshing = false;
            this.showLoadingState(false);
        }
    }
    
    processServicesData(data) {
        const timestamp = new Date().toISOString();
        
        // Store current services data
        this.services = data.services;
        
        // Update service history for trend analysis
        Object.keys(data.services).forEach(serviceName => {
            if (!this.serviceHistory[serviceName]) {
                this.serviceHistory[serviceName] = [];
            }
            
            const history = this.serviceHistory[serviceName];
            history.push({
                timestamp,
                status: data.services[serviceName].status,
                responseTime: data.services[serviceName].response_time
            });
            
            // Keep only last 50 entries
            if (history.length > 50) {
                history.shift();
            }
        });
    }
    
    checkForStatusChanges(newServices) {
        Object.keys(newServices).forEach(serviceName => {
            const oldService = this.services[serviceName];
            const newService = newServices[serviceName];
            
            if (oldService && oldService.status !== newService.status) {
                this.showNotification(
                    serviceName,
                    newService.status ? 'Service is now ONLINE' : 'Service is now OFFLINE',
                    newService.status ? 'success' : 'error'
                );
                
                if (this.soundEnabled) {
                    this.playNotificationSound(newService.status);
                }
            }
        });
    }
    
    updateOverview(summary) {
        const elements = {
            totalServices: document.getElementById('totalServices'),
            onlineServices: document.getElementById('onlineServices'),
            offlineServices: document.getElementById('offlineServices'),
            healthPercentage: document.getElementById('healthPercentage')
        };
        
        if (elements.totalServices) elements.totalServices.textContent = summary.total_services;
        if (elements.onlineServices) elements.onlineServices.textContent = summary.active_services;
        if (elements.offlineServices) elements.offlineServices.textContent = summary.inactive_services;
        if (elements.healthPercentage) elements.healthPercentage.textContent = Math.round(summary.health_percentage) + '%';
        
        // Update health bar with animation
        const healthFill = document.getElementById('healthFill');
        if (healthFill) {
            requestAnimationFrame(() => {
                healthFill.style.width = summary.health_percentage + '%';
            });
        }
        
        // Update page title with status
        document.title = `Services Monitor (${summary.active_services}/${summary.total_services} online)`;
    }
    
    renderServices() {
        const grid = document.getElementById('servicesGrid');
        if (!grid) return;
        
        // Clear existing content
        grid.innerHTML = '';
        
        // Filter services based on current filters
        const filteredServices = this.getFilteredServices();
        
        if (filteredServices.length === 0) {
            grid.innerHTML = '<div class="no-services">No services match the current filters</div>';
            return;
        }
        
        filteredServices.forEach(service => {
            const card = this.createServiceCard(service);
            grid.appendChild(card);
        });
    }
    
    getFilteredServices() {
        let services = Object.values(this.services);
        
        // Filter by status
        if (this.filters.status !== 'all') {
            services = services.filter(service => {
                return this.filters.status === 'online' ? service.status : !service.status;
            });
        }
        
        // Filter by service name
        if (this.filters.service !== 'all') {
            services = services.filter(service => service.service_name === this.filters.service);
        }
        
        return services;
    }
    
    createServiceCard(service) {
        const card = document.createElement('div');
        card.className = `service-card ${this.getServiceStatusClass(service)}`;
        card.id = `service-${service.service_name}`;
        
        const trend = this.getServiceTrend(service.service_name);
        const uptime = this.calculateUptime(service.service_name);
        
        card.innerHTML = `
            <div class="service-header">
                <div class="service-info">
                    <div class="service-icon" style="color: ${this.getServiceColor(service)}">
                        <i class="${service.icon}"></i>
                    </div>
                    <div>
                        <h3 class="service-name">${service.display_name}</h3>
                        <p class="service-address">${service.host}:${service.port}</p>
                    </div>
                </div>
                <div class="service-status">
                    <div class="status-indicator ${this.getServiceStatusClass(service)}"></div>
                    <span class="status-text">${service.status ? 'Online' : 'Offline'}</span>
                    ${trend ? `<div class="trend-indicator ${trend}">
                        <i class="fas fa-${trend === 'up' ? 'arrow-up' : trend === 'down' ? 'arrow-down' : 'minus'}"></i>
                    </div>` : ''}
                </div>
            </div>
            
            <div class="service-details">
                ${this.generateServiceDetails(service)}
                
                <div class="detail-row">
                    <span class="detail-label">Uptime (24h):</span>
                    <span class="detail-value">${uptime}%</span>
                </div>
            </div>
            
            ${service.error ? `<div class="error-message">
                <i class="fas fa-exclamation-triangle"></i> ${service.error}
            </div>` : ''}
            
            <div class="service-actions">
                <button class="action-btn" onclick="monitor.testService('${service.service_name}')">
                    <i class="fas fa-plug"></i> Test
                </button>
                <button class="action-btn" onclick="monitor.showServiceTrend('${service.service_name}')">
                    <i class="fas fa-chart-line"></i> Trend
                </button>
                <button class="action-btn" onclick="monitor.showServiceDetails('${service.service_name}')">
                    <i class="fas fa-info-circle"></i> Details
                </button>
            </div>
            
            <div class="service-trend-mini">
                ${this.createMiniTrendChart(service.service_name)}
            </div>
        `;
        
        return card;
    }
    
    getServiceStatusClass(service) {
        if (this.isRefreshing) return 'checking';
        return service.status ? 'online' : 'offline';
    }
    
    getServiceColor(service) {
        if (this.isRefreshing) return '#ffaa00';
        return service.status ? '#00ff00' : '#ff0040';
    }
    
    generateServiceDetails(service) {
        let details = `
            <div class="detail-row">
                <span class="detail-label">Response Time:</span>
                <span class="detail-value ${this.getResponseTimeClass(service.response_time)}">
                    ${service.response_time ? (service.response_time * 1000).toFixed(0) + 'ms' : 'N/A'}
                </span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Last Check:</span>
                <span class="detail-value">${this.formatRelativeTime(service.checked_at)}</span>
            </div>
        `;
        
        // Add service-specific details
        const additionalDetails = this.getServiceSpecificDetails(service);
        details += additionalDetails;
        
        return details;
    }
    
    getServiceSpecificDetails(service) {
        let details = '';
        
        if (service.version) {
            details += `
                <div class="detail-row">
                    <span class="detail-label">Version:</span>
                    <span class="detail-value">${service.version}</span>
                </div>
            `;
        }
        
        if (service.uptime !== undefined) {
            const uptimeFormatted = this.formatUptime(service.uptime);
            details += `
                <div class="detail-row">
                    <span class="detail-label">Uptime:</span>
                    <span class="detail-value">${uptimeFormatted}</span>
                </div>
            `;
        }
        
        if (service.used_memory) {
            details += `
                <div class="detail-row">
                    <span class="detail-label">Memory:</span>
                    <span class="detail-value">${service.used_memory}</span>
                </div>
            `;
        }
        
        if (service.connected_clients !== undefined || service.connections !== undefined) {
            const connections = service.connected_clients || service.connections || 0;
            details += `
                <div class="detail-row">
                    <span class="detail-label">Connections:</span>
                    <span class="detail-value">${connections}</span>
                </div>
            `;
        }
        
        return details;
    }
    
    getResponseTimeClass(responseTime) {
        if (!responseTime) return '';
        const ms = responseTime * 1000;
        if (ms < 100) return 'response-excellent';
        if (ms < 500) return 'response-good';
        if (ms < 1000) return 'response-fair';
        return 'response-poor';
    }
    
    formatRelativeTime(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = now - time;
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
        if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago';
        return Math.floor(diff / 86400000) + 'd ago';
    }
    
    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) return `${days}d ${hours}h`;
        if (hours > 0) return `${hours}h ${mins}m`;
        return `${mins}m`;
    }
    
    getServiceTrend(serviceName) {
        const history = this.serviceHistory[serviceName];
        if (!history || history.length < 2) return null;
        
        const recent = history.slice(-5);
        const onlineCount = recent.filter(h => h.status).length;
        const totalCount = recent.length;
        
        if (onlineCount === totalCount) return 'up';
        if (onlineCount === 0) return 'down';
        return 'stable';
    }
    
    calculateUptime(serviceName) {
        const history = this.serviceHistory[serviceName];
        if (!history || history.length === 0) return 0;
        
        const onlineCount = history.filter(h => h.status).length;
        return Math.round((onlineCount / history.length) * 100);
    }
    
    createMiniTrendChart(serviceName) {
        const history = this.serviceHistory[serviceName];
        if (!history || history.length < 2) return '<div class="no-trend">No trend data</div>';
        
        const points = history.slice(-10).map((h, i) => {
            const x = (i / 9) * 100;
            const y = h.status ? 20 : 80;
            return `${x},${y}`;
        }).join(' ');
        
        return `
            <svg class="trend-chart" viewBox="0 0 100 100" width="100%" height="30">
                <polyline points="${points}" 
                         fill="none" 
                         stroke="${this.getTrendColor(serviceName)}" 
                         stroke-width="2"/>
            </svg>
        `;
    }
    
    getTrendColor(serviceName) {
        const trend = this.getServiceTrend(serviceName);
        switch (trend) {
            case 'up': return '#00ff00';
            case 'down': return '#ff0040';
            default: return '#ffaa00';
        }
    }
    
    async testService(serviceName) {
        const card = document.getElementById(`service-${serviceName}`);
        if (!card) return;
        
        // Add testing state
        card.classList.add('testing');
        
        try {
            const response = await fetch(`/services_bp/api/status/${serviceName}`);
            const data = await response.json();
            
            if (data.success) {
                // Update service data
                this.services[serviceName] = data.service;
                
                // Re-render the specific card
                const newCard = this.createServiceCard(data.service);
                card.innerHTML = newCard.innerHTML;
                card.className = `service-card ${this.getServiceStatusClass(data.service)}`;
                
                this.showNotification(
                    serviceName,
                    `Test completed: ${data.service.status ? 'Online' : 'Offline'}`,
                    data.service.status ? 'success' : 'warning'
                );
            }
        } catch (error) {
            console.error('Error testing service:', error);
            this.showNotification(serviceName, 'Test failed: ' + error.message, 'error');
        } finally {
            card.classList.remove('testing');
        }
    }
    
    showServiceTrend(serviceName) {
        const service = this.services[serviceName];
        const history = this.serviceHistory[serviceName];
        
        if (!history || history.length < 2) {
            alert('Not enough trend data available for ' + service.display_name);
            return;
        }
        
        // Create a modal or popup with detailed trend chart
        this.createTrendModal(serviceName, service, history);
    }
    
    createTrendModal(serviceName, service, history) {
        // Remove existing modal
        const existingModal = document.getElementById('trendModal');
        if (existingModal) existingModal.remove();
        
        const modal = document.createElement('div');
        modal.id = 'trendModal';
        modal.className = 'modal trend-modal';
        modal.innerHTML = `
            <div class="modal-backdrop" onclick="this.parentElement.remove()"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${service.display_name} - Trend Analysis</h3>
                    <button class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="trend-stats">
                        <div class="stat">
                            <span class="stat-label">Uptime (24h):</span>
                            <span class="stat-value">${this.calculateUptime(serviceName)}%</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Avg Response:</span>
                            <span class="stat-value">${this.calculateAverageResponseTime(serviceName)}ms</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Checks:</span>
                            <span class="stat-value">${history.length}</span>
                        </div>
                    </div>
                    <div class="trend-chart-container">
                        ${this.createDetailedTrendChart(serviceName, history)}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    createDetailedTrendChart(serviceName, history) {
        const chartId = `chart-${serviceName}`;
        return `<canvas id="${chartId}" width="600" height="300"></canvas>`;
    }
    
    calculateAverageResponseTime(serviceName) {
        const history = this.serviceHistory[serviceName];
        if (!history || history.length === 0) return 0;
        
        const validTimes = history.filter(h => h.responseTime !== null);
        if (validTimes.length === 0) return 0;
        
        const sum = validTimes.reduce((acc, h) => acc + (h.responseTime * 1000), 0);
        return Math.round(sum / validTimes.length);
    }
    
    showServiceDetails(serviceName) {
        const service = this.services[serviceName];
        if (!service) return;
        
        const uptime = this.calculateUptime(serviceName);
        const avgResponse = this.calculateAverageResponseTime(serviceName);
        
        const details = `
Service Details for ${service.display_name}

Connection:
• Host: ${service.host}
• Port: ${service.port}
• Status: ${service.status ? 'Online' : 'Offline'}

Performance:
• Response Time: ${service.response_time ? (service.response_time * 1000).toFixed(0) + 'ms' : 'N/A'}
• Average Response: ${avgResponse}ms
• Uptime (24h): ${uptime}%

System Information:
${service.version ? `• Version: ${service.version}` : ''}
${service.uptime !== undefined ? `• System Uptime: ${this.formatUptime(service.uptime)}` : ''}
${service.used_memory ? `• Memory Usage: ${service.used_memory}` : ''}
${service.connected_clients !== undefined ? `• Active Connections: ${service.connected_clients}` : ''}

Last Check: ${new Date(service.checked_at).toLocaleString()}
${service.error ? `\nError: ${service.error}` : ''}
        `.trim();
        
        alert(details);
    }
    
    showLoadingState(isLoading) {
        const refreshBtn = document.querySelector('button[onclick="refreshAll()"]');
        if (refreshBtn) {
            if (isLoading) {
                refreshBtn.disabled = true;
                refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            } else {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh All';
            }
        }
    }
    
    initializeNotifications() {
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
        
        // Create notification container
        if (!document.getElementById('notificationContainer')) {
            const container = document.createElement('div');
            container.id = 'notificationContainer';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
    }
    
    showNotification(serviceName, message, type = 'info') {
        const notification = {
            id: Date.now(),
            serviceName,
            message,
            type,
            timestamp: new Date()
        };
        
        this.notifications.unshift(notification);
        this.renderNotification(notification);
        
        // Browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(`${serviceName} - ${message}`, {
                icon: '/static/img/service-icon.png',
                tag: serviceName
            });
        }
        
        // Auto-remove after 5 seconds
        setTimeout(() => this.removeNotification(notification.id), 5000);
    }
    
    renderNotification(notification) {
        const container = document.getElementById('notificationContainer');
        if (!container) return;
        
        const notifEl = document.createElement('div');
        notifEl.className = `notification notification-${notification.type}`;
        notifEl.id = `notif-${notification.id}`;
        notifEl.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${notification.serviceName}</div>
                <div class="notification-message">${notification.message}</div>
                <div class="notification-time">${notification.timestamp.toLocaleTimeString()}</div>
            </div>
            <button class="notification-close" onclick="monitor.removeNotification(${notification.id})">&times;</button>
        `;
        
        container.appendChild(notifEl);
        
        // Animate in
        requestAnimationFrame(() => {
            notifEl.classList.add('notification-show');
        });
    }
    
    removeNotification(id) {
        const notifEl = document.getElementById(`notif-${id}`);
        if (notifEl) {
            notifEl.classList.remove('notification-show');
            setTimeout(() => notifEl.remove(), 300);
        }
        
        this.notifications = this.notifications.filter(n => n.id !== id);
    }
    
    playNotificationSound(isOnline) {
        if (!this.soundEnabled) return;
        
        // Create audio context if not exists
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        // Play different tones for online/offline
        const frequency = isOnline ? 800 : 400;
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.frequency.value = frequency;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3);
        
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + 0.3);
    }
    
    startAutoRefresh() {
        this.stopAutoRefresh();
        
        const intervalElement = document.getElementById('refreshInterval');
        const interval = intervalElement ? parseInt(intervalElement.value) * 1000 : 10000;
        
        this.autoRefreshInterval = setInterval(() => {
            this.loadServices();
        }, interval);
    }
    
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }
    
    updateLastRefreshTime() {
        const element = document.getElementById('lastUpdateTime');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    }
    
    applyFilters() {
        this.renderServices();
    }
    
    exportReport() {
        const report = {
            timestamp: new Date().toISOString(),
            summary: this.calculateSummary(),
            services: this.services,
            serviceHistory: this.serviceHistory,
            notifications: this.notifications.slice(0, 50) // Last 50 notifications
        };
        
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `services-report-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showNotification('System', 'Report exported successfully', 'success');
    }
    
    calculateSummary() {
        const services = Object.values(this.services);
        const online = services.filter(s => s.status).length;
        const total = services.length;
        
        return {
            total_services: total,
            active_services: online,
            inactive_services: total - online,
            health_percentage: total > 0 ? (online / total) * 100 : 0
        };
    }
    
    saveUserPreferences() {
        const prefs = {
            autoRefresh: document.getElementById('autoRefresh')?.checked || false,
            refreshInterval: document.getElementById('refreshInterval')?.value || '10',
            soundEnabled: this.soundEnabled,
            filters: this.filters
        };
        
        localStorage.setItem('servicesMonitorPrefs', JSON.stringify(prefs));
    }
    
    loadUserPreferences() {
        try {
            const prefs = JSON.parse(localStorage.getItem('servicesMonitorPrefs') || '{}');
            
            const autoRefreshEl = document.getElementById('autoRefresh');
            const refreshIntervalEl = document.getElementById('refreshInterval');
            
            if (autoRefreshEl && prefs.autoRefresh !== undefined) {
                autoRefreshEl.checked = prefs.autoRefresh;
            }
            
            if (refreshIntervalEl && prefs.refreshInterval) {
                refreshIntervalEl.value = prefs.refreshInterval;
            }
            
            if (prefs.soundEnabled !== undefined) {
                this.soundEnabled = prefs.soundEnabled;
            }
            
            if (prefs.filters) {
                this.filters = { ...this.filters, ...prefs.filters };
            }
        } catch (error) {
            console.error('Error loading user preferences:', error);
        }
    }
    
    showError(message) {
        this.showNotification('System', message, 'error');
        console.error(message);
    }
}

// Initialize the monitor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.monitor = new AdvancedServicesMonitor();
});

// Global functions for backward compatibility
function refreshAll() {
    if (window.monitor) {
        window.monitor.loadServices();
    }
}

function exportReport() {
    if (window.monitor) {
        window.monitor.exportReport();
    }
}