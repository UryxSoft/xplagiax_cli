// ============================================
// HISTORY SIDEBAR DROPDOWN
// ============================================

// Variables para el historial del sidebar
let sidebarHistoryOpen = false;

// Inicializar el dropdown del historial en el sidebar
document.addEventListener('DOMContentLoaded', function() {
    const historyLink = document.querySelector('a[href="/history"]');
    if (historyLink) {
        initSidebarHistory(historyLink);
    }
});

async function initSidebarHistory(historyLink) {
    // Crear el contenedor del dropdown
    const dropdownContainer = document.createElement('div');
    dropdownContainer.className = 'history-dropdown';
    dropdownContainer.innerHTML = `
        <div class="history-dropdown-list" id="historyDropdownList">
            <div class="history-loading">Loading...</div>
        </div>
        <div class="history-dropdown-footer">
            <a href="/history" class="view-all-link" onclick="event.stopPropagation()">View all</a>
        </div>
    `;
    
    // Insertar después del link dentro del li (nav-rail usa <a> directo, no <li>)
    const listItem = historyLink.closest('li');
    if (!listItem) return;
    listItem.appendChild(dropdownContainer);
    
    // Toggle dropdown al hacer click
    historyLink.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        toggleSidebarHistory();
    });
    
    // Agregar indicador visual de dropdown
    const linkSpan = historyLink.querySelector('.link');
    if (linkSpan) {
        const arrow = document.createElement('span');
        arrow.className = 'history-arrow';
        arrow.innerHTML = '▼';
        linkSpan.appendChild(arrow);
    }
    
    // Cargar historial inicial
    loadSidebarHistory();
}

function toggleSidebarHistory() {
    const dropdown = document.querySelector('.history-dropdown');
    const historyLink = document.querySelector('a[href="/history"]');
    sidebarHistoryOpen = !sidebarHistoryOpen;
    
    if (sidebarHistoryOpen) {
        dropdown.classList.add('active');
        historyLink.classList.add('dropdown-active');
        loadSidebarHistory();
    } else {
        dropdown.classList.remove('active');
        historyLink.classList.remove('dropdown-active');
    }
}

async function loadSidebarHistory() {
    try {
        const response = await fetch('/api/historial/data');
        const data = await response.json();
        
        if (data.success && data.data.length > 0) {
            displaySidebarHistory(data.data);
        } else {
            displayEmptyHistory();
        }
    } catch (error) {
        console.error('Error loading sidebar history:', error);
        displayErrorHistory();
    }
}

function displaySidebarHistory(items) {
    const listContainer = document.getElementById('historyDropdownList');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Agrupar por fecha
    const groupedItems = groupByDate(items, today);
    
    let html = '';
    
    // Esta semana
    if (groupedItems.thisWeek.length > 0) {
        html += '<div class="history-group-title">This week</div>';
        groupedItems.thisWeek.forEach(item => {
            html += createHistoryItem(item, today);
        });
    }
    
    // October/mes actual
    if (groupedItems.thisMonth.length > 0) {
        const monthName = getMonthName(new Date(groupedItems.thisMonth[0].date));
        html += `<div class="history-group-title">${monthName}</div>`;
        groupedItems.thisMonth.forEach(item => {
            html += createHistoryItem(item, today);
        });
    }
    
    // September/mes anterior
    if (groupedItems.lastMonth.length > 0) {
        const lastMonthName = getMonthName(new Date(groupedItems.lastMonth[0].date));
        html += `<div class="history-group-title">${lastMonthName}</div>`;
        groupedItems.lastMonth.forEach(item => {
            html += createHistoryItem(item, today);
        });
    }
    
    listContainer.innerHTML = html || '<div class="history-empty">No recent documents</div>';
    
    // Agregar event listeners a los items
    document.querySelectorAll('.history-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.stopPropagation();
            const analysisId = this.dataset.analysisId;
            verDetalle(analysisId);
        });
    });
}

function createHistoryItem(item, today) {
    const itemDate = new Date(item.date);
    const truncatedName = truncateText(item.document, 30);
    const timeOrDate = formatTimeOrDate(itemDate, today);
    
    return `
        <div class="history-item" data-analysis-id="${item.analysis_id}">
            <div class="history-item-content">
                <div class="history-item-name" title="${item.document}">${truncatedName}</div>
                <!--<div class="history-item-meta">${timeOrDate}</div>-->
            </div>
        </div>
    `;
}

function groupByDate(items, today) {
    const thisWeek = [];
    const thisMonth = [];
    const lastMonth = [];
    
    const oneWeekAgo = new Date(today);
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    
    const thisMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    
    items.forEach(item => {
        const itemDate = new Date(item.date);
        itemDate.setHours(0, 0, 0, 0);
        
        if (itemDate >= oneWeekAgo) {
            thisWeek.push(item);
        } else if (itemDate >= thisMonthStart) {
            thisMonth.push(item);
        } else if (itemDate >= lastMonthStart) {
            lastMonth.push(item);
        }
    });
    
    return { thisWeek, thisMonth, lastMonth };
}

function formatTimeOrDate(date, today) {
    const itemDate = new Date(date);
    itemDate.setHours(0, 0, 0, 0);
    
    const diffTime = today - itemDate;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        // Hoy - mostrar hora
        return new Date(date).toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    } else if (diffDays < 7) {
        // Esta semana - mostrar día
        return new Date(date).toLocaleDateString('es-ES', { 
            weekday: 'long' 
        });
    } else {
        // Más antiguo - mostrar fecha
        return new Date(date).toLocaleDateString('es-ES', { 
            day: 'numeric',
            month: 'short'
        });
    }
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + '...';
}

function getMonthName(date) {
    return date.toLocaleDateString('es-ES', { month: 'long' });
}

function displayEmptyHistory() {
    const listContainer = document.getElementById('historyDropdownList');
    listContainer.innerHTML = '<div class="history-empty">No recent documents</div>';
}

function displayErrorHistory() {
    const listContainer = document.getElementById('historyDropdownList');
    listContainer.innerHTML = '<div class="history-error">Error al cargar historial</div>';
}

// Cerrar dropdown al hacer click fuera
document.addEventListener('click', function(e) {
    const dropdown = document.querySelector('.history-dropdown');
    const historyLink = document.querySelector('a[href="/history"]');
    
    if (dropdown && historyLink && sidebarHistoryOpen) {
        if (!dropdown.contains(e.target) && !historyLink.contains(e.target)) {
            dropdown.classList.remove('active');
            historyLink.classList.remove('dropdown-active');
            sidebarHistoryOpen = false;
        }
    }
});