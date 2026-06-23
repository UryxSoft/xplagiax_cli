class SSHTerminalManager {
    constructor() {
        this.socket = null;
        this.terminal = null;
        this.fitAddon = null;
        this.searchAddon = null;
        this.webLinksAddon = null;
        this.unicode11Addon = null;
        this.serializeAddon = null;
        this.currentSession = null;
        this.sessions = [];
        this.isConnected = false;
        this.fontSize = 14;
        this.isFullscreen = false;
        this.sidebarVisible = true;
        
        this.init();
    }

    init() {
        this.initializeSocket();
        this.initializeTerminal();
        this.loadSessions();
        this.bindKeyboardShortcuts();
        this.startStatsUpdates();
        
        // Check if session ID is in URL
        const urlPath = window.location.pathname;
        const sessionIdMatch = urlPath.match(/\/terminal\/(\d+)/);
        if (sessionIdMatch) {
            const sessionId = parseInt(sessionIdMatch[1]);
            this.autoConnectToSession(sessionId);
        }
    }

        initializeSocket() {
        this.socket = io(window.location.origin, {
                transports: ['websocket'],
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000,
                timeout: 20000
            });
        
        this.socket.on('connect', () => {
            console.log('Connected to SSH Manager');
            this.updateConnectionStatus(false);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from SSH Manager');
            this.updateConnectionStatus(false);
            this.showNotification('Lost connection to server', 'error');
        });

        this.socket.on('ssh_connected', (data) => {
            this.handleSSHConnected(data);
        });

        this.socket.on('ssh_output', (data) => {
            this.handleSSHOutput(data);
        });

        this.socket.on('ssh_error', (data) => {
            this.handleSSHError(data);
        });

        this.socket.on('session_closed', (data) => {
            this.handleSessionClosed(data);
        });
    }

    initializeTerminal() {
        // Terminal configuration with cyberpunk theme
        this.terminal = new Terminal({
            allowProposedApi: true,
            cursorBlink: true,
            cursorStyle: 'block',
            fontFamily: '"Courier New", Courier, monospace',
            fontSize: this.fontSize,
            fontWeight: 'normal',
            fontWeightBold: 'bold',
            lineHeight: 1.2,
            letterSpacing: 0,
            scrollback: 10000,
            tabStopWidth: 4,
            theme: {
                background: '#000000',
                foreground: '#00ff00',
                cursor: '#00ff00',
                cursorAccent: '#000000',
                selection: 'rgba(0, 255, 255, 0.3)',
                black: '#000000',
                red: '#ff0080',
                green: '#00ff00',
                yellow: '#ffff00',
                blue: '#0080ff',
                magenta: '#ff00ff',
                cyan: '#00ffff',
                white: '#ffffff',
                brightBlack: '#404040',
                brightRed: '#ff4080',
                brightGreen: '#40ff40',
                brightYellow: '#ffff40',
                brightBlue: '#4080ff',
                brightMagenta: '#ff40ff',
                brightCyan: '#40ffff',
                brightWhite: '#ffffff'
            },
            allowTransparency: true,
            bellSound: null,
            bellStyle: 'visual',
            convertEol: true,
            disableStdin: false,
            macOptionIsMeta: true,
            rightClickSelectsWord: true,
            fastScrollModifier: 'shift',
            fastScrollSensitivity: 5,
            scrollSensitivity: 1
        });

        // Initialize addons
        this.fitAddon = new FitAddon.FitAddon();
        this.searchAddon = new SearchAddon.SearchAddon();
        this.webLinksAddon = new WebLinksAddon.WebLinksAddon();
        this.unicode11Addon = new Unicode11Addon.Unicode11Addon();
        this.serializeAddon = new SerializeAddon.SerializeAddon();

        // Load addons
        this.terminal.loadAddon(this.fitAddon);
        this.terminal.loadAddon(this.searchAddon);
        this.terminal.loadAddon(this.webLinksAddon);
        this.terminal.loadAddon(this.unicode11Addon);
        this.terminal.loadAddon(this.serializeAddon);

        // Activate Unicode 11
        this.terminal.unicode.activeVersion = '11';

        // Open terminal in container
        const container = document.getElementById('terminalContainer');
        this.terminal.open(container);

        // Fit terminal to container
        this.fitAddon.fit();

        // Handle terminal input
        this.terminal.onData((data) => {
            if (this.isConnected && this.currentSession) {
                this.socket.emit('ssh_input', {
                    session_id: this.currentSession.id,
                    data: data
                });
            }
        });

        // Handle terminal resize
        this.terminal.onResize((size) => {
            if (this.isConnected && this.currentSession) {
                this.socket.emit('ssh_resize', {
                    session_id: this.currentSession.id,
                    cols: size.cols,
                    rows: size.rows
                });
            }
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            if (this.terminal) {
                setTimeout(() => this.fitAddon.fit(), 100);
            }
        });

        // Welcome message
        this.showWelcomeMessage();
    }

    showWelcomeMessage() {
        const welcomeText = [
            '\x1b[32m╔═══════════════════════════════════════════════════════════════════════════════╗\x1b[0m',
            '\x1b[32m║                          SSH TERMINAL MANAGER v2.0                           ║\x1b[0m',
            '\x1b[32m║                           Cyberpunk Edition                                  ║\x1b[0m',
            '\x1b[32m╚═══════════════════════════════════════════════════════════════════════════════╝\x1b[0m',
            '',
            '\x1b[36mWelcome to the SSH Terminal Manager!\x1b[0m',
            '',
            '\x1b[33mAvailable Commands:\x1b[0m',
            '  \x1b[32mhelp\x1b[0m          - Show this help message',
            '  \x1b[32msessions\x1b[0m      - List available SSH sessions',
            '  \x1b[32mconnect <id>\x1b[0m  - Connect to session by ID',
            '  \x1b[32mclear\x1b[0m         - Clear terminal',
            '  \x1b[32mstatus\x1b[0m        - Show connection status',
            '',
            '\x1b[33mKeyboard Shortcuts:\x1b[0m',
            '  \x1b[32mCtrl+Shift+F\x1b[0m  - Search terminal',
            '  \x1b[32mCtrl+Shift+C\x1b[0m  - Copy selection',
            '  \x1b[32mCtrl+Shift+V\x1b[0m  - Paste from clipboard',
            '  \x1b[32mCtrl+L\x1b[0m        - Clear terminal',
            '  \x1b[32mF11\x1b[0m           - Toggle fullscreen',
            '',
            '\x1b[35mSelect a session from the sidebar or type \'sessions\' to get started.\x1b[0m',
            '',
            '\x1b[32muser@ssh-manager:~$\x1b[0m '
        ];

        welcomeText.forEach(line => {
            this.terminal.writeln(line);
        });
    }

    async loadSessions() {
        try {
            const response = await fetch('/sessionsssh_bp/api/sessions');
            if (response.ok) {
                this.sessions = await response.json();
                this.renderSessionsList();
                this.updateStats();
            }
        } catch (error) {
            console.error('Error loading sessions:', error);
            this.showNotification('Error loading sessions', 'error');
        }
    }

    renderSessionsList() {
        const container = document.getElementById('sessionsList');
        container.innerHTML = '';

        if (this.sessions.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; color: #666; padding: 20px;">
                    <p>No sessions configured</p>
                    <p style="font-size: 12px;">Create a session to get started</p>
                </div>
            `;
            return;
        }

        this.sessions.forEach(session => {
            const sessionElement = document.createElement('div');
            sessionElement.className = 'session-option';
            if (this.currentSession && this.currentSession.id === session.id) {
                sessionElement.classList.add('active');
            }

            sessionElement.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: bold; color: #00ffff;">${session.name}</div>
                        <div style="font-size: 12px; color: #999;">${session.hostname}:${session.port}</div>
                    </div>
                    <div>
                        <span style="
                            width: 8px; 
                            height: 8px; 
                            border-radius: 50%; 
                            background: ${session.is_active ? '#00ff00' : '#ff0080'}; 
                            display: inline-block;
                            animation: pulse 2s infinite;
                        "></span>
                    </div>
                </div>
            `;

            sessionElement.onclick = () => this.selectSession(session);
            container.appendChild(sessionElement);
        });
    }

    selectSession(session) {
        this.currentSession = session;
        this.renderSessionsList();
        this.updateSessionInfo();
        this.updateTerminalTitle();
        
        if (this.isConnected) {
            this.disconnectSession();
        }
    }

    updateSessionInfo() {
        const infoElement = document.getElementById('currentSessionInfo');
        const detailsElement = document.getElementById('sessionDetails');

        if (this.currentSession) {
            infoElement.style.display = 'block';
            detailsElement.innerHTML = `
                <div style="margin-bottom: 8px;">
                    <strong>Name:</strong> ${this.currentSession.name}
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>Host:</strong> ${this.currentSession.hostname}:${this.currentSession.port}
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>User:</strong> ${this.currentSession.username}
                </div>
                <div style="margin-bottom: 8px;">
                    <strong>Status:</strong> 
                    <span style="color: ${this.isConnected ? '#00ff00' : '#ff0080'};">
                        ${this.isConnected ? 'Connected' : 'Disconnected'}
                    </span>
                </div>
            `;
        } else {
            infoElement.style.display = 'none';
        }
    }

    updateTerminalTitle() {
        const titleElement = document.getElementById('terminalTitle');
        if (this.currentSession) {
            titleElement.textContent = `${this.currentSession.name} - SSH Terminal`;
            document.title = `${this.currentSession.name} - SSH Manager`;
        } else {
            titleElement.textContent = 'SSH Terminal';
            document.title = 'SSH Terminal - SSH Manager';
        }
    }

    async autoConnectToSession(sessionId) {
        // Wait for sessions to load
        await this.loadSessions();
        
        const session = this.sessions.find(s => s.id === sessionId);
        if (session) {
            this.selectSession(session);
            setTimeout(() => {
                this.connectToSession();
            }, 500);
        } else {
            this.showNotification(`Session ${sessionId} not found`, 'error');
        }
    }

    connectToSession() {
        if (!this.currentSession) {
            this.showNotification('Please select a session first', 'error');
            return;
        }

        if (this.isConnected) {
            this.showNotification('Already connected to a session', 'info');
            return;
        }

        this.showLoading(true, `Connecting to ${this.currentSession.hostname}...`);
        
        this.socket.emit('ssh_connect', {
            session_id: this.currentSession.id
        });

        // Timeout after 30 seconds
        setTimeout(() => {
            if (!this.isConnected) {
                this.showLoading(false);
                this.showNotification('Connection timeout', 'error');
            }
        }, 30000);
    }

    disconnectSession() {
        if (!this.isConnected || !this.currentSession) {
            return;
        }

        this.socket.emit('ssh_disconnect', {
            session_id: this.currentSession.id
        });

        this.handleSessionClosed({ session_id: this.currentSession.id });
    }

    handleSSHConnected(data) {
        this.isConnected = true;
        this.showLoading(false);
        this.updateConnectionStatus(true);
        this.updateSessionInfo();
        
        // Update UI
        document.getElementById('connectBtn').style.display = 'none';
        document.getElementById('disconnectBtn').style.display = 'inline-block';
        
        this.terminal.clear();
        this.terminal.writeln('\x1b[32m╔═════════════════════════════════════════════════════════════════════════════════╗\x1b[0m');
        this.terminal.writeln('\x1b[32m║                          SSH CONNECTION ESTABLISHED                            ║\x1b[0m');
        this.terminal.writeln('\x1b[32m╚═════════════════════════════════════════════════════════════════════════════════╝\x1b[0m');
        this.terminal.writeln('');
        
        this.showNotification('Connected successfully!', 'success');
        
        // Focus terminal
        this.terminal.focus();
    }

    handleSSHOutput(data) {
        if (data.session_id === this.currentSession?.id) {
            this.terminal.write(data.output);
        }
    }

    handleSSHError(data) {
        this.showLoading(false);
        this.showNotification(`SSH Error: ${data.error}`, 'error');
        
        this.terminal.writeln('');
        this.terminal.writeln(`\x1b[31mSSH Error: ${data.error}\x1b[0m`);
        this.terminal.writeln('');
    }

    handleSessionClosed(data) {
        if (data.session_id === this.currentSession?.id) {
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.updateSessionInfo();
            
            // Update UI
            document.getElementById('connectBtn').style.display = 'inline-block';
            document.getElementById('disconnectBtn').style.display = 'none';
            
            this.terminal.writeln('');
            this.terminal.writeln('\x1b[33m╔═════════════════════════════════════════════════════════════════════════════════╗\x1b[0m');
            this.terminal.writeln('\x1b[33m║                            SSH CONNECTION CLOSED                               ║\x1b[0m');
            this.terminal.writeln('\x1b[33m╚═════════════════════════════════════════════════════════════════════════════════╝\x1b[0m');
            this.terminal.writeln('');
            
            this.showNotification('SSH session closed', 'info');
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = connected ? 'Conectado' : 'Desconectado';
            statusElement.className = connected ? 'connected' : '';
        }
    }

    bindKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Shift+F - Search
            if (e.ctrlKey && e.shiftKey && e.key === 'F') {
                e.preventDefault();
                this.toggleSearch();
            }
            
            // Ctrl+Shift+C - Copy
            if (e.ctrlKey && e.shiftKey && e.key === 'C') {
                e.preventDefault();
                this.copySelection();
            }
            
            // Ctrl+Shift+V - Paste
            if (e.ctrlKey && e.shiftKey && e.key === 'V') {
                e.preventDefault();
                this.pasteFromClipboard();
            }
            
            // Ctrl+L - Clear terminal
            if (e.ctrlKey && e.key === 'l') {
                e.preventDefault();
                this.clearTerminal();
            }
            
            // F11 - Fullscreen
            if (e.key === 'F11') {
                e.preventDefault();
                this.toggleFullscreen();
            }
            
            // Ctrl+Shift+K - Toggle shortcuts
            if (e.ctrlKey && e.shiftKey && e.key === 'K') {
                e.preventDefault();
                this.showShortcuts();
            }
            
            // Escape - Close overlays
            if (e.key === 'Escape') {
                this.closeOverlays();
            }
        });
    }

    toggleSearch() {
        const searchElement = document.getElementById('terminalSearch');
        const searchInput = document.getElementById('searchInput');
        
        if (searchElement.style.display === 'none' || !searchElement.style.display) {
            searchElement.style.display = 'block';
            searchInput.focus();
        } else {
            searchElement.style.display = 'none';
            this.terminal.focus();
        }
    }

    searchNext() {
        const searchTerm = document.getElementById('searchInput').value;
        if (searchTerm) {
            this.searchAddon.findNext(searchTerm);
        }
    }

    searchPrevious() {
        const searchTerm = document.getElementById('searchInput').value;
        if (searchTerm) {
            this.searchAddon.findPrevious(searchTerm);
        }
    }

    copySelection() {
        const selection = this.terminal.getSelection();
        if (selection) {
            navigator.clipboard.writeText(selection).then(() => {
                this.showNotification('Copied to clipboard', 'success');
            }).catch(() => {
                this.showNotification('Copy failed', 'error');
            });
        }
    }

    async pasteFromClipboard() {
        try {
            const text = await navigator.clipboard.readText();
            if (text && this.isConnected && this.currentSession) {
                this.socket.emit('ssh_input', {
                    session_id: this.currentSession.id,
                    data: text
                });
                this.showNotification('Pasted from clipboard', 'success');
            }
        } catch (error) {
            this.showNotification('Paste failed', 'error');
        }
    }

    clearTerminal() {
        this.terminal.clear();
        if (this.isConnected && this.currentSession) {
            this.socket.emit('ssh_input', {
                session_id: this.currentSession.id,
                data: 'clear\n'
            });
        }
    }

    changeFontSize(delta) {
        this.fontSize = Math.max(8, Math.min(24, this.fontSize + delta));
        this.terminal.options.fontSize = this.fontSize;
        document.getElementById('fontSizeDisplay').textContent = this.fontSize;
        
        // Refit terminal after font size change
        setTimeout(() => this.fitAddon.fit(), 100);
    }

    toggleFullscreen() {
        const layout = document.getElementById('terminalLayout');
        
        if (!this.isFullscreen) {
            layout.classList.add('fullscreen-mode');
            this.isFullscreen = true;
            this.sidebarVisible = false;
        } else {
            layout.classList.remove('fullscreen-mode');
            this.isFullscreen = false;
            this.sidebarVisible = true;
        }
        
        // Refit terminal after layout change
        setTimeout(() => this.fitAddon.fit(), 100);
    }

    toggleSidebar() {
        const sidebar = document.getElementById('terminalSidebar');
        this.sidebarVisible = !this.sidebarVisible;
        
        if (this.sidebarVisible) {
            sidebar.classList.remove('collapsed');
        } else {
            sidebar.classList.add('collapsed');
        }
        
        // Refit terminal after sidebar toggle
        setTimeout(() => this.fitAddon.fit(), 100);
    }

    showShortcuts() {
        const layout = document.getElementById('terminalLayout');
        layout.classList.toggle('shortcuts-visible');
    }

    closeOverlays() {
        document.getElementById('terminalSearch').style.display = 'none';
        document.getElementById('terminalLayout').classList.remove('shortcuts-visible');
        this.terminal.focus();
    }

    // Función actualizada updateStats()
    updateStats() {
        // Actualizar solo elementos existentes
        const activeEl = document.getElementById('activeSessionsCount');
        if (activeEl) activeEl.textContent = this.sessions.length;
        
        const memoryEl = document.getElementById('memoryUsage');
        if (memoryEl) memoryEl.textContent = '1200 MB';  // Ejemplo de dato
        
        const cpuEl = document.getElementById('cpuUsage');
        if (cpuEl) cpuEl.textContent = '15%';  // Ejemplo de dato
    }

    startStatsUpdates() {
        setInterval(() => {
            this.updateStats();
        }, 30000);
    }

    showLoading(show, message = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        const messageElement = document.getElementById('loadingMessage');
        
        if (show) {
            messageElement.textContent = message;
            overlay.style.display = 'flex';
        } else {
            overlay.style.display = 'none';
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 10000;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.5);
            border: 1px solid #00ff00;
            font-family: 'Courier New', monospace;
        `;

        if (type === 'error') {
            notification.style.backgroundColor = 'rgba(255, 0, 128, 0.9)';
            notification.style.borderColor = '#ff0080';
            notification.style.boxShadow = '0 0 20px rgba(255, 0, 128, 0.5)';
        } else if (type === 'success') {
            notification.style.backgroundColor = 'rgba(0, 255, 0, 0.9)';
            notification.style.color = '#000';
        } else {
            notification.style.backgroundColor = 'rgba(0, 255, 255, 0.9)';
            notification.style.color = '#000';
        }

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Global functions for HTML onclick events
function toggleSidebar() {
    terminalManager.toggleSidebar();
}

function connectToSession() {
    terminalManager.connectToSession();
}

function disconnectSession() {
    terminalManager.disconnectSession();
}

function toggleFullscreen() {
    terminalManager.toggleFullscreen();
}

function toggleSearch() {
    terminalManager.toggleSearch();
}

function searchNext() {
    terminalManager.searchNext();
}

function searchPrevious() {
    terminalManager.searchPrevious();
}

function clearTerminal() {
    terminalManager.clearTerminal();
}

function changeFontSize(delta) {
    terminalManager.changeFontSize(delta);
}

function showShortcuts() {
    terminalManager.showShortcuts();
}

function openSessionManager() {
    window.open('/sessions', '_blank');
}

// Initialize terminal manager when page loads
let terminalManager;
document.addEventListener('DOMContentLoaded', () => {
    terminalManager = new SSHTerminalManager();
    
    // Handle search input
    document.getElementById('searchInput').addEventListener('input', (e) => {
        const searchTerm = e.target.value;
        if (searchTerm) {
            terminalManager.searchAddon.findNext(searchTerm);
        }
    });
    
    document.getElementById('searchInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            if (e.shiftKey) {
                terminalManager.searchPrevious();
            } else {
                terminalManager.searchNext();
            }
        }
    });
});