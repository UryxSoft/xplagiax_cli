// terminal_enhanced.js - SSH Terminal Manager Enhanced
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
        document.getElementById('fontSizeValue').textContent = this.settings.fontSize + 'px';
        document.getElementById('opacityValue').textContent = this.settings.opacity + '%';
    }
    
    // === TERMINAL MEJORADO ===
    initializeTerminal() {
        try {
            console.log('🖥️ Initializing enhanced terminal...');
            
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
                scrollback: 5000, // Más historial
                tabStopWidth: 4,
                rightClickSelectsWord: true,
                macOptionIsMeta: true,
                minimumContrastRatio: 4.5
            });
            
            // Cargar todos los addons modernos
            this.fitAddon = new FitAddon.FitAddon();
            this.searchAddon = new SearchAddon.SearchAddon();
            this.webLinksAddon = new WebLinksAddon.WebLinksAddon();
            this.clipboardAddon = new ClipboardAddon.ClipboardAddon();
            this.serializeAddon = new SerializeAddon.SerializeAddon();
            this.unicode11Addon = new Unicode11Addon.Unicode11Addon();
            this.imageAddon = new ImageAddon.ImageAddon();
            
            // Aplicar addons
            this.terminal.loadAddon(this.fitAddon);
            this.terminal.loadAddon(this.searchAddon);
            this.terminal.loadAddon(this.webLinksAddon);
            this.terminal.loadAddon(this.clipboardAddon);
            this.terminal.loadAddon(this.serializeAddon);
            this.terminal.loadAddon(this.unicode11Addon);
            this.terminal.loadAddon(this.imageAddon);
            
            // Activar unicode11
            this.terminal.unicode.activeVersion = '11';
            
            const terminalContainer = document.getElementById('terminalContainer');
            if (terminalContainer) {
                this.terminal.open(terminalContainer);
                
                setTimeout(() => {
                    this.fitAddon.fit();
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
    
    // === TRANSFERENCIA DE ARCHIVOS ===
    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        uploadArea?.addEventListener('click', () => fileInput?.click());
        
        uploadArea?.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea?.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea?.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFileUpload(e.dataTransfer.files);
        });
        
        fileInput?.addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });
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
            const formData = new FormData();
            formData.append('file', file);
            formData.append('session_id', this.currentSession.id);
            
            this.showUploadProgress(0);
            
            const response = await fetch('/api/upload', {
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
    
    // === FUNCIONES AVANZADAS ===
    takeScreenshot() {
        try {
            const canvas = this.terminal.buffer.active.getAsCanvas();
            const link = document.createElement('a');
            link.download = `terminal-screenshot-${new Date().toISOString().slice(0, 19)}.png`;
            link.href = canvas.toDataURL();
            link.click();
            
            this.showNotification('Captura guardada', 'success');
        } catch (error) {
            this.showNotification('Error al tomar captura', 'error');
        }
    }
    
    copySelection() {
        const selection = this.terminal.getSelection();
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
    
    handleTabCompletion() {
        // Implementar autocompletado básico
        const commonCommands = ['ls', 'cd', 'pwd', 'cat', 'grep', 'find', 'ps', 'top', 'htop', 'nano', 'vim'];
        const matches = commonCommands.filter(cmd => cmd.startsWith(this.currentCommand));
        
        if (matches.length === 1) {
            const completion = matches[0].slice(this.currentCommand.length);
            this.terminal.write(completion);
            this.currentCommand += completion;
        }
    }
    
    // === COMANDOS ESPECIALES ===
    sendCtrlC() {
        this.sendSpecialKey('\x03');
    }
    
    sendCtrlZ() {
        this.sendSpecialKey('\x1a');
    }
    
    sendCtrlL() {
        this.sendSpecialKey('\x0c');
    }
    
    sendSpecialKey(key) {
        if (this.isConnected && this.currentSession && this.socket?.connected) {
            this.socket.emit('terminal_input', {
                session_id: this.currentSession.id,
                data: key
            });
        }
    }
    
    // === SONIDOS ===
    playKeySound() {
        if (this.settings.sound) {
            const audio = new AudioContext();
            const oscillator = audio.createOscillator();
            const gainNode = audio.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audio.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'square';
            gainNode.gain.setValueAtTime(0.1, audio.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audio.currentTime + 0.1);
            
            oscillator.start(audio.currentTime);
            oscillator.stop(audio.currentTime + 0.1);
        }
    }
    
    // === NOTIFICACIONES MEJORADAS ===
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
            setTimeout(() => document.body.removeChild(notification), 300);
        }, duration);
    }
    
    // === INTERFAZ MEJORADA ===
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
        
        // Actualizar tiempo de conexión
        if (status === 'connected') {
            this.connectionStartTime = Date.now();
            this.startUptimeCounter();
        } else {
            this.connectionStartTime = null;
        }
    }
    
    startUptimeCounter() {
        setInterval(() => {
            if (this.connectionStartTime && this.isConnected) {
                const uptime = Date.now() - this.connectionStartTime;
                const seconds = Math.floor(uptime / 1000);
                const minutes = Math.floor(seconds / 60);
                const hours = Math.floor(minutes / 60);
                
                const uptimeText = hours > 0 
                    ? `${hours}h ${minutes % 60}m ${seconds % 60}s`
                    : `${minutes}m ${seconds % 60}s`;
                
                const uptimeElement = document.getElementById('sessionUptime');
                if (uptimeElement) {
                    uptimeElement.textContent = uptimeText;
                }
            }
        }, 1000);
    }
    
    // === TOGGLE FUNCTIONS ===
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
    
    // Cargar historial guardado
    loadCommandHistory() {
        const saved = localStorage.getItem('commandHistory');
        if (saved) {
            this.commandHistory = JSON.parse(saved);
        }
    }
    
    // === CONFIGURACIÓN DE EVENTOS ===
    setupEventHandlers() {
        // Configuración de ajustes
        document.getElementById('themeSelect')?.addEventListener('change', (e) => {
            this.settings.theme = e.target.value;
            this.saveSettings();
        });
        
        document.getElementById('fontSizeRange')?.addEventListener('input', (e) => {
            this.settings.fontSize = parseInt(e.target.value);
            this.saveSettings();
        });
        
        document.getElementById('opacityRange')?.addEventListener('input', (e) => {
            this.settings.opacity = parseInt(e.target.value);
            this.saveSettings();
        });
        
        document.getElementById('cursorBlinkCheck')?.addEventListener('change', (e) => {
            this.settings.cursorBlink = e.target.checked;
            this.saveSettings();
        });
        
        document.getElementById('soundCheck')?.addEventListener('change', (e) => {
            this.settings.sound = e.target.checked;
            this.saveSettings();
        });
        
        // Redimensionar terminal
        window.addEventListener('resize', () => {
            if (this.fitAddon) {
                setTimeout(() => this.fitAddon.fit(), 100);
            }
        });
        
        // Atajos de teclado mejorados
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey) {
                switch (e.key) {
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
                }
            }
        });
        
        this.loadCommandHistory();
    }
    
    // Heredar métodos de la clase original que siguen siendo válidos
    getSessionIdFromURL() {
        const path = window.location.pathname;
        const match = path.match(/\/terminal\/(\d+)/);
        return match ? match[1] : null;
    }
    
    // ... resto de métodos de la clase original ...
    // (incluir todos los métodos de conexión Socket.IO, etc.)
}

// Funciones globales
let terminalManager;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Enhanced Terminal Manager');
    terminalManager = new EnhancedSSHTerminalManager();
    
    // Debug functions
    window.getTerminalDebugInfo = () => terminalManager?.getDebugInfo();
    window.testConnection = () => terminalManager?.socket?.emit('ping', { test: true });
    window.showTerminalSettings = () => {
        const sidebar = document.getElementById('terminalSidebar');
        sidebar?.scrollTo({ top: sidebar.scrollHeight, behavior: 'smooth' });
    };
});

// Funciones de compatibilidad
function connectToSession() { terminalManager?.connectToSession(); }
function disconnectSession() { terminalManager?.disconnectSession(); }
function clearTerminal() { terminalManager?.clearTerminal(); }
function toggleFullscreen() { terminalManager?.toggleFullscreen(); }
function toggleSearch() { terminalManager?.toggleSearch(); }
function searchNext() { terminalManager?.searchNext(); }
function searchPrevious() { terminalManager?.searchPrevious(); }
function openSessionManager() { window.open('/sessionsssh_bp/new', '_blank'); }
function toggleFileTransfer() { terminalManager?.toggleFileTransfer(); }
function toggleHistory() { terminalManager?.toggleHistory(); }
function takeScreenshot() { terminalManager?.takeScreenshot(); }
function copySelection() { terminalManager?.copySelection(); }
function pasteFromClipboard() { terminalManager?.pasteFromClipboard(); }
function sendCtrlC() { terminalManager?.sendCtrlC(); }
function sendCtrlZ() { terminalManager?.sendCtrlZ(); }
function sendCtrlL() { terminalManager?.sendCtrlL(); }