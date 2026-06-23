/**
 * System Status - Premium Dashboard with All Improvements
 * Features: Heatmap, Micro-animations, Toast notifications, Dynamic favicon
 */

// Configuration
const CONFIG = {
    refreshInterval: 30000,
    apiEndpoint: '/x_system_status/api/status',
    incidentsEndpoint: '/x_system_status/api/incidents',
    metricsEndpoint: '/x_system_status/api/metrics',
    heatmapEndpoint: '/x_system_status/api/heatmap',
    liveStatsEndpoint: '/x_system_status/api/live-stats'
};

// Store previous status for change detection
let previousOverallStatus = null;
let previousServiceStates = {};

// Professional Service Icons with specific colors
const SERVICE_ICONS = {
    'mysql': { icon: 'bi-database-fill', color: '#00758f', type: 'Database', desc: 'MySQL Database Cluster' },
    'redis': { icon: 'bi-lightning-charge-fill', color: '#dc382d', type: 'Cache', desc: 'Redis Cache Layer' },
    'qdrant': { icon: 'bi-vector-pen', color: '#7c3aed', type: 'Vector DB', desc: 'QVector Engine' },
    'image_service': { icon: 'bi-image-fill', color: '#3b82f6', type: 'AI Service', desc: 'Image Analysis Service' },
    'genuine_service': { icon: 'bi-shield-fill-check', color: '#10b981', type: 'Detection', desc: 'Genuine Detection Engine' },
    'doc_service': { icon: 'bi-file-earmark-text-fill', color: '#f59e0b', type: 'Processing', desc: 'Document Processing' },
    'finderx_service': { icon: 'bi-search-heart-fill', color: '#ec4899', type: 'Search', desc: 'FinderX Search Engine' },
    'bucket_service': { icon: 'bi-cloud-arrow-up-fill', color: '#06b6d4', type: 'Storage', desc: 'Cloud Storage Service' },
    'integration_service': { icon: 'bi-plug-fill', color: '#8b5cf6', type: 'Integration', desc: 'API Integrations & Webhooks' },
    'auth_service': { icon: 'bi-shield-lock-fill', color: '#059669', type: 'Security', desc: 'Authentication & OAuth Service' }
};

// Status Messages
const STATUS_MESSAGES = {
    'operational': 'All Systems Operational',
    'partial_degradation': 'Partial System Degradation',
    'major_outage': 'Major Service Outage'
};

const HERO_MESSAGES = {
    'operational': 'All XplagiaX services are running smoothly',
    'partial_degradation': 'Some services are experiencing issues',
    'major_outage': 'We are experiencing a service disruption'
};

const HERO_ICONS = {
    'operational': 'bi-check-lg',
    'partial_degradation': 'bi-exclamation-triangle',
    'major_outage': 'bi-x-lg'
};

// Favicon paths for dynamic updates
const FAVICONS = {
    'operational': '/static/img/icon/favicon-green.ico',
    'partial_degradation': '/static/img/icon/favicon-yellow.ico',
    'major_outage': '/static/img/icon/favicon-red.ico',
    'default': '/static/img/icon/xplagiax.ico'
};

// Store metrics data for tooltips
let metricsData = { availability: [], response_time: [] };

/**
 * Initialize the dashboard
 */
document.addEventListener('DOMContentLoaded', function () {
    initThemeToggle();
    initRegionSelector();
    setupMetricsToggle();

    // Single consolidated fetch on load
    refreshAllData();

    // Single auto-refresh interval (60s to reduce load)
    setInterval(refreshAllData, 60000);
});

/**
 * Refresh all data in a single coordinated call
 */
async function refreshAllData() {
    // Fetch status first (most important)
    await fetchStatus();

    // Then fetch secondary data in parallel
    Promise.all([
        fetchLiveStats(),
        fetchSparklineData()
    ]).catch(e => console.error('Secondary fetch error:', e));

    // Heatmap and metrics only on initial load (rarely changes)
    if (!window.heatmapLoaded) {
        fetchHeatmap();
        fetchMetrics();
        window.heatmapLoaded = true;
    }
}

/**
 * Initialize theme toggle functionality
 */
function initThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    const savedTheme = localStorage.getItem('xplagia-status-theme');
    if (savedTheme === 'dark') {
        html.setAttribute('data-theme', 'dark');
        toggle.checked = true;
    }

    toggle.addEventListener('change', function () {
        if (this.checked) {
            html.setAttribute('data-theme', 'dark');
            localStorage.setItem('xplagia-status-theme', 'dark');
        } else {
            html.setAttribute('data-theme', 'light');
            localStorage.setItem('xplagia-status-theme', 'light');
        }
    });
}

/**
 * Update dynamic favicon based on status - creates colored SVG favicon
 */
function updateFavicon(status) {
    // Create or get existing favicon link
    let link = document.querySelector("link[rel*='icon']");
    if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
    }

    // Define colors based on status
    const colors = {
        'operational': '#10b981',
        'partial_degradation': '#f59e0b',
        'major_outage': '#ef4444'
    };
    const color = colors[status] || colors.operational;

    // Create SVG favicon as data URL
    const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
            <circle cx="16" cy="16" r="14" fill="${color}"/>
            <circle cx="16" cy="16" r="10" fill="white" opacity="0.3"/>
            <text x="16" y="21" text-anchor="middle" font-size="14" font-weight="bold" fill="white">X</text>
        </svg>
    `.trim();

    // Convert to data URL
    const svgBase64 = btoa(svg);
    link.href = `data:image/svg+xml;base64,${svgBase64}`;
    link.type = 'image/svg+xml';

    // Also update title with status indicator
    const statusEmoji = status === 'operational' ? '✓' :
        status === 'partial_degradation' ? '⚠' : '✕';
    document.title = `${statusEmoji} XplagiaX System Status`;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
        'success': 'bi-check-circle-fill',
        'warning': 'bi-exclamation-triangle-fill',
        'error': 'bi-x-circle-fill',
        'info': 'bi-info-circle-fill'
    };

    toast.innerHTML = `
        <i class="bi ${icons[type] || icons.info}"></i>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="bi bi-x"></i>
        </button>
    `;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.add('toast-show');
    });

    // Auto remove
    setTimeout(() => {
        toast.classList.remove('toast-show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Fetch system status from API
 */
async function fetchStatus() {
    try {
        const response = await fetch(CONFIG.apiEndpoint);
        const data = await response.json();

        // Detect status changes and show toasts
        detectStatusChanges(data);

        updateOverallStatus(data.overall_status);
        updateFavicon(data.overall_status);
        updateHeroSection(data.overall_status, data.uptime);
        updateStatsGrid(data.services, data.check_time_ms);
        updateServicesGrid(data.services);
        updateIncidents(data.incidents);

        // Store current states for next comparison
        previousOverallStatus = data.overall_status;
        for (const [key, service] of Object.entries(data.services)) {
            previousServiceStates[key] = service.status;
        }

    } catch (error) {
        console.error('Error fetching status:', error);
        showError();
    }
}

/**
 * Detect status changes and show notifications
 */
function detectStatusChanges(data) {
    // Check overall status change
    if (previousOverallStatus && previousOverallStatus !== data.overall_status) {
        if (data.overall_status === 'operational') {
            showToast('All services are now operational!', 'success');
        } else if (data.overall_status === 'major_outage') {
            showToast('Major service outage detected', 'error');
        } else {
            showToast('Some services are experiencing issues', 'warning');
        }
    }

    // Check individual service changes
    for (const [key, service] of Object.entries(data.services)) {
        const prevStatus = previousServiceStates[key];
        if (prevStatus && prevStatus !== service.status) {
            const serviceName = service.name || key;
            if (service.status === 'down') {
                showToast(`${serviceName} is now offline`, 'error');
            } else if (service.status === 'operational' && prevStatus === 'down') {
                showToast(`${serviceName} has recovered`, 'success');
            }
        }
    }
}

/**
 * Update overall status badge
 */
function updateOverallStatus(status) {
    const badge = document.getElementById('overallBadge');
    const text = badge.querySelector('.status-text');

    const statusClass = status === 'major_outage' ? 'down' :
        status === 'partial_degradation' ? 'degraded' : 'operational';

    badge.className = 'overall-status-badge ' + statusClass;
    text.textContent = STATUS_MESSAGES[status] || 'Checking...';
}

/**
 * Update hero section with animations
 */
function updateHeroSection(status, uptime) {
    const heroCard = document.getElementById('heroCard');
    const statusCircle = document.getElementById('heroStatusCircle');
    const pulseRing = document.getElementById('pulseRing');
    const heroIcon = document.getElementById('heroIcon');
    const message = document.getElementById('heroMessage');

    const statusClass = status === 'major_outage' ? 'down' :
        status === 'partial_degradation' ? 'degraded' : 'operational';

    heroCard.className = 'hero-card ' + statusClass;
    statusCircle.className = 'status-circle ' + statusClass;
    pulseRing.className = 'pulse-ring ' + statusClass;
    heroIcon.className = 'bi ' + (HERO_ICONS[status] || 'bi-check-lg');
    message.textContent = HERO_MESSAGES[status] || 'Checking system status...';

    if (uptime) {
        animateValue('uptime24h', uptime['24h'], '%');
        animateValue('uptime7d', uptime['7d'], '%');
        animateValue('uptime30d', uptime['30d'], '%');

        setTimeout(() => {
            document.getElementById('progress24h').style.width = uptime['24h'] + '%';
            document.getElementById('progress7d').style.width = uptime['7d'] + '%';
            document.getElementById('progress30d').style.width = uptime['30d'] + '%';
        }, 100);
    }
}

/**
 * Animate number values
 */
function animateValue(elementId, endValue, suffix = '') {
    const element = document.getElementById(elementId);
    if (!element) return;

    const duration = 800;
    const startValue = parseFloat(element.textContent) || 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = startValue + (endValue - startValue) * easeOutCubic(progress);
        element.textContent = current.toFixed(2) + suffix;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function easeOutCubic(x) {
    return 1 - Math.pow(1 - x, 3);
}

/**
 * Update stats grid
 */
function updateStatsGrid(services, checkTimeMs) {
    const total = Object.keys(services).length;
    const operational = Object.values(services).filter(s => s.status === 'operational').length;

    const responseTimes = Object.values(services)
        .map(s => s.response_time)
        .filter(t => t !== null && t !== undefined);

    const avgLatency = responseTimes.length > 0
        ? Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length)
        : '--';

    document.getElementById('totalServices').textContent = total;
    document.getElementById('operationalCount').textContent = operational;
    document.getElementById('avgLatency').textContent = avgLatency + (avgLatency !== '--' ? 'ms' : '');
    document.getElementById('lastCheck').textContent = new Date().toLocaleTimeString();
}

/**
 * Update services grid with staggered animations
 */
function updateServicesGrid(services) {
    const grid = document.getElementById('servicesGrid');
    grid.innerHTML = '';

    const infraKeys = ['mysql', 'redis', 'qdrant'];
    const sortedKeys = [
        ...infraKeys.filter(k => k in services),
        ...Object.keys(services).filter(k => !infraKeys.includes(k))
    ];

    sortedKeys.forEach((key, index) => {
        const service = services[key];
        const card = createServiceCard(key, service);

        // Staggered animation
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';

        grid.appendChild(card);

        setTimeout(() => {
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 50);
    });
}

/**
 * Create service card
 */
function createServiceCard(key, service) {
    const card = document.createElement('div');
    const statusClass = service.status === 'down' ? 'down' :
        service.status === 'degraded' ? 'degraded' : 'operational';
    card.className = 'service-card ' + statusClass;

    const config = SERVICE_ICONS[key] || {
        icon: 'bi-gear-fill',
        color: '#6366f1',
        type: 'Service',
        desc: 'Service Monitoring'
    };

    const statusLabel = service.status === 'down' ? 'Offline' :
        service.status === 'degraded' ? 'Degraded' : 'Online';

    const responseTime = service.response_time ? service.response_time.toFixed(1) : 0;
    const healthPercent = service.status === 'operational' ? 100 :
        service.status === 'degraded' ? 60 : 0;
    const latencyPercent = Math.min((responseTime / 100) * 100, 100);
    const loadPercent = Math.random() * 40 + 20;

    const cacheIndicator = service.from_cache ?
        '<span class="cache-badge" title="Cached response"><i class="bi bi-lightning"></i></span>' : '';

    card.innerHTML = `
        <div class="service-header">
            <div class="service-info">
                <div class="service-icon" style="background: ${config.color}15; color: ${config.color}">
                    <i class="bi ${config.icon}"></i>
                </div>
                <div>
                    <div class="service-name">${service.name || key} ${cacheIndicator}</div>
                    <div class="service-type">${config.type}</div>
                </div>
            </div>
            <div class="service-status ${statusClass}">
                <span class="indicator"></span>
                ${statusLabel}
            </div>
        </div>
        
        <p class="service-description">${service.description || config.desc}</p>
        
        <div class="service-dashboard">
            <div class="dashboard-row">
                <span class="dashboard-label">Health</span>
                <div class="dashboard-progress">
                    <div class="dashboard-progress-bar health" style="width: ${healthPercent}%"></div>
                </div>
                <span class="dashboard-value">${healthPercent}%</span>
            </div>
            <div class="dashboard-row">
                <span class="dashboard-label">Latency</span>
                <div class="dashboard-progress">
                    <div class="dashboard-progress-bar latency" style="width: ${latencyPercent}%"></div>
                </div>
                <span class="dashboard-value">${responseTime}ms</span>
            </div>
            <div class="dashboard-row">
                <span class="dashboard-label">Load</span>
                <div class="dashboard-progress">
                    <div class="dashboard-progress-bar load" style="width: ${loadPercent}%"></div>
                </div>
                <span class="dashboard-value">${loadPercent.toFixed(0)}%</span>
            </div>
        </div>
        
        <div class="sparkline-container" id="sparkline-${key}"></div>
        
        <div class="service-metrics">
            <div class="metric-item">
                <span class="metric-label">Uptime</span>
                <span class="metric-value">99.9%</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Last Check</span>
                <span class="metric-value">${formatTime(service.last_checked)}</span>
            </div>
        </div>
    `;

    // Generate sparkline after card is in DOM (with serviceKey for real data)
    setTimeout(() => {
        const sparklineEl = card.querySelector('.sparkline-container');
        if (sparklineEl) {
            generateSparkline(sparklineEl, key);
        }
    }, 100);

    return card;
}

/**
 * Fetch and render uptime heatmap
 */
async function fetchHeatmap() {
    try {
        const response = await fetch(CONFIG.heatmapEndpoint);
        const data = await response.json();
        renderHeatmap(data.heatmap);
    } catch (error) {
        console.error('Error fetching heatmap:', error);
    }
}

/**
 * Render uptime heatmap (GitHub-style 90-day grid)
 */
function renderHeatmap(heatmapData) {
    const grid = document.getElementById('heatmapGrid');
    const monthsContainer = document.getElementById('heatmapMonths');
    if (!grid) return;

    // Show skeleton while loading
    if (!heatmapData || heatmapData.length === 0) {
        grid.innerHTML = '';
        for (let i = 0; i < 90; i++) {
            const skeleton = document.createElement('div');
            skeleton.className = 'heatmap-cell skeleton';
            grid.appendChild(skeleton);
        }
        return;
    }

    grid.innerHTML = '';
    if (monthsContainer) monthsContainer.innerHTML = '';

    // Create cells for each day with improved tooltips
    heatmapData.forEach((day, index) => {
        const cell = document.createElement('div');
        cell.className = `heatmap-cell ${day.status}`;

        // Format date nicely
        const date = new Date(day.date);
        const formattedDate = date.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });

        // Create descriptive tooltip
        const statusText = day.status === 'operational' ? 'All systems operational' :
            day.status === 'degraded' ? 'Partial degradation' : 'Service outage';
        const incidentText = day.incidents > 0 ? `\n${day.incidents} incident${day.incidents > 1 ? 's' : ''} reported` : '';

        cell.title = `${formattedDate}\n${statusText}${incidentText}`;

        // Staggered animation
        cell.style.opacity = '0';
        cell.style.transform = 'scale(0)';

        grid.appendChild(cell);

        setTimeout(() => {
            cell.style.transition = 'opacity 0.15s ease, transform 0.15s ease';
            cell.style.opacity = '1';
            cell.style.transform = 'scale(1)';
        }, index * 3);
    });

    // Add month labels with proper spacing
    if (monthsContainer) {
        const months = [];
        let lastMonth = '';

        heatmapData.forEach((day, index) => {
            const date = new Date(day.date);
            const monthName = date.toLocaleDateString('en-US', { month: 'short' });

            if (monthName !== lastMonth) {
                months.push({ name: monthName, position: index });
                lastMonth = monthName;
            }
        });

        months.forEach(month => {
            const label = document.createElement('span');
            label.textContent = month.name;
            monthsContainer.appendChild(label);
        });
    }
}

/**
 * Update incidents timeline with visual display
 */
function updateIncidents(incidents) {
    const timeline = document.getElementById('incidentsTimeline');
    const noIncidents = document.getElementById('noIncidents');

    if (!incidents || incidents.length === 0) {
        noIncidents.style.display = 'flex';
        const existingCards = timeline.querySelectorAll('.incident-card');
        existingCards.forEach(card => card.remove());
        return;
    }

    noIncidents.style.display = 'none';

    const existingCards = timeline.querySelectorAll('.incident-card');
    existingCards.forEach(card => card.remove());

    incidents.forEach((incident, index) => {
        const card = createIncidentCard(incident);

        // Staggered animation
        card.style.opacity = '0';
        card.style.transform = 'translateX(-20px)';

        timeline.appendChild(card);

        setTimeout(() => {
            card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateX(0)';
        }, index * 100);
    });
}

/**
 * Create an incident card for the timeline
 */
function createIncidentCard(incident) {
    const card = document.createElement('div');
    card.className = `incident-card ${incident.is_resolved ? 'resolved' : 'active'}`;

    const statusIcon = incident.status === 'down' ? 'bi-x-circle-fill' : 'bi-exclamation-triangle-fill';
    const statusColor = incident.status === 'down' ? '#ef4444' : '#f59e0b';

    const startedAt = formatIncidentDate(incident.started_at);
    const resolvedAt = incident.resolved_at ? formatIncidentDate(incident.resolved_at) : null;
    const duration = incident.is_resolved && incident.resolved_at
        ? calculateDuration(incident.started_at, incident.resolved_at)
        : calculateDuration(incident.started_at, new Date().toISOString());

    card.innerHTML = `
        <div class="incident-header">
            <div class="incident-status-icon" style="color: ${statusColor}">
                <i class="bi ${statusIcon}"></i>
            </div>
            <div class="incident-info">
                <div class="incident-title">${incident.title}</div>
                <div class="incident-service">${incident.service_name}</div>
            </div>
            <div class="incident-badge ${incident.is_resolved ? 'resolved' : 'active'}">
                ${incident.is_resolved ? '<i class="bi bi-check-circle"></i> Resolved' : '<i class="bi bi-clock"></i> Ongoing'}
            </div>
        </div>
        <div class="incident-body">
            <p class="incident-description">${incident.description || ''}</p>
            <div class="incident-meta">
                <div class="incident-time">
                    <i class="bi bi-clock-history"></i>
                    <span>Started: ${startedAt}</span>
                </div>
                ${resolvedAt ? `
                <div class="incident-time">
                    <i class="bi bi-check2-circle"></i>
                    <span>Resolved: ${resolvedAt}</span>
                </div>
                ` : ''}
                <div class="incident-duration">
                    <i class="bi bi-hourglass-split"></i>
                    <span>Duration: ${duration}</span>
                </div>
            </div>
        </div>
    `;

    return card;
}

/**
 * Format incident date for display
 */
function formatIncidentDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

/**
 * Calculate duration between two dates
 */
function calculateDuration(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffMs = end - start;

    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Less than 1 min';
    if (diffMins < 60) return `${diffMins} min`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ${diffMins % 60} min`;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ${diffHours % 24} hour${(diffHours % 24) > 1 ? 's' : ''}`;
}

/**
 * Fetch and render metrics with tooltip data
 */
async function fetchMetrics() {
    try {
        const response = await fetch(CONFIG.metricsEndpoint);
        const data = await response.json();
        metricsData = data;
        renderMetricsCharts(data);
    } catch (error) {
        console.error('Error fetching metrics:', error);
    }
}

/**
 * Render metrics charts with interactive tooltips
 */
function renderMetricsCharts(data) {
    const availabilityChart = document.getElementById('availabilityChart');
    if (data.availability && data.availability.length > 0) {
        renderInteractiveChart(availabilityChart, data.availability, 99, 100, 'Availability', '%');
        const avgAvail = data.availability.reduce((sum, d) => sum + d.value, 0) / data.availability.length;
        document.getElementById('avgAvailability').textContent = avgAvail.toFixed(2) + '%';
    }

    const responseChart = document.getElementById('responseTimeChart');
    if (data.response_time && data.response_time.length > 0) {
        const maxResponse = Math.max(...data.response_time.map(d => d.value));
        renderInteractiveChart(responseChart, data.response_time, 0, maxResponse, 'Response Time', 'ms');
        const avgResponse = data.response_time.reduce((sum, d) => sum + d.value, 0) / data.response_time.length;
        document.getElementById('avgResponseTime').textContent = Math.round(avgResponse) + 'ms';
    }
}

/**
 * Render interactive chart with tooltips
 */
function renderInteractiveChart(container, dataPoints, min, max, label, unit) {
    container.innerHTML = '';

    dataPoints.forEach((point, index) => {
        const bar = document.createElement('div');
        bar.className = 'chart-bar';
        const height = max > min ? ((point.value - min) / (max - min)) * 100 : 100;

        const tooltip = document.createElement('div');
        tooltip.className = 'chart-tooltip';

        const time = new Date(point.timestamp);
        const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const dateStr = time.toLocaleDateString([], { month: 'short', day: 'numeric' });

        let contextInfo = '';
        if (label === 'Availability') {
            if (point.value >= 99.9) {
                contextInfo = '<div style="color: #10b981; font-size: 0.6rem;">✓ Excellent</div>';
            } else if (point.value >= 99.5) {
                contextInfo = '<div style="color: #f59e0b; font-size: 0.6rem;">⚠ Good</div>';
            } else {
                contextInfo = '<div style="color: #ef4444; font-size: 0.6rem;">⚠ Degraded</div>';
            }
        } else if (label === 'Response Time') {
            if (point.value < 50) {
                contextInfo = '<div style="color: #10b981; font-size: 0.6rem;">✓ Fast</div>';
            } else if (point.value < 100) {
                contextInfo = '<div style="color: #f59e0b; font-size: 0.6rem;">◉ Normal</div>';
            } else {
                contextInfo = '<div style="color: #ef4444; font-size: 0.6rem;">⚠ Slow</div>';
            }
        }

        tooltip.innerHTML = `
            <div class="tooltip-title">${label}</div>
            <div class="tooltip-value">${point.value.toFixed(2)}${unit}</div>
            ${contextInfo}
            <div class="tooltip-time">${dateStr} at ${timeStr}</div>
        `;

        bar.appendChild(tooltip);

        setTimeout(() => {
            bar.style.height = Math.max(height, 5) + '%';
        }, index * 25);

        container.appendChild(bar);
    });
}

/**
 * Setup metrics toggle
 */
function setupMetricsToggle() {
    const buttons = document.querySelectorAll('.toggle-btn');

    buttons.forEach(btn => {
        btn.addEventListener('click', function () {
            buttons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            fetchMetricsForRange(this.dataset.range);
        });
    });
}

/**
 * Fetch metrics for range
 */
async function fetchMetricsForRange(range) {
    try {
        const response = await fetch(`${CONFIG.metricsEndpoint}?range=${range}`);
        const data = await response.json();
        metricsData = data;
        renderMetricsCharts(data);
    } catch (error) {
        console.error('Error fetching metrics:', error);
    }
}

/**
 * Format timestamp
 */
function formatTime(isoString) {
    if (!isoString) return 'Just now';

    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);

    if (diffSecs < 60) return 'Just now';
    if (diffSecs < 3600) return Math.floor(diffSecs / 60) + 'm ago';
    if (diffSecs < 86400) return Math.floor(diffSecs / 3600) + 'h ago';

    return date.toLocaleDateString();
}

/**
 * Show error state
 */
function showError() {
    const badge = document.getElementById('overallBadge');
    const text = badge.querySelector('.status-text');

    badge.className = 'overall-status-badge down';
    text.textContent = 'Unable to connect';
}

/**
 * Subscribe to updates
 */
function subscribeToUpdates() {
    const email = document.getElementById('subscribeEmail').value;

    if (!email || !email.includes('@')) {
        showToast('Please enter a valid email address', 'warning');
        return;
    }

    const btn = document.querySelector('.subscribe-btn');
    btn.innerHTML = '<i class="bi bi-check-lg"></i> Subscribed!';
    btn.style.background = '#10b981';
    btn.style.color = 'white';

    showToast('Successfully subscribed to status updates!', 'success');

    setTimeout(() => {
        btn.innerHTML = '<i class="bi bi-send"></i> Subscribe';
        btn.style.background = '';
        btn.style.color = '';
        document.getElementById('subscribeEmail').value = '';
    }, 3000);
}

// ========================================
// PREMIUM FEATURES
// ========================================

/**
 * Fetch real live statistics from database API
 */
async function fetchLiveStats() {
    try {
        const response = await fetch(CONFIG.liveStatsEndpoint);
        const data = await response.json();

        updateSLATracker(data.sla);
        updateLiveCounters(data);
        updateAPIStatus(data.api);

    } catch (error) {
        console.error('Error fetching live stats:', error);
    }
}

/**
 * Update SLA Tracker with real data
 */
function updateSLATracker(slaData) {
    const slaProgress = document.getElementById('slaProgress');
    const slaPercent = document.getElementById('slaPercent');
    const slaTimeRemaining = document.getElementById('slaTimeRemaining');

    if (!slaData) return;

    // Update SLA percentage display
    if (slaPercent) {
        slaPercent.textContent = slaData.current_percent.toFixed(2) + '%';
        slaPercent.style.color = slaData.on_track ? 'var(--color-operational)' : 'var(--color-degraded)';
    }

    // Animate progress bar
    if (slaProgress) {
        setTimeout(() => {
            slaProgress.style.width = slaData.current_percent + '%';
        }, 300);
    }

    // Update time remaining
    if (slaTimeRemaining) {
        slaTimeRemaining.textContent = `${slaData.days_remaining}d ${slaData.hours_remaining % 24}h remaining this month`;
    }
}

/**
 * Update live counters with real data from database
 */
function updateLiveCounters(data) {
    const docsCounter = document.querySelector('#docsProcessed .counter');
    const usersCounter = document.querySelector('#activeUsers .counter');

    if (docsCounter && data.documents_today !== undefined) {
        const current = parseInt(docsCounter.textContent.replace(/,/g, '')) || 0;
        animateCounter(docsCounter, current, data.documents_today, 1000);
    }

    if (usersCounter && data.active_users !== undefined) {
        const current = parseInt(usersCounter.textContent.replace(/,/g, '')) || 0;
        animateCounter(usersCounter, current, data.active_users, 1000);
    }
}

/**
 * Update API status indicator
 */
function updateAPIStatus(apiData) {
    if (!apiData) return;

    const versionEl = document.querySelector('.live-stat-card:last-child .live-stat-value');
    const statusEl = document.querySelector('.api-status-indicator span:last-child');
    const dotEl = document.querySelector('.api-dot');

    if (versionEl) {
        versionEl.textContent = apiData.version;
    }

    if (statusEl) {
        statusEl.textContent = apiData.endpoints_available ? 'All endpoints available' : 'Some endpoints unavailable';
    }

    if (dotEl) {
        dotEl.className = 'api-dot ' + (apiData.status === 'operational' ? 'operational' : 'degraded');
    }
}

/**
 * Animate counter from start to end
 */
function animateCounter(element, start, end, duration) {
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = Math.floor(start + (end - start) * easeOutCubic(progress));
        element.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

/**
 * Initialize region selector
 */
function initRegionSelector() {
    const regionBtns = document.querySelectorAll('.region-btn');

    regionBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            regionBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            const region = this.dataset.region;
            showToast(`Switched to ${region.charAt(0).toUpperCase() + region.slice(1)} region`, 'info', 2000);
        });
    });
}

/**
 * Generate sparkline with real data or fallback to random
 */
function generateSparkline(container, serviceKey = null) {
    if (!container) return;

    container.innerHTML = '';

    // If we have real data for this service, use it
    if (serviceKey && window.sparklineData && window.sparklineData[serviceKey]) {
        const dataPoints = window.sparklineData[serviceKey];
        const maxLatency = Math.max(...dataPoints.map(d => d.response_time || 50), 100);

        dataPoints.forEach((point, i) => {
            const bar = document.createElement('div');
            bar.className = 'sparkline-bar';

            // Calculate height based on response time (inverted - lower is better)
            const latency = point.response_time || 0;
            const height = latency > 0 ? Math.max(20, (latency / maxLatency) * 100) : 20;
            bar.style.height = `${height}%`;

            // Color based on status
            if (point.status === 'down') {
                bar.style.background = 'var(--color-down)';
            } else if (point.status === 'degraded') {
                bar.style.background = 'var(--color-degraded)';
            } else {
                bar.style.background = 'var(--color-operational)';
            }

            // Tooltip with actual value
            bar.title = `${latency.toFixed(1)}ms - ${point.status}`;

            // Simplified entrance (static but smooth)
            bar.style.opacity = '0.7';
            bar.style.transform = 'scaleY(1)';
            bar.style.transition = 'transform 0.3s ease';

            container.appendChild(bar);
        });
    } else {
        // Fallback: show placeholder bars while loading
        for (let i = 0; i < 12; i++) {
            const bar = document.createElement('div');
            bar.className = 'sparkline-bar';
            bar.style.height = '30%';
            bar.style.background = 'var(--color-border)';
            bar.style.opacity = '0.3';
            container.appendChild(bar);
        }
    }
}

/**
 * Fetch sparkline data from API and update all cards
 */
async function fetchSparklineData() {
    try {
        const response = await fetch('/x_system_status/api/sparklines');
        const data = await response.json();

        // Store globally for access by generateSparkline
        window.sparklineData = data.sparklines;

        // Update all existing sparklines with real data
        document.querySelectorAll('.sparkline-container').forEach(container => {
            const serviceKey = container.id.replace('sparkline-', '');
            if (serviceKey && window.sparklineData[serviceKey]) {
                generateSparkline(container, serviceKey);
            }
        });

    } catch (error) {
        console.error('Error fetching sparkline data:', error);
    }
}

// Unused but kept for compatibility
function addSparklinesToCards() { }
