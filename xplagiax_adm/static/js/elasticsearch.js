// Configuración global
const API_BASE_URL = 'http://localhost:5000/api';
let selectedIndex = null;
let networkChart = null;
let distributionChart = null;
let categoriesChart = null;
let currentGraphData = null;

// Inicializar aplicación
async function initApp() {
console.log('🚀 Iniciando Elasticsearch Visualizer...');
await loadIndices();
}

// Cargar lista de índices
async function loadIndices() {
try {
    console.log('📥 Cargando índices...');
    const response = await fetch(`${API_BASE_URL}/elasticsearch/indices`);
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    renderIndices(data.indices);
    
} catch (error) {
    console.error('❌ Error cargando índices:', error);
    showError('Error cargando índices: ' + error.message);
}
}

// Renderizar grid de índices
function renderIndices(indices) {
const grid = document.getElementById('indicesGrid');

if (indices.length === 0) {
    grid.innerHTML = '<div class="error-message">No se encontraron índices en Elasticsearch</div>';
    return;
}

grid.innerHTML = '';

indices.forEach(index => {
    const card = document.createElement('div');
    card.className = 'index-card';
    card.onclick = () => selectIndex(index.name);
    
    card.innerHTML = `
        <div class="index-name">${index.name}</div>
        <div class="index-stats">
            📄 ${index.doc_count.toLocaleString()} documentos | 
            💾 ${index.size_mb} MB | 
            🏷️ ${index.fields_count} campos
        </div>
    `;
    
    grid.appendChild(card);
});

console.log(`✅ ${indices.length} índices cargados`);
}

// Seleccionar índice
async function selectIndex(indexName) {
console.log(`🎯 Seleccionando índice: ${indexName}`);

// Actualizar UI
document.querySelectorAll('.index-card').forEach(card => {
    card.classList.remove('selected');
});
event.target.closest('.index-card').classList.add('selected');

selectedIndex = indexName;

// Mostrar contenedores de visualización
document.getElementById('statsBar').style.display = 'grid';
document.getElementById('chartsContainer').style.display = 'grid';
document.getElementById('dataTableContainer').style.display = 'block';

// Cargar datos
await loadIndexData();
}

// Cargar datos del índice seleccionado
async function loadIndexData() {
if (!selectedIndex) return;

try {
    console.log(`📊 Cargando datos de ${selectedIndex}...`);
    
    // Cargar datos para gráfica de red
    const maxNodes = document.getElementById('maxNodesSelect').value;
    const [graphData, indexData, aggregations] = await Promise.all([
        fetch(`${API_BASE_URL}/elasticsearch/index/${selectedIndex}/graph?max_nodes=${maxNodes}`).then(r => r.json()),
        fetch(`${API_BASE_URL}/elasticsearch/index/${selectedIndex}/data?size=100`).then(r => r.json()),
        fetch(`${API_BASE_URL}/elasticsearch/index/${selectedIndex}/aggregations`).then(r => r.json())
    ]);
    
    currentGraphData = graphData;
    
    // Actualizar estadísticas
    updateStats(graphData, indexData);
    
    // Crear visualizaciones
    createNetworkChart(graphData);
    createDistributionChart(aggregations);
    createCategoriesChart(graphData);
    updateDataTable(indexData);
    
    showNotification(`✅ Datos de ${selectedIndex} cargados correctamente`);
    
} catch (error) {
    console.error('❌ Error cargando datos:', error);
    showError('Error cargando datos: ' + error.message);
}
}

// Actualizar estadísticas
function updateStats(graphData, indexData) {
document.getElementById('totalDocs').textContent = indexData.total_hits.toLocaleString();
document.getElementById('indexSize').textContent = indexData.stats.size_mb + ' MB';
document.getElementById('totalNodes').textContent = graphData.nodes.length.toLocaleString();
document.getElementById('totalConnections').textContent = graphData.links.length.toLocaleString();
}

// Crear gráfica de red
function createNetworkChart(data) {
const container = document.getElementById('networkChart');
container.innerHTML = '';

if (networkChart) {
    networkChart.dispose();
}

networkChart = echarts.init(container);

const option = {
    title: {
        text: `Red de Datos - ${selectedIndex}`,
        subtext: `${data.nodes.length} nodos, ${data.links.length} conexiones`,
        left: 'center',
        textStyle: { fontSize: 16 }
    },
    tooltip: {
        trigger: 'item',
        formatter: function(params) {
            if (params.dataType === 'node') {
                const nodeData = params.data.data;
                let tooltip = `<strong>${params.data.name}</strong><br/>`;
                tooltip += `Categoría: ${params.data.category}<br/>`;
                tooltip += `Tamaño: ${params.data.value}<br/>`;
                
                // Mostrar algunos campos del documento
                const fields = Object.keys(nodeData).slice(0, 5);
                fields.forEach(field => {
                    const value = nodeData[field];
                    const displayValue = typeof value === 'string' && value.length > 50 
                        ? value.substring(0, 50) + '...' 
                        : value;
                    tooltip += `${field}: ${displayValue}<br/>`;
                });
                
                return tooltip;
            } else if (params.dataType === 'edge') {
                return `Conexión: ${params.data.source} → ${params.data.target}<br/>Peso: ${params.data.value}`;
            }
        }
    },
    legend: {
        data: data.categories.map(cat => cat.name),
        orient: 'horizontal',
        bottom: 10
    },
    animationDuration: 1500,
    animationEasingUpdate: 'quinticInOut',
    series: [{
        name: 'Network',
        type: 'graph',
        layout: 'force',
        data: data.nodes,
        links: data.links,
        categories: data.categories,
        roam: true,
        focusNodeAdjacency: true,
        itemStyle: {
            borderColor: '#fff',
            borderWidth: 1,
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
        },
        lineStyle: {
            color: 'rgba(50, 50, 50, 0.5)',
            curveness: 0.1
        },
        emphasis: {
            focus: 'adjacency',
            lineStyle: {
                width: 4
            }
        },
        force: {
            repulsion: 2000,
            gravity: 0.1,
            edgeLength: [50, 200],
            layoutAnimation: true
        },
        label: {
            show: true,
            position: 'right',
            formatter: '{b}'
        }
    }]
};

networkChart.setOption(option);

// Agregar evento de click
networkChart.on('click', function(params) {
    if (params.dataType === 'node') {
        console.log('Nodo clickeado:', params.data);
        showNodeDetails(params.data);
    }
});
}

// Crear gráfica de distribución
function createDistributionChart(aggregations) {
const container = document.getElementById('distributionChart');
container.innerHTML = '';

if (distributionChart) {
    distributionChart.dispose();
}

distributionChart = echarts.init(container);

// Buscar agregación de histograma de fecha
let chartData = [];
let chartTitle = 'Distribución de Documentos';

for (const [aggName, aggData] of Object.entries(aggregations.aggregations)) {
    if (aggData.type === 'buckets' && aggData.data.length > 0) {
        chartData = aggData.data.map(bucket => ({
            name: bucket.key_as_string || bucket.key,
            value: bucket.doc_count
        }));
        chartTitle = `Distribución por ${aggName.replace('top_', '').replace('date_', '')}`;
        break;
    }
}

// Si no hay datos de agregación, crear distribución por categorías de la gráfica
if (chartData.length === 0 && currentGraphData) {
    const categoryCounts = {};
    currentGraphData.nodes.forEach(node => {
        const catName = currentGraphData.categories[node.category]?.name || 'Sin categoría';
        categoryCounts[catName] = (categoryCounts[catName] || 0) + 1;
    });
    
    chartData = Object.entries(categoryCounts).map(([name, value]) => ({ name, value }));
    chartTitle = 'Distribución por Categorías';
}

const option = {
    title: {
        text: chartTitle,
        left: 'center'
    },
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'shadow'
        }
    },
    xAxis: {
        type: 'category',
        data: chartData.map(item => item.name),
        axisLabel: {
            rotate: 45,
            interval: 0
        }
    },
    yAxis: {
        type: 'value'
    },
    series: [{
        data: chartData.map(item => item.value),
        type: 'bar',
        itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#83bff6' },
                { offset: 0.5, color: '#188df0' },
                { offset: 1, color: '#188df0' }
            ])
        },
        emphasis: {
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#2378f7' },
                    { offset: 0.7, color: '#2378f7' },
                    { offset: 1, color: '#83bff6' }
                ])
            }
        }
    }]
};

distributionChart.setOption(option);
}

// Crear gráfica de categorías (pie chart)
function createCategoriesChart(data) {
const container = document.getElementById('categoriesChart');
container.innerHTML = '';

if (categoriesChart) {
    categoriesChart.dispose();
}

categoriesChart = echarts.init(container);

// Contar nodos por categoría
const categoryCounts = {};
data.nodes.forEach(node => {
    const catName = data.categories[node.category]?.name || 'Sin categoría';
    categoryCounts[catName] = (categoryCounts[catName] || 0) + 1;
});

const pieData = Object.entries(categoryCounts).map(([name, value]) => ({
    name,
    value,
    itemStyle: {
        color: data.categories.find(cat => cat.name === name)?.itemStyle?.color || '#999'
    }
}));

const option = {
    title: {
        text: 'Distribución por Categorías',
        left: 'center'
    },
    tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b} : {c} ({d}%)'
    },
    legend: {
        orient: 'vertical',
        left: 'left',
        data: pieData.map(item => item.name)
    },
    series: [{
        name: 'Categorías',
        type: 'pie',
        radius: '50%',
        data: pieData,
        emphasis: {
            itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
        }
    }]
};

categoriesChart.setOption(option);
}

// Actualizar tabla de datos
function updateDataTable(data) {
const tbody = document.getElementById('dataTableBody');
tbody.innerHTML = '';

data.documents.slice(0, 50).forEach(doc => {
    const row = document.createElement('tr');
    
    // Preparar datos para mostrar
    const sourceStr = JSON.stringify(doc.source, null, 2);
    const truncatedSource = sourceStr.length > 200 
        ? sourceStr.substring(0, 200) + '...' 
        : sourceStr;
    
    row.innerHTML = `
        <td>${doc.id}</td>
        <td>${doc.score.toFixed(2)}</td>
        <td><pre style="font-size: 11px; margin: 0;">${truncatedSource}</pre></td>
    `;
    
    row.onclick = () => showDocumentDetails(doc);
    row.style.cursor = 'pointer';
    
    tbody.appendChild(row);
});
}

// Cambiar tipo de gráfica
function setGraphType(type) {
// Actualizar botones activos
document.querySelectorAll('.chart-control-btn').forEach(btn => {
    btn.classList.remove('active');
});
event.target.classList.add('active');

if (!currentGraphData || !networkChart) return;

let layoutType = type;
if (type === 'graph') {
    // Usar GraphGL para gráficas 3D
    createGraphGL();
    return;
}

const option = networkChart.getOption();
option.series[0].layout = layoutType;

if (layoutType === 'circular') {
    option.series[0].circular = {
        rotateLabel: true
    };
}

networkChart.setOption(option);
}

// Crear gráfica 3D con GraphGL
function createGraphGL() {
const container = document.getElementById('networkChart');
container.innerHTML = '';

if (networkChart) {
    networkChart.dispose();
}

networkChart = echarts.init(container);

const option = {
    title: {
        text: `Red 3D - ${selectedIndex}`,
        subtext: `${currentGraphData.nodes.length} nodos, ${currentGraphData.links.length} conexiones`,
        left: 'center'
    },
    tooltip: {},
    animationDurationUpdate: 1500,
    animationEasingUpdate: 'quinticInOut',
    series: [{
        name: 'Network 3D',
        type: 'graphGL',
        nodes: currentGraphData.nodes.map(node => ({
            ...node,
            x: Math.random() * 1000,
            y: Math.random() * 1000,
            z: Math.random() * 1000
        })),
        edges: currentGraphData.links.map(link => ({
            source: link.source,
            target: link.target,
            value: link.value
        })),
        modularity: {
            resolution: 2,
            sort: true
        },
        lineStyle: {
            color: 'rgba(255, 255, 255, 0.8)',
            width: 1
        },
        itemStyle: {
            opacity: 0.8
        },
        focusNodeAdjacency: true,
        forceAtlas2: {
            GPU: true,
            steps: 5,
            stopThreshold: 1,
            jitterTolerence: 10,
            edgeWeight: [0.2, 1],
            edgeWeightInfluence: 0,
            nodeWeight: [1, 4],
            nodeWeightInfluence: 0,
            preventOverlap: true,
            gravity: 5,
            scaling: 3
        }
    }]
};

networkChart.setOption(option);
}

// Buscar datos
async function searchData() {
const query = document.getElementById('searchInput').value;
if (!selectedIndex || !query.trim()) return;

try {
    const response = await fetch(`${API_BASE_URL}/elasticsearch/index/${selectedIndex}/data?q=${encodeURIComponent(query)}&size=100`);
    const data = await response.json();
    updateDataTable(data);
    showNotification(`🔍 Búsqueda completada: ${data.total_hits} resultados`);
} catch (error) {
    console.error('Error en búsqueda:', error);
    showError('Error en búsqueda: ' + error.message);
}
}

// Refrescar datos
async function refreshData() {
if (selectedIndex) {
    await loadIndexData();
} else {
    await loadIndices();
}
}

// Mostrar detalles de un nodo
function showNodeDetails(nodeData) {
const details = JSON.stringify(nodeData.data, null, 2);
alert(`Detalles del Nodo: ${nodeData.name}\n\n${details}`);
}

// Mostrar detalles de un documento
function showDocumentDetails(doc) {
const details = JSON.stringify(doc.source, null, 2);
alert(`Documento: ${doc.id}\nScore: ${doc.score}\n\n${details}`);
}

// Mostrar notificación
function showNotification(message) {
const notification = document.createElement('div');
notification.className = 'notification';
notification.textContent = message;

document.body.appendChild(notification);

setTimeout(() => {
    notification.style.opacity = '0';
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 300);
}, 3000);
}

// Mostrar error
function showError(message) {
const container = document.getElementById('indicesGrid');
const errorDiv = document.createElement('div');
errorDiv.className = 'error-message';
errorDiv.textContent = message;
container.appendChild(errorDiv);
}

// Event listeners
document.addEventListener('DOMContentLoaded', initApp);

// Redimensionar gráficas cuando cambia el tamaño de la ventana
window.addEventListener('resize', () => {
if (networkChart) networkChart.resize();
if (distributionChart) distributionChart.resize();
if (categoriesChart) categoriesChart.resize();
});

// Enter en búsqueda
document.getElementById('searchInput').addEventListener('keypress', (e) => {
if (e.key === 'Enter') {
    searchData();
}
});

// Cambio en max nodes
document.getElementById('maxNodesSelect').addEventListener('change', () => {
if (selectedIndex) {
    loadIndexData();
}
});

console.log('📊 Elasticsearch Visualizer inicializado');