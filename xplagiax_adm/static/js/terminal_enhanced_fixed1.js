// terminal_enhanced.js - SSH Terminal Manager Enhanced (Fixed)
class EnhancedSSHTerminalManager {
    constructor() {
        this.socket = null;
        this.terminal = null;
        this.fitAddon = null;
        this.searchAddon = null;
        this.webLinksAddon = null;
        this.clipboardAddon = null;
        this.serializeAddon = null;
        this.unicode11Addon = null;
        this.imageAddon = null;
        
        this.currentSession = null;
        this.isConnected = false;
        this.isConnecting = false;
        this.sessions = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.heartbeatInterval = null;
        this.connectionStartTime = null;
        
        // Nuevas funcionalidades
        this.commandHistory = [];
        this.historyIndex = -1;
        this.currentCommand = '';
        this.settings = {
            theme: 'dark',
            fontSize: 14,
            opacity: 100,
            cursorBlink: true,
            sound: false
        };
        
        this.init();
    }
    
    init() {
        this.loadSettings();
        this.initializeTerminal();
        this.loadSessions();
        this.setupEventHandlers();
        this.setupFileUpload();
        this.startStatsUpdate();
        
        setTimeout(() => {
            this.initializeSocket();
        }, 100);
        
        const sessionId = this.getSessionIdFromURL();
        if (sessionId) {
            this.currentSession = { id: parseInt(sessionId) };
            this.loadSessionDetails(sessionId);
        }
    }
    
    // === FUNCIÓN DE ERROR FALTANTE ===
    showError(message) {
        console.error('Terminal Error:', message);
        this.showNotification(message, 'error');
        
        // También mostrar en el terminal si está disponible
        if (this.terminal) {
            this.terminal.writeln(`\r\n\x1b[31m[ERROR] ${message}\x1b[0m\r\n`);
        }
    }
    
    // === CONFIGURACIÓN Y TEMAS ===
    loadSettings() {
        const saved = localStorage.getItem('terminalSettings');
        if (saved) {
            this.settings = { ...this.settings, ...JSON.parse(saved) };
        }
        this.applySettings();
    }
    
    saveSettings() {
        localStorage.setItem('terminalSettings', JSON.stringify(this.settings));
        this.applySettings();
    }
    
    applySettings() {
        if (this.terminal) {
            this.terminal.options.fontSize = this.settings.fontSize;
            this.terminal.options.cursorBlink = this.settings.cursorBlink;
            
            // Aplicar tema
            const themes = {
                dark: {
                    background: '#000000',
                    foreground: '#ffffff',
                    cursor: '#ffffff'
                },
                light: {
                    background: '#ffffff',
                    foreground: '#000000',
                    cursor: '#000000'
                },
                matrix: {
                    background: '#000000',
                    foreground: '#00ff00',
                    cursor: '#00ff00'
                },
                cyberpunk: {
                    background: '#0d1117',
                    foreground: '#ff79c6',
                    cursor: '#ff79c6'
                }
            };
            
            const theme = themes[this.settings.theme];
            if (theme) {
                this.terminal.options.theme = theme;
            }
            
            // Aplicar transparencia
            const container = document.getElementById('terminalContainer');
            if (container) {
                container.style.opacity = this.settings.opacity / 100;
            }
        }
        
        // Actualizar controles de configuración
        this.updateSettingsUI();
    }
    
    updateSettingsUI() {
        const elements = {
            themeSelect: this.settings.theme,
            fontSizeRange: this.settings.fontSize,
            opacityRange: this.settings.opacity,
            cursorBlinkCheck: this.settings.cursorBlink,
            soundCheck: this.settings.sound
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = value;
                } else {
                    element.value = value;
                }
            }
        });
        
        // Actualizar valores mostrados
        const fontSizeValue = document.getElementById('fontSizeValue');
        const opacityValue = document.getElementById('opacityValue');
        if (fontSizeValue) fontSizeValue.textContent = this.settings.fontSize + 'px';
        if (opacityValue) opacityValue.textContent = this.settings.opacity + '%';
    }
    
    // === TERMINAL MEJORADO CON VERIFICACIÓN DE ADDONS ===
    initializeTerminal() {
        try {
            console.log('🖥️ Initializing enhanced terminal...');
            
            // Verificar que XTerm esté disponible
            if (typeof Terminal === 'undefined') {
                throw new Error('XTerm library not loaded');
            }
            
            this.terminal = new Terminal({
                cols: 80,
                rows: 24,
                cursorBlink: this.settings.cursorBlink,
                cursorStyle: 'block',
                bellStyle: 'none',
                fontSize: this.settings.fontSize,
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                allowTransparency: true,
                convertEol: true,
                scrollback: 5000,
                tabStopWidth: 4,
                rightClickSelectsWord: true,
                macOptionIsMeta: true,
                minimumContrastRatio: 4.5
            });
            
            // Cargar addons con verificación
            this.loadAddons();
            
            const terminalContainer = document.getElementById('terminalContainer');
            if (terminalContainer) {
                this.terminal.open(terminalContainer);
                
                setTimeout(() => {
                    if (this.fitAddon) {
                        this.fitAddon.fit();
                    }
                }, 100);
                
                // Eventos del terminal mejorados
                this.terminal.onData((data) => {
                    this.handleTerminalInput(data);
                });
                
                this.terminal.onResize((size) => {
                    if (this.isConnected && this.currentSession && this.socket?.connected) {
                        this.socket.emit('terminal_resize', {
                            session_id: this.currentSession.id,
                            cols: size.cols,
                            rows: size.rows
                        });
                    }
                });
                
                // Eventos de selección para clipboard
                this.terminal.onSelectionChange(() => {
                    const selection = this.terminal.getSelection();
                    if (selection) {
                        this.lastSelection = selection;
                    }
                });
                
                this.applySettings();
                this.showWelcomeMessage();
                
                console.log('✅ Enhanced terminal initialized successfully');
            }
            
        } catch (error) {
            console.error('❌ Error initializing terminal:', error);
            this.showError('Error al inicializar el terminal: ' + error.message);
        }
    }
    
    // === CARGA SEGURA DE ADDONS ===
    loadAddons() {
        try {
            // FitAddon - Sintaxis para CDN
            if (typeof FitAddon !== 'undefined') {
                this.fitAddon = new FitAddon.FitAddon();
                this.terminal.loadAddon(this.fitAddon);
                console.log('✅ FitAddon loaded');
            } else {
                console.warn('⚠️ FitAddon not available');
            }
            
            // SearchAddon - Sintaxis para CDN
            if (typeof SearchAddon !== 'undefined') {
                this.searchAddon = new SearchAddon.SearchAddon();
                this.terminal.loadAddon(this.searchAddon);
                console.log('✅ SearchAddon loaded');
            } else {
                console.warn('⚠️ SearchAddon not available');
            }
            
            // WebLinksAddon - Sintaxis para CDN
            if (typeof WebLinksAddon !== 'undefined') {
                this.webLinksAddon = new WebLinksAddon.WebLinksAddon();
                this.terminal.loadAddon(this.webLinksAddon);
                console.log('✅ WebLinksAddon loaded');
            } else {
                console.warn('⚠️ WebLinksAddon not available');
            }
            
            // SerializeAddon - Sintaxis para CDN
            if (typeof SerializeAddon !== 'undefined') {
                this.serializeAddon = new SerializeAddon.SerializeAddon();
                this.terminal.loadAddon(this.serializeAddon);
                console.log('✅ SerializeAddon loaded');
            } else {
                console.warn('⚠️ SerializeAddon not available');
            }
            
            // Addons adicionales solo si están disponibles
            if (typeof ClipboardAddon !== 'undefined') {
                this.clipboardAddon = new ClipboardAddon.ClipboardAddon();
                this.terminal.loadAddon(this.clipboardAddon);
                console.log('✅ ClipboardAddon loaded');
            }
            
            if (typeof Unicode11Addon !== 'undefined') {
                this.unicode11Addon = new Unicode11Addon.Unicode11Addon();
                this.terminal.loadAddon(this.unicode11Addon);
                this.terminal.unicode.activeVersion = '11';
                console.log('✅ Unicode11Addon loaded');
            }
            
            if (typeof ImageAddon !== 'undefined') {
                this.imageAddon = new ImageAddon.ImageAddon();
                this.terminal.loadAddon(this.imageAddon);
                console.log('✅ ImageAddon loaded');
            }
            
        } catch (error) {
            console.error('Error loading addons:', error);
            this.showNotification('Algunos addons no se cargaron correctamente', 'warning');
        }
    }
    
    // === MENSAJE DE BIENVENIDA ===
    showWelcomeMessage() {
        if (this.terminal) {
            this.terminal.writeln('\x1b[36m╔══════════════════════════════════════════════════════════════╗\x1b[0m');
            this.terminal.writeln('\x1b[36m║\x1b[0m \x1b[1m\x1b[32mSSH Terminal Enhanced v2.0\x1b[0m                               \x1b[36m║\x1b[0m');
            this.terminal.writeln('\x1b[36m║\x1b[0m                                                            \x1b[36m║\x1b[0m');
            this.terminal.writeln('\x1b[36m║\x1b[0m \x1b[33mCaracterísticas:\x1b[0m                                         \x1b[36m║\x1b[0m');
            this.terminal.writeln('\x1b[36m║\x1b[0m • Historial de comandos (↑/↓)                             \x1b[36m║\x1b[0m');
            this.terminal.writeln('\x1b[36m║\x1b[0m • Transferencia de archivos                               \x1b[36m║\x1b[0m');
            this.terminal.writeln('\x1b[36m║\x1b[0m • Búsqueda avanzada (Ctrl+F)                             \x1b[36m║\x1b[0m');
            this.terminal.writeln('\x1b[36m║\x1b[0m • Temas personalizables                                   \x1b[36m║\x1b[0m');
            this.terminal.writeln('\x1b[36m║\x1b[0m • Capturas de pantalla (Ctrl+S)                          \x1b[36m║\x1b[0m');
            this.terminal.writeln('\x1b[36m║\x1b[0m                                                            \x1b[36m║\x1b[0m');
            this.terminal.writeln('\x1b[36m║\x1b[0m \x1b[31m⚠ Conecta a una sesión SSH para comenzar\x1b[0m                \x1b[36m║\x1b[0m');
            this.terminal.writeln('\x1b[36m╚══════════════════════════════════════════════════════════════╝\x1b[0m');
            this.terminal.writeln('');
        }
    }
    
    // === HISTORIAL DE COMANDOS ===
    handleTerminalInput(data) {
        try {
            const charCode = data.charCodeAt(0);
            
            // Detectar comandos especiales
            if (charCode === 13) { // Enter
                this.handleCommandSubmit();
            } else if (charCode === 38) { // Flecha arriba
                this.navigateHistory(-1);
                return; // No enviar al servidor
            } else if (charCode === 40) { // Flecha abajo
                this.navigateHistory(1);
                return; // No enviar al servidor
            } else if (charCode === 9) { // Tab - autocompletado
                this.handleTabCompletion();
            } else if (charCode >= 32 && charCode <= 126) { // Caracteres imprimibles
                this.currentCommand += data;
            } else if (charCode === 8 || charCode === 127) { // Backspace/Delete
                this.currentCommand = this.currentCommand.slice(0, -1);
            }
            
            // Validaciones antes de enviar
            if (!this.socket || !this.socket.connected) {
                this.showNotification('Sin conexión WebSocket', 'warning');
                return;
            }
            
            if (!this.isConnected) {
                this.showNotification('SSH no conectado', 'warning');
                return;
            }
            
            if (!this.currentSession) {
                this.showNotification('No hay sesión seleccionada', 'warning');
                return;
            }
            
            // Enviar al servidor
            this.socket.emit('terminal_input', {
                session_id: this.currentSession.id,
                data: data
            });
            
            // Reproducir sonido si está habilitado
            if (this.settings.sound) {
                this.playKeySound();
            }
            
        } catch (error) {
            console.error('❌ Error handling terminal input:', error);
        }
    }
    
    handleCommandSubmit() {
        if (this.currentCommand.trim()) {
            // Guardar en historial
            this.addToHistory(this.currentCommand.trim());
            this.currentCommand = '';
            this.historyIndex = -1;
        }
    }
    
    addToHistory(command) {
        // Evitar duplicados consecutivos
        if (this.commandHistory[this.commandHistory.length - 1] !== command) {
            this.commandHistory.push(command);
            
            // Limitar historial a 100 comandos
            if (this.commandHistory.length > 100) {
                this.commandHistory.shift();
            }
            
            // Guardar en localStorage
            localStorage.setItem('commandHistory', JSON.stringify(this.commandHistory));
            this.updateHistoryDisplay();
        }
    }
    
    navigateHistory(direction) {
        if (this.commandHistory.length === 0) return;
        
        if (direction === -1) { // Arriba
            if (this.historyIndex === -1) {
                this.historyIndex = this.commandHistory.length - 1;
            } else if (this.historyIndex > 0) {
                this.historyIndex--;
            }
        } else { // Abajo
            if (this.historyIndex !== -1) {
                this.historyIndex++;
                if (this.historyIndex >= this.commandHistory.length) {
                    this.historyIndex = -1;
                }
            }
        }
        
        // Mostrar comando del historial
        const command = this.historyIndex === -1 ? '' : this.commandHistory[this.historyIndex];
        this.replaceCurrentLine(command);
        this.currentCommand = command;
    }
    
    replaceCurrentLine(text) {
        // Limpiar línea actual y escribir nuevo texto
        this.terminal.write('\r\x1b[K' + text);
    }
    
    updateHistoryDisplay() {
        const historyList = document.getElementById('historyList');
        if (!historyList) return;
        
        const recentHistory = this.commandHistory.slice(-20).reverse();
        historyList.innerHTML = recentHistory.map((cmd, index) => `
            <div class="history-item" onclick="terminalManager.executeFromHistory('${cmd.replace(/'/g, "\\'")}')">
                <span>${cmd}</span>
                <span class="history-time">${new Date().toLocaleTimeString()}</span>
            </div>
        `).join('');
    }
    
    executeFromHistory(command) {
        if (this.isConnected && this.currentSession && this.socket?.connected) {
            this.socket.emit('terminal_input', {
                session_id: this.currentSession.id,
                data: command + '\r'
            });
            this.addToHistory(command);
        }
    }
    
    // === FUNCIONES BÁSICAS NECESARIAS ===
    initializeSocket() {
        try {
            if (typeof io === 'undefined') {
                throw new Error('Socket.IO no está disponible');
            }
            
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('✅ Socket conectado');
                this.showNotification('Conexión WebSocket establecida', 'success');
            });
            
            this.socket.on('disconnect', () => {
                console.log('❌ Socket desconectado');
                this.showNotification('Conexión WebSocket perdida', 'error');
            });
            
            this.socket.on('ssh_connected', (data) => {
                this.isConnected = true;
                this.isConnecting = false;
                this.updateConnectionStatus('Conectado', 'connected');
                this.showNotification('SSH conectado exitosamente', 'success');
                
                // Actualizar botones
                const connectBtn = document.getElementById('connectBtn');
                const disconnectBtn = document.getElementById('disconnectBtn');
                if (connectBtn) connectBtn.style.display = 'none';
                if (disconnectBtn) disconnectBtn.style.display = 'inline-flex';
            });
            
            this.socket.on('ssh_error', (data) => {
                this.isConnecting = false;
                this.showError('Error SSH: ' + data.error);
            });
            
            this.socket.on('ssh_status', (data) => {
                console.log('SSH Status:', data.message);
                this.showNotification(data.message, 'info', 2000);
            });
            
            this.socket.on('terminal_output', (data) => {
                if (this.terminal && data.data) {
                    this.terminal.write(data.data);
                }
            });
            
            this.socket.on('ssh_disconnected', (data) => {
                this.isConnected = false;
                this.updateConnectionStatus('Desconectado', 'disconnected');
                this.showNotification('SSH desconectado', 'info');
                
                // Actualizar botones
                const connectBtn = document.getElementById('connectBtn');
                const disconnectBtn = document.getElementById('disconnectBtn');
                if (connectBtn) connectBtn.style.display = 'inline-flex';
                if (disconnectBtn) disconnectBtn.style.display = 'none';
            });
            
        } catch (error) {
            console.error('Error inicializando socket:', error);
            this.showError('Error de conexión: ' + error.message);
        }
    }
    
    loadSessions() {
        // Simular carga de sesiones o cargar desde la API
        if (this.currentSession) {
            this.sessions = [this.currentSession];
            this.updateSessionsList();
        } else {
            // Intentar cargar desde la API
            fetch('/sessionsssh_bp/api/sessions')
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        throw new Error('Error al cargar sesiones');
                    }
                })
                .then(sessions => {
                    this.sessions = sessions;
                    this.updateSessionsList();
                })
                .catch(error => {
                    console.error('Error cargando sesiones:', error);
                    // No mostrar error si no hay endpoint de API disponible
                });
        }
    }
    
    updateSessionsList() {
        const sessionsList = document.getElementById('sessionsList');
        if (sessionsList && this.sessions.length > 0) {
            sessionsList.innerHTML = this.sessions.map(session => `
                <div class="session-item ${this.currentSession?.id === session.id ? 'active' : ''}" 
                     onclick="terminalManager.selectSession(${session.id})">
                    <div class="session-name">${session.name || 'Sesión SSH'}</div>
                    <div class="session-info">${session.hostname || 'localhost'}:${session.port || 22}</div>
                </div>
            `).join('');
        } else if (sessionsList) {
            sessionsList.innerHTML = `
                <div style="text-align: center; color: #6b7280; padding: 20px;">
                    <i class="fas fa-server fa-2x"></i>
                    <p>No hay sesiones disponibles</p>
                    <button class="btn btn-primary btn-sm" onclick="openSessionManager()">
                        Crear Sesión
                    </button>
                </div>
            `;
        }
    }
    
    selectSession(sessionId) {
        this.currentSession = this.sessions.find(s => s.id === sessionId);
        if (this.currentSession) {
            this.updateSessionInfo();
            this.updateSessionsList(); // Para actualizar la clase 'active'
        }
    }
    
    updateSessionInfo() {
        if (!this.currentSession) return;
        
        const elements = {
            sessionName: this.currentSession.name || 'Sesión SSH',
            sessionServer: `${this.currentSession.hostname || 'localhost'}:${this.currentSession.port || 22}`,
            sessionUser: this.currentSession.username || 'usuario'
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }
    
    loadSessionDetails(sessionId) {
        fetch(`/sessionsssh_bp/sessions/${sessionId}`)
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Sesión no encontrada');
                }
            })
            .then(session => {
                this.currentSession = session;
                this.updateSessionInfo();
            })
            .catch(error => {
                console.error('Error cargando detalles de sesión:', error);
                // Crear sesión mock si no se puede cargar
                this.currentSession = {
                    id: sessionId,
                    name: `Sesión ${sessionId}`,
                    hostname: 'localhost',
                    port: 22,
                    username: 'usuario'
                };
                this.updateSessionInfo();
            });
    }
    
    getSessionIdFromURL() {
        const path = window.location.pathname;
        const match = path.match(/\/terminal\/(\d+)/);
        return match ? match[1] : null;
    }
    
    // === CONEXIÓN SSH ===
    connectToSession() {
        if (!this.currentSession) {
            this.showError('No hay sesión seleccionada');
            return;
        }
        
        if (this.isConnecting) {
            this.showNotification('Ya hay una conexión en proceso', 'warning');
            return;
        }
        
        this.isConnecting = true;
        this.showNotification('Conectando...', 'info');
        
        this.socket.emit('ssh_connect', {
            session_id: this.currentSession.id,
            cols: this.terminal?.cols || 80,
            rows: this.terminal?.rows || 24
        });
        
        // Timeout de conexión
        setTimeout(() => {
            if (this.isConnecting && !this.isConnected) {
                this.isConnecting = false;
                this.showError('Timeout de conexión SSH');
            }
        }, 30000);
    }
    
    disconnectSession() {
        if (this.socket && this.currentSession) {
            this.socket.emit('ssh_disconnect', {
                session_id: this.currentSession.id
            });
        }
        
        this.isConnected = false;
        this.isConnecting = false;
        this.updateConnectionStatus('Desconectado', 'disconnected');
    }
    
    clearTerminal() {
        if (this.terminal) {
            this.terminal.clear();
        }
    }
    
    // === NOTIFICACIONES ===
    showNotification(message, type = 'info', duration = 4000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        notification.innerHTML = `${icons[type] || ''} ${message}`;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.classList.add('show'), 100);
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, duration);
    }
    
    updateConnectionStatus(message, status) {
        const statusElement = document.getElementById('connectionStatus');
        const statusIndicator = document.getElementById('statusIndicator');
        const headerSessionName = document.getElementById('headerSessionName');
        
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `connection-status ${status}`;
        }
        
        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${status === 'connected' ? 'connected' : ''}`;
        }
        
        if (headerSessionName && this.currentSession) {
            headerSessionName.textContent = status === 'connected' 
                ? this.currentSession.name 
                : 'No conectado';
        }
    }
    
    // === FUNCIONES DE CONFIGURACIÓN ===
    setupEventHandlers() {
        // Configuración de ajustes
        const themeSelect = document.getElementById('themeSelect');
        if (themeSelect) {
            themeSelect.addEventListener('change', (e) => {
                this.settings.theme = e.target.value;
                this.saveSettings();
            });
        }
        
        const fontSizeRange = document.getElementById('fontSizeRange');
        if (fontSizeRange) {
            fontSizeRange.addEventListener('input', (e) => {
                this.settings.fontSize = parseInt(e.target.value);
                this.saveSettings();
            });
        }
        
        const opacityRange = document.getElementById('opacityRange');
        if (opacityRange) {
            opacityRange.addEventListener('input', (e) => {
                this.settings.opacity = parseInt(e.target.value);
                this.saveSettings();
            });
        }
        
        const cursorBlinkCheck = document.getElementById('cursorBlinkCheck');
        if (cursorBlinkCheck) {
            cursorBlinkCheck.addEventListener('change', (e) => {
                this.settings.cursorBlink = e.target.checked;
                this.saveSettings();
            });
        }
        
        const soundCheck = document.getElementById('soundCheck');
        if (soundCheck) {
            soundCheck.addEventListener('change', (e) => {
                this.settings.sound = e.target.checked;
                this.saveSettings();
            });
        }
        
        // Redimensionar terminal
        window.addEventListener('resize', () => {
            if (this.fitAddon) {
                setTimeout(() => this.fitAddon.fit(), 100);
            }
        });
        
        this.loadCommandHistory();
    }
    
    loadCommandHistory() {
        const saved = localStorage.getItem('commandHistory');
        if (saved) {
            try {
                this.commandHistory = JSON.parse(saved);
            } catch (error) {
                console.error('Error cargando historial:', error);
                this.commandHistory = [];
            }
        }
    }
    
    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        if (uploadArea && fileInput) {
            uploadArea.addEventListener('click', () => fileInput.click());
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                this.handleFileUpload(e.dataTransfer.files);
            });
            
            fileInput.addEventListener('change', (e) => {
                this.handleFileUpload(e.target.files);
            });
        } else {
            console.log('File upload elements not found, skipping setup');
        }
    }
    
    async handleFileUpload(files) {
        if (!this.isConnected) {
            this.showNotification('Conecta SSH primero', 'warning');
            return;
        }
        
        for (const file of files) {
            await this.uploadFile(file);
        }
    }
    
    async uploadFile(file) {
        try {
            if (!this.currentSession) {
                throw new Error('No hay sesión activa');
            }
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('session_id', this.currentSession.id);
            
            this.showUploadProgress(0);
            
            const response = await fetch('/sessionsssh_bp/api/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                this.showNotification(`Archivo ${file.name} subido exitosamente`, 'success');
                this.hideUploadProgress();
            } else {
                throw new Error('Error al subir archivo');
            }
            
        } catch (error) {
            this.showNotification(`Error subiendo ${file.name}: ${error.message}`, 'error');
            this.hideUploadProgress();
        }
    }
    
    showUploadProgress(percent) {
        const progress = document.getElementById('fileProgress');
        const fill = document.getElementById('progressFill');
        const text = document.getElementById('progressText');
        
        if (progress) progress.style.display = 'block';
        if (fill) fill.style.width = percent + '%';
        if (text) text.textContent = Math.round(percent) + '%';
    }
    
    hideUploadProgress() {
        const progress = document.getElementById('fileProgress');
        if (progress) progress.style.display = 'none';
    }
    
    startStatsUpdate() {
        // Actualizar estadísticas cada 5 segundos
        setInterval(() => {
            this.updateStats();
        }, 5000);
        
        // Actualización inicial
        this.updateStats();
    }
    
    updateStats() {
        // Simular estadísticas básicas
        const stats = {
            cpu: Math.floor(Math.random() * 100),
            memory: Math.floor(Math.random() * 1000),
            sessions: this.isConnected ? 1 : 0
        };
        
        const elements = {
            cpuUsage: stats.cpu + '%',
            memoryUsage: stats.memory + ' MB',
            activeSessionsCount: stats.sessions
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
        
        // Si hay conexión activa, obtener estadísticas reales
        if (this.isConnected && this.currentSession && this.socket?.connected) {
            this.socket.emit('get_session_stats', {
                session_id: this.currentSession.id
            });
        }
    }
    
    // === FUNCIONES DE BÚSQUEDA ===
    toggleSearch() {
        const searchPanel = document.getElementById('terminalSearch');
        if (searchPanel) {
            const isVisible = searchPanel.style.display !== 'none';
            searchPanel.style.display = isVisible ? 'none' : 'block';
            
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
        if (this.searchAddon && searchInput && searchInput.value) {
            const caseSensitive = document.getElementById('searchCaseSensitive')?.checked || false;
            const regex = document.getElementById('searchRegex')?.checked || false;
            
            this.searchAddon.findNext(searchInput.value, {
                caseSensitive,
                regex
            });
        }
    }
    
    searchPrevious() {
        const searchInput = document.getElementById('searchInput');
        if (this.searchAddon && searchInput && searchInput.value) {
            const caseSensitive = document.getElementById('searchCaseSensitive')?.checked || false;
            const regex = document.getElementById('searchRegex')?.checked || false;
            
            this.searchAddon.findPrevious(searchInput.value, {
                caseSensitive,
                regex
            });
        }
    }
    
    // === PANTALLA COMPLETA ===
    toggleFullscreen() {
        const layout = document.getElementById('terminalLayout');
        if (layout) {
            layout.classList.toggle('fullscreen');
            
            // Redimensionar terminal después del cambio
            setTimeout(() => {
                if (this.fitAddon) {
                    this.fitAddon.fit();
                }
            }, 100);
            
            // Actualizar icono del botón
            const btn = document.querySelector('[onclick="toggleFullscreen()"] i');
            if (btn) {
                if (layout.classList.contains('fullscreen')) {
                    btn.className = 'fas fa-compress';
                } else {
                    btn.className = 'fas fa-expand';
                }
            }
        }
    }
    
    // === CAPTURA DE PANTALLA MEJORADA ===
    takeScreenshot() {
        try {
            if (!this.terminal) {
                this.showNotification('Terminal no disponible', 'error');
                return;
            }
            
            // Usar el addon de serialize si está disponible
            if (this.serializeAddon) {
                const content = this.serializeAddon.serialize();
                this.downloadAsFile(content, `terminal-session-${new Date().toISOString().slice(0, 19)}.txt`);
                this.showNotification('Sesión guardada como archivo de texto', 'success');
            } else {
                // Fallback: captura básica del contenido visible
                const lines = [];
                const buffer = this.terminal.buffer.active;
                for (let i = 0; i < buffer.length; i++) {
                    const line = buffer.getLine(i);
                    if (line) {
                        lines.push(line.translateToString(true));
                    }
                }
                
                const content = lines.join('\n');
                this.downloadAsFile(content, `terminal-capture-${new Date().toISOString().slice(0, 19)}.txt`);
                this.showNotification('Captura guardada', 'success');
            }
        } catch (error) {
            console.error('Error en captura:', error);
            this.showNotification('Error al tomar captura', 'error');
        }
    }
    
    downloadAsFile(content, filename) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }
    
    // === EVENTOS AVANZADOS DE CONFIGURACIÓN ===
    setupAdvancedEventHandlers() {
        // Búsqueda en tiempo real
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                if (e.target.value && this.searchAddon) {
                    this.searchNext();
                }
            });
            
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (e.shiftKey) {
                        this.searchPrevious();
                    } else {
                        this.searchNext();
                    }
                } else if (e.key === 'Escape') {
                    this.toggleSearch();
                }
            });
        }
        
        // Atajos de teclado globales
        document.addEventListener('keydown', (e) => {
            // Solo procesar si no estamos en un input
            if (e.target.tagName.toLowerCase() !== 'input' && e.target.tagName.toLowerCase() !== 'textarea') {
                if (e.ctrlKey) {
                    switch (e.key.toLowerCase()) {
                        case 'f':
                            e.preventDefault();
                            this.toggleSearch();
                            break;
                        case 'h':
                            e.preventDefault();
                            this.toggleHistory();
                            break;
                        case 's':
                            e.preventDefault();
                            this.takeScreenshot();
                            break;
                        case 'u':
                            e.preventDefault();
                            this.toggleFileTransfer();
                            break;
                        case 'enter':
                            e.preventDefault();
                            this.toggleFullscreen();
                            break;
                    }
                } else if (e.key === 'F11') {
                    e.preventDefault();
                    this.toggleFullscreen();
                }
            }
        });
        
        // Detectar cambios de tamaño de ventana
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (this.fitAddon && this.terminal) {
                    this.fitAddon.fit();
                }
            }, 150);
        });
        
        // Manejo de visibilidad de página
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && this.isConnected) {
                // Reconectar si es necesario
                if (this.socket && !this.socket.connected) {
                    this.showNotification('Reestableciendo conexión...', 'info');
                    this.socket.connect();
                }
            }
        });
    }
    
    // === MÉTODOS DE DEBUG Y DIAGNÓSTICO ===
    getDebugInfo() {
        return {
            isConnected: this.isConnected,
            isConnecting: this.isConnecting,
            currentSession: this.currentSession,
            terminalAvailable: !!this.terminal,
            socketConnected: this.socket?.connected || false,
            addonsLoaded: {
                fit: !!this.fitAddon,
                search: !!this.searchAddon,
                webLinks: !!this.webLinksAddon,
                serialize: !!this.serializeAddon
            },
            settings: this.settings,
            commandHistoryCount: this.commandHistory.length,
            sessionsCount: this.sessions.length
        };
    }
    
    // === LIMPIEZA Y CLEANUP ===
    destroy() {
        try {
            // Desconectar SSH si está conectado
            if (this.isConnected) {
                this.disconnectSession();
            }
            
            // Cerrar socket
            if (this.socket) {
                this.socket.disconnect();
                this.socket = null;
            }
            
            // Limpiar terminal
            if (this.terminal) {
                this.terminal.dispose();
                this.terminal = null;
            }
            
            // Limpiar intervalos
            if (this.heartbeatInterval) {
                clearInterval(this.heartbeatInterval);
                this.heartbeatInterval = null;
            }
            
            console.log('✅ Terminal manager destroyed');
        } catch (error) {
            console.error('Error during cleanup:', error);
        }
    }
    
    copySelection() {
        const selection = this.terminal?.getSelection?.();
        if (selection) {
            navigator.clipboard.writeText(selection).then(() => {
                this.showNotification('Texto copiado', 'success');
            });
        }
    }
    
    async pasteFromClipboard() {
        try {
            const text = await navigator.clipboard.readText();
            if (text && this.isConnected) {
                this.socket.emit('terminal_input', {
                    session_id: this.currentSession.id,
                    data: text
                });
            }
        } catch (error) {
            this.showNotification('Error al pegar', 'error');
        }
    }
    
    sendCtrlC() { this.sendSpecialKey('\x03'); }
    sendCtrlZ() { this.sendSpecialKey('\x1a'); }
    sendCtrlL() { this.sendSpecialKey('\x0c'); }
    
    sendSpecialKey(key) {
        if (this.isConnected && this.currentSession && this.socket?.connected) {
            this.socket.emit('terminal_input', {
                session_id: this.currentSession.id,
                data: key
            });
        }
    }
    
    toggleFileTransfer() {
        const panel = document.getElementById('fileTransfer');
        if (panel) {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        }
    }
    
    toggleHistory() {
        const panel = document.getElementById('commandHistory');
        if (panel) {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
            if (panel.style.display === 'block') {
                this.updateHistoryDisplay();
            }
        }
    }
}

// === INICIALIZACIÓN Y FUNCIONES GLOBALES ===
let terminalManager;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Enhanced Terminal Manager');
    try {
        terminalManager = new EnhancedSSHTerminalManager();
        
        // Debug functions
        window.getTerminalDebugInfo = () => {
            return {
                isConnected: terminalManager?.isConnected,
                currentSession: terminalManager?.currentSession,
                terminalAvailable: !!terminalManager?.terminal,
                socketConnected: terminalManager?.socket?.connected,
                addonsLoaded: {
                    fit: !!terminalManager?.fitAddon,
                    search: !!terminalManager?.searchAddon,
                    webLinks: !!terminalManager?.webLinksAddon
                }
            };
        };
        
        window.testConnection = () => terminalManager?.socket?.emit('ping', { test: true });
        
        window.showTerminalSettings = () => {
            const sidebar = document.getElementById('terminalSidebar');
            if (sidebar) {
                sidebar.scrollTo({ top: sidebar.scrollHeight, behavior: 'smooth' });
            }
        };
        
    } catch (error) {
        console.error('Error inicializando terminal manager:', error);
        
        // Mostrar mensaje de error en la página
        const container = document.getElementById('terminalContainer');
        if (container) {
            container.innerHTML = `
                <div style="color: #ff6b6b; padding: 20px; text-align: center;">
                    <h3>❌ Error al inicializar el terminal</h3>
                    <p>${error.message}</p>
                    <p>Por favor, recarga la página o contacta al administrador.</p>
                </div>
            `;
        }
    }
});

// === FUNCIONES DE COMPATIBILIDAD ===
function connectToSession() { 
    if (terminalManager) {
        terminalManager.connectToSession(); 
    } else {
        console.error('Terminal manager no disponible');
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
    if (terminalManager && terminalManager.searchAddon) {
        terminalManager.searchAddon.findNext(document.getElementById('searchInput')?.value || '');
    }
}

function searchPrevious() { 
    if (terminalManager && terminalManager.searchAddon) {
        terminalManager.searchAddon.findPrevious(document.getElementById('searchInput')?.value || '');
    }
}

function openSessionManager() { 
    window.open('/sessionsssh_bp/new', '_blank'); 
}

function toggleFileTransfer() { 
    if (terminalManager) {
        terminalManager.toggleFileTransfer(); 
    }
}

function toggleHistory() { 
    if (terminalManager) {
        terminalManager.toggleHistory(); 
    }
}

function takeScreenshot() { 
    if (terminalManager) {
        terminalManager.takeScreenshot(); 
    }
}

function copySelection() { 
    if (terminalManager) {
        terminalManager.copySelection(); 
    }
}

function pasteFromClipboard() { 
    if (terminalManager) {
        terminalManager.pasteFromClipboard(); 
    }
}

function sendCtrlC() { 
    if (terminalManager) {
        terminalManager.sendCtrlC(); 
    }
}

function sendCtrlZ() { 
    if (terminalManager) {
        terminalManager.sendCtrlZ(); 
    }
}

function sendCtrlL() { 
    if (terminalManager) {
        terminalManager.sendCtrlL(); 
    }
}