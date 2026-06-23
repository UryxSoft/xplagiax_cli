// terminal.js - SSH Terminal Manager - Versión Corregida
class SSHTerminalManager {
    constructor() {
        this.socket = null;
        this.terminal = null;
        this.fitAddon = null;
        this.searchAddon = null;
        this.webLinksAddon = null;
        this.unicode11Addon = null;
        this.currentSession = null;
        this.isConnected = false;
        this.isConnecting = false;
        this.sessions = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        
        this.init();
    }
    
    init() {
        this.initializeTerminal();
        this.loadSessions();
        this.setupEventHandlers();
        this.startStatsUpdate();
        
        // Inicializar socket después de que el DOM esté listo
        setTimeout(() => {
            this.initializeSocket();
        }, 100);
        
        // Si hay una sesión en la URL, intentar conectar
        const sessionId = this.getSessionIdFromURL();
        if (sessionId) {
            this.currentSession = { id: parseInt(sessionId) };
            this.loadSessionDetails(sessionId);
        }
    }
    
    getSessionIdFromURL() {
        const path = window.location.pathname;
        const match = path.match(/\/terminal\/(\d+)/);
        return match ? match[1] : null;
    }
    
    initializeSocket() {
        try {
            console.log('Initializing Socket.IO connection...');
            
            // Obtener la URL base correcta
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            const socketURL = `${window.location.protocol}//${host}`;
            
            this.socket = io(socketURL, {
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true,
                timeout: 20000,
                forceNew: true
            });
            
            this.socket.on('connect', () => {
                console.log('✅ Socket connected successfully');
                this.updateConnectionStatus('Conectado al servidor', 'connected');
                this.reconnectAttempts = 0;
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('❌ Socket connection error:', error);
                this.updateConnectionStatus('Error de conexión: ' + error.message, 'error');
                this.handleReconnect();
            });
            
            this.socket.on('disconnect', (reason) => {
                console.log('🔌 Socket disconnected:', reason);
                this.updateConnectionStatus('Desconectado del servidor: ' + reason, 'disconnected');
                this.isConnected = false;
                
                if (reason === 'io server disconnect') {
                    // Reconectar automáticamente si el servidor desconectó
                    this.socket.connect();
                }
            });
            
            this.socket.on('ssh_connected', (data) => {
                console.log('🚀 SSH connected:', data);
                this.isConnected = true;
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('SSH Conectado', 'connected');
                this.updateSessionInfo(data);
                this.showConnectedState();
                this.hideLoading();
                
                // Mostrar mensaje de éxito en terminal
                if (this.terminal) {
                    this.terminal.write('\r\n\x1b[1;32m✅ Conectado exitosamente a ' + data.hostname + '\x1b[0m\r\n');
                }
            });
            
            this.socket.on('ssh_error', (data) => {
                console.error('❌ SSH error:', data);
                this.isConnected = false;
                this.isConnecting = false;
                this.updateConnectionStatus('Error SSH: ' + data.error, 'error');
                this.showDisconnectedState();
                this.hideLoading();
                this.showError(data.error);
            });
            
            this.socket.on('terminal_output', (data) => {
                if (this.terminal && data.session_id == this.currentSession?.id) {
                    this.terminal.write(data.data);
                }
            });
            
            this.socket.on('ssh_disconnected', (data) => {
                console.log('🔌 SSH disconnected:', data);
                this.isConnected = false;
                this.updateConnectionStatus('SSH desconectado', 'disconnected');
                this.showDisconnectedState();
                
                if (this.terminal) {
                    this.terminal.write('\r\n\x1b[1;33m🔌 Sesión SSH desconectada\x1b[0m\r\n');
                }
            });
            
            this.socket.on('terminal_resized', (data) => {
                console.log('📏 Terminal resized:', data);
            });
            
            this.socket.on('terminal_error', (data) => {
                console.error('❌ Terminal error:', data);
                this.showError(data.error);
            });
            
            this.socket.on('connection_status', (data) => {
                console.log('📡 Connection status:', data);
            });
            
            this.socket.on('pong', (data) => {
                console.log('🏓 Pong received:', data);
            });
            
        } catch (error) {
            console.error('❌ Error initializing socket:', error);
            this.showError('Error al inicializar la conexión WebSocket: ' + error.message);
        }
    }
    
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.socket.connect();
            }, 2000 * this.reconnectAttempts);
        } else {
            console.error('❌ Max reconnection attempts reached');
            this.showError('No se pudo establecer conexión con el servidor');
        }
    }
    
    initializeTerminal() {
        try {
            console.log('🖥️ Initializing terminal...');
            
            // Configuración del terminal
            this.terminal = new Terminal({
                cols: 80,
                rows: 24,
                cursorBlink: true,
                cursorStyle: 'block',
                bellStyle: 'none',
                fontSize: 14,
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                theme: {
                    background: '#000000',
                    foreground: '#ffffff',
                    cursor: '#ffffff',
                    selection: '#ffffff40',
                    black: '#000000',
                    red: '#ff0000',
                    green: '#00ff00',
                    yellow: '#ffff00',
                    blue: '#0000ff',
                    magenta: '#ff00ff',
                    cyan: '#00ffff',
                    white: '#ffffff',
                    brightBlack: '#808080',
                    brightRed: '#ff8080',
                    brightGreen: '#80ff80',
                    brightYellow: '#ffff80',
                    brightBlue: '#8080ff',
                    brightMagenta: '#ff80ff',
                    brightCyan: '#80ffff',
                    brightWhite: '#ffffff'
                },
                allowTransparency: false,
                convertEol: true,
                scrollback: 1000,
                tabStopWidth: 4,
                rightClickSelectsWord: true,
                macOptionIsMeta: true
            });
            
            // Cargar addons
            this.fitAddon = new FitAddon.FitAddon();
            this.searchAddon = new SearchAddon.SearchAddon();
            this.webLinksAddon = new WebLinksAddon.WebLinksAddon();
            
            // Aplicar addons
            this.terminal.loadAddon(this.fitAddon);
            this.terminal.loadAddon(this.searchAddon);
            this.terminal.loadAddon(this.webLinksAddon);
            
            // Abrir terminal en el contenedor
            const terminalContainer = document.getElementById('terminalContainer');
            if (terminalContainer) {
                this.terminal.open(terminalContainer);
                
                // Ajustar tamaño
                setTimeout(() => {
                    this.fitAddon.fit();
                }, 100);
                
                // Configurar eventos del terminal
                this.terminal.onData((data) => {
                    console.log('📝 Terminal input:', data.charCodeAt(0), data);
                    if (this.isConnected && this.currentSession && this.socket) {
                        this.socket.emit('terminal_input', {
                            session_id: this.currentSession.id,
                            data: data
                        });
                    } else {
                        console.warn('⚠️ Not connected - input ignored');
                        if (!this.isConnected) {
                            this.terminal.write('\r\n\x1b[1;33m⚠️ No conectado. Haz clic en "Conectar" primero.\x1b[0m\r\n');
                        }
                    }
                });
                
                this.terminal.onResize((size) => {
                    console.log('📏 Terminal resize:', size);
                    if (this.isConnected && this.currentSession && this.socket) {
                        this.socket.emit('terminal_resize', {
                            session_id: this.currentSession.id,
                            cols: size.cols,
                            rows: size.rows
                        });
                    }
                });
                
                // Mensaje de bienvenida
                this.showWelcomeMessage();
                
                console.log('✅ Terminal initialized successfully');
            } else {
                console.error('❌ Terminal container not found');
                this.showError('Contenedor del terminal no encontrado');
            }
            
        } catch (error) {
            console.error('❌ Error initializing terminal:', error);
            this.showError('Error al inicializar el terminal: ' + error.message);
        }
    }
    
    showWelcomeMessage() {
        this.terminal.write('\r\n\x1b[1;36m╔════════════════════════════════════════════════════════════════════════════════════════╗\x1b[0m\r\n');
        this.terminal.write('\x1b[1;36m║\x1b[0m                              \x1b[1;32m🚀 SSH Terminal Manager\x1b[0m                                    \x1b[1;36m║\x1b[0m\r\n');
        this.terminal.write('\x1b[1;36m║\x1b[0m                                                                                          \x1b[1;36m║\x1b[0m\r\n');
        this.terminal.write('\x1b[1;36m║\x1b[0m  \x1b[1;33m1.\x1b[0m Selecciona una sesión SSH de la lista lateral                                     \x1b[1;36m║\x1b[0m\r\n');
        this.terminal.write('\x1b[1;36m║\x1b[0m  \x1b[1;33m2.\x1b[0m Haz clic en "Conectar" para establecer la conexión SSH                          \x1b[1;36m║\x1b[0m\r\n');
        this.terminal.write('\x1b[1;36m║\x1b[0m  \x1b[1;33m3.\x1b[0m Una vez conectado, podrás escribir comandos normalmente                          \x1b[1;36m║\x1b[0m\r\n');
        this.terminal.write('\x1b[1;36m║\x1b[0m                                                                                          \x1b[1;36m║\x1b[0m\r\n');
        this.terminal.write('\x1b[1;36m║\x1b[0m  \x1b[1;31m⚠️  Asegúrate de que la conexión WebSocket esté establecida\x1b[0m                      \x1b[1;36m║\x1b[0m\r\n');
        this.terminal.write('\x1b[1;36m╚════════════════════════════════════════════════════════════════════════════════════════╝\x1b[0m\r\n');
        this.terminal.write('\r\n');
    }
    
    setupEventHandlers() {
        // Redimensionar terminal cuando cambie el tamaño de la ventana
        window.addEventListener('resize', () => {
            if (this.fitAddon) {
                setTimeout(() => {
                    this.fitAddon.fit();
                }, 100);
            }
        });
        
        // Atajos de teclado
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey) {
                switch (e.key) {
                    case 'f':
                        e.preventDefault();
                        this.toggleSearch();
                        break;
                    case 'c':
                        if (this.isConnected) {
                            e.preventDefault();
                            this.sendCtrlC();
                        }
                        break;
                    case 'l':
                        if (this.isConnected) {
                            e.preventDefault();
                            this.clearTerminal();
                        }
                        break;
                }
            }
        });
        
        // Ping periódico para mantener conexión
        setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.socket.emit('ping', { timestamp: Date.now() });
            }
        }, 30000);
    }
    
    async loadSessions() {
        try {
            console.log('📋 Loading sessions...');
            const response = await fetch('/sessionsssh_bp/api/sessions');
            if (response.ok) {
                this.sessions = await response.json();
                console.log('✅ Sessions loaded:', this.sessions.length);
                this.renderSessionsList();
            } else {
                console.error('❌ Error loading sessions:', response.statusText);
                this.showError('Error al cargar las sesiones: ' + response.statusText);
            }
        } catch (error) {
            console.error('❌ Error loading sessions:', error);
            this.showError('Error al cargar las sesiones: ' + error.message);
        }
    }
    
    renderSessionsList() {
        const sessionsList = document.getElementById('sessionsList');
        if (!sessionsList) return;
        
        if (this.sessions.length === 0) {
            sessionsList.innerHTML = `
                <div class="no-sessions">
                    <i class="fas fa-server"></i>
                    <p>No hay sesiones SSH configuradas</p>
                    <button class="btn btn-primary" onclick="openSessionManager()">
                        Crear Nueva Sesión
                    </button>
                </div>
            `;
            return;
        }
        
        sessionsList.innerHTML = this.sessions.map(session => `
            <div class="session-item ${session.id == this.currentSession?.id ? 'active' : ''}" 
                 onclick="terminalManager.selectSession(${session.id})">
                <div class="session-header">
                    <h4>${session.name}</h4>
                    <span class="session-status ${session.is_active ? 'active' : 'inactive'}">
                        ${session.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                </div>
                <div class="session-details">
                    <div><i class="fas fa-server"></i> ${session.hostname}:${session.port}</div>
                    <div><i class="fas fa-user"></i> ${session.username}</div>
                    <div><i class="fas fa-key"></i> ${session.auth_type}</div>
                </div>
            </div>
        `).join('');
    }
    
    selectSession(sessionId) {
        console.log('🎯 Selecting session:', sessionId);
        const session = this.sessions.find(s => s.id === sessionId);
        if (session) {
            this.currentSession = session;
            this.updateSessionInfo(session);
            this.renderSessionsList();
            
            // Actualizar URL
            const newUrl = `/sessionsssh_bp/terminal/${sessionId}`;
            window.history.pushState({}, '', newUrl);
            
            // Mostrar información en el terminal
            if (this.terminal) {
                this.terminal.write(`\r\n\x1b[1;34m📋 Sesión seleccionada: ${session.name}\x1b[0m\r\n`);
                this.terminal.write(`\x1b[1;34m🖥️  Servidor: ${session.hostname}:${session.port}\x1b[0m\r\n`);
                this.terminal.write(`\x1b[1;34m👤 Usuario: ${session.username}\x1b[0m\r\n`);
                this.terminal.write(`\x1b[1;33m💡 Haz clic en "Conectar" para establecer la conexión SSH\x1b[0m\r\n\r\n`);
            }
        }
    }
    
    async loadSessionDetails(sessionId) {
        try {
            console.log('📋 Loading session details for:', sessionId);
            const response = await fetch('/sessionsssh_bp/api/sessions');
            if (response.ok) {
                const sessions = await response.json();
                const session = sessions.find(s => s.id == sessionId);
                if (session) {
                    this.currentSession = session;
                    this.sessions = sessions;
                    this.updateSessionInfo(session);
                    this.renderSessionsList();
                    console.log('✅ Session details loaded:', session.name);
                }
            }
        } catch (error) {
            console.error('❌ Error loading session details:', error);
            this.showError('Error al cargar detalles de la sesión: ' + error.message);
        }
    }
    
    updateSessionInfo(session) {
        const elements = {
            sessionName: session.name,
            sessionServer: `${session.hostname}:${session.port}`,
            sessionUser: session.username
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }
    
    updateConnectionStatus(message, status) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `connection-status ${status}`;
        }
        
        console.log(`📡 Connection status: ${message} (${status})`);
    }
    
    showConnectedState() {
        const connectBtn = document.getElementById('connectBtn');
        const disconnectBtn = document.getElementById('disconnectBtn');
        
        if (connectBtn) {
            connectBtn.style.display = 'none';
        }
        if (disconnectBtn) {
            disconnectBtn.style.display = 'inline-block';
        }
    }
    
    showDisconnectedState() {
        const connectBtn = document.getElementById('connectBtn');
        const disconnectBtn = document.getElementById('disconnectBtn');
        
        if (connectBtn) {
            connectBtn.style.display = 'inline-block';
        }
        if (disconnectBtn) {
            disconnectBtn.style.display = 'none';
        }
    }
    
    showLoading(message = 'Conectando...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingMessage = document.getElementById('loadingMessage');
        
        if (overlay) {
            overlay.style.display = 'flex';
        }
        if (loadingMessage) {
            loadingMessage.textContent = message;
        }
        
        console.log('⏳ Loading:', message);
    }
    
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
        
        console.log('✅ Loading hidden');
    }
    
    showError(message) {
        console.error('❌ SSH Error:', message);
        
        // Mostrar en el terminal
        if (this.terminal) {
            this.terminal.write(`\r\n\x1b[1;31m❌ Error: ${message}\x1b[0m\r\n`);
        }
        
        // Mostrar notificación (si existe un sistema de notificaciones)
        if (typeof showNotification === 'function') {
            showNotification(message, 'error');
        } else {
            // Mostrar alerta solo para errores críticos
            if (message.includes('WebSocket') || message.includes('conexión')) {
                alert('Error crítico: ' + message);
            }
        }
    }
    
    connectToSession() {
        if (!this.currentSession) {
            this.showError('No hay sesión seleccionada');
            return;
        }
        
        if (!this.socket || !this.socket.connected) {
            this.showError('No hay conexión WebSocket. Recarga la página.');
            return;
        }
        
        if (this.isConnecting) {
            console.log('⚠️ Already connecting...');
            return;
        }
        
        this.isConnecting = true;
        this.showLoading('Conectando al servidor SSH...');
        
        console.log('🚀 Connecting to session:', this.currentSession.id);
        
        // Limpiar terminal antes de conectar
        this.terminal.clear();
        this.terminal.write(`\x1b[1;33m🔄 Conectando a ${this.currentSession.name}...\x1b[0m\r\n`);
        
        this.socket.emit('ssh_connect', {
            session_id: this.currentSession.id,
            cols: this.terminal.cols,
            rows: this.terminal.rows
        });
        
        // Timeout para la conexión
        setTimeout(() => {
            if (this.isConnecting) {
                this.isConnecting = false;
                this.hideLoading();
                this.showError('Timeout de conexión SSH (30 segundos)');
            }
        }, 30000);
    }
    
    disconnectSession() {
        if (!this.currentSession || !this.isConnected) {
            return;
        }
        
        if (!this.socket || !this.socket.connected) {
            this.showError('No hay conexión WebSocket');
            return;
        }
        
        console.log('🔌 Disconnecting session:', this.currentSession.id);
        
        this.socket.emit('ssh_disconnect', {
            session_id: this.currentSession.id
        });
        
        this.isConnected = false;
        this.updateConnectionStatus('Desconectando...', 'disconnecting');
        this.showDisconnectedState();
        
        if (this.terminal) {
            this.terminal.write('\r\n\x1b[1;33m🔌 Desconectando sesión SSH...\x1b[0m\r\n');
        }
    }
    
    clearTerminal() {
        if (this.terminal) {
            this.terminal.clear();
            if (!this.isConnected) {
                this.showWelcomeMessage();
            }
        }
    }
    
    sendCtrlC() {
        if (this.isConnected && this.currentSession && this.socket) {
            console.log('📨 Sending Ctrl+C');
            this.socket.emit('terminal_input', {
                session_id: this.currentSession.id,
                data: '\x03'
            });
        }
    }
    
    toggleFullscreen() {
        const terminalLayout = document.getElementById('terminalLayout');
        if (terminalLayout) {
            terminalLayout.classList.toggle('fullscreen');
            
            // Ajustar terminal después del cambio
            setTimeout(() => {
                if (this.fitAddon) {
                    this.fitAddon.fit();
                }
            }, 100);
        }
    }
    
    toggleSearch() {
        const searchBox = document.getElementById('terminalSearch');
        if (searchBox) {
            const isVisible = searchBox.style.display === 'block';
            searchBox.style.display = isVisible ? 'none' : 'block';
            
            if (!isVisible) {
                const searchInput = document.getElementById('searchInput');
                if (searchInput) {
                    searchInput.focus();
                }
            }
        }
    }
    
    searchNext() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput && this.searchAddon) {
            this.searchAddon.findNext(searchInput.value);
        }
    }
    
    searchPrevious() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput && this.searchAddon) {
            this.searchAddon.findPrevious(searchInput.value);
        }
    }
    
    startStatsUpdate() {
        // Actualizar estadísticas cada 5 segundos
        setInterval(() => {
            this.updateStats();
        }, 5000);
    }
    
    async updateStats() {
        try {
            // Estadísticas básicas
            const stats = {
                cpu: Math.floor(Math.random() * 100),
                memory: Math.floor(Math.random() * 8192),
                activeSessions: this.sessions.filter(s => s.is_active).length
            };
            
            this.updateStatsDisplay(stats);
        } catch (error) {
            console.error('❌ Error updating stats:', error);
        }
    }
    
    updateStatsDisplay(stats) {
        const cpuElement = document.getElementById('cpuUsage');
        const memoryElement = document.getElementById('memoryUsage');
        const sessionsElement = document.getElementById('activeSessionsCount');
        
        if (cpuElement) {
            cpuElement.textContent = stats.cpu + '%';
        }
        if (memoryElement) {
            memoryElement.textContent = stats.memory + ' MB';
        }
        if (sessionsElement) {
            sessionsElement.textContent = stats.activeSessions;
        }
    }
    
    // Método para depuración
    getDebugInfo() {
        return {
            socketConnected: this.socket?.connected || false,
            isConnected: this.isConnected,
            isConnecting: this.isConnecting,
            currentSession: this.currentSession,
            sessionsCount: this.sessions.length,
            terminalReady: !!this.terminal
        };
    }
}

// Inicializar el manager cuando se cargue la página
let terminalManager;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM Content Loaded - Initializing Terminal Manager');
    terminalManager = new SSHTerminalManager();
    
    // Agregar información de depuración a la consola
    window.getTerminalDebugInfo = () => {
        if (terminalManager) {
            console.log('🔍 Terminal Debug Info:', terminalManager.getDebugInfo());
        }
    };
    
    // Comando para probar conexión desde consola
    window.testConnection = () => {
        if (terminalManager && terminalManager.socket) {
            console.log('🧪 Testing connection...');
            terminalManager.socket.emit('ping', { test: true });
        }
    };
});

// Funciones globales para compatibilidad con onclick en HTML
function connectToSession() {
    if (terminalManager) {
        terminalManager.connectToSession();
    }
}

function disconnectSession() {
    if (terminalManager) {
        terminalManager.disconnectSession();
    }
}

function clearTerminal() {
    if (terminalManager) {
        terminalManager.clearTerminal();
    }
}

function toggleFullscreen() {
    if (terminalManager) {
        terminalManager.toggleFullscreen();
    }
}

function toggleSearch() {
    if (terminalManager) {
        terminalManager.toggleSearch();
    }
}

function searchNext() {
    if (terminalManager) {
        terminalManager.searchNext();
    }
}

function searchPrevious() {
    if (terminalManager) {
        terminalManager.searchPrevious();
    }
}

function openSessionManager() {
    window.open('/sessionsssh_bp/new', '_blank');
}

// Estilos adicionales para el CSS
const additionalStyles = `
.session-item {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 10px;
    cursor: pointer;
    transition: all 0.2s;
}

.session-item:hover {
    background: #e9ecef;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.session-item.active {
    background: #e3f2fd;
    border-color: #2196f3;
}

.session-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.session-header h4 {
    margin: 0;
    font-size: 16px;
    color: #212529;
}
.session-status {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
}

.session-status.active {
    background: #d4edda;
    color: #155724;
}

.session-status.inactive {
    background: #f8d7da;
    color: #721c24;
}

.session-details {
    font-size: 14px;
    color: #6c757d;
}

.session-details div {
    margin-bottom: 4px;
}

.session-details i {
    width: 16px;
    margin-right: 8px;
}

.no-sessions {
    text-align: center;
    padding: 40px 20px;
    color: #6c757d;
}

.no-sessions i {
    font-size: 48px;
    margin-bottom: 16px;
    color: #dee2e6;
}

.connection-status.connected {
    color: #28a745;
    font-weight: 600;
}

.connection-status.disconnected {
    color: #dc3545;
    font-weight: 600;
}

.connection-status.error {
    color: #dc3545;
    font-weight: 600;
}

.connection-status.connecting {
    color: #ffc107;
    font-weight: 600;
}

.fullscreen {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 9999 !important;
    background: #000 !important;
}
`;

// Agregar estilos al documento
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);