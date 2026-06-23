// Text Editor Functionality
const textarea = document.getElementById('main-textarea');
const wordCountSpan = document.getElementById('wordCount'); // Cambiado de 'word-count' a 'wordCount'
const charCountSpan = document.getElementById('charCount'); // Cambiado de 'char-count' a 'charCount'
const fontSizeSelect = document.querySelector('.toolbar-select');
const clearBtn = document.querySelector('.clear-btn');
const copyBtn = document.querySelector('.copy-btn');
const pasteBtn = document.querySelector('.paste-btn');
const saveBtn = document.getElementById('captureBtn'); // El botón de save tiene ID 'captureBtn'

// Verificar que los elementos existen antes de usarlos
function checkElements() {
    const elements = {
        textarea,
        wordCountSpan,
        charCountSpan,
        fontSizeSelect,
        clearBtn,
        copyBtn,
        pasteBtn,
        saveBtn
    };
    
    for (let [name, element] of Object.entries(elements)) {
        if (!element) {
            console.warn(`Element ${name} not found in DOM`);
        }
    }
}

// Ejecutar verificación
checkElements();

// Word and character count
function updateCounts() {
    if (!textarea || !wordCountSpan || !charCountSpan) return;
    
    const text = textarea.value;
    const words = text.trim() === '' ? 0 : text.trim().split(/\s+/).length;
    const chars = text.length;
    
    wordCountSpan.textContent = words;
    charCountSpan.textContent = chars;
    
    // Actualizar reading time
    const readingTimeElement = document.getElementById('readingTime');
    if (readingTimeElement) {
        const readingTime = Math.ceil(words / 200); // 200 words per minute
        readingTimeElement.textContent = `${readingTime} min read`;
    }
}

// Solo agregar event listeners si los elementos existen
if (textarea) {
    textarea.addEventListener('input', updateCounts);
    textarea.addEventListener('paste', () => setTimeout(updateCounts, 10));
}

// Font size change
if (fontSizeSelect) {
    fontSizeSelect.addEventListener('change', (e) => {
        if (textarea) {
            textarea.style.fontSize = e.target.value + 'px';
        }
    });
}

// HTML del modal (agregar al HTML)
const clearModalHTML = `
    <div class="logout-modal-overlay" id="clearModalOverlay">
        <div class="logout-modal-container">
            <div class="logout-modal-header">
                <div class="logout-modal-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                        <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
                        <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
                    </svg>
                </div>
                <h3 class="logout-modal-title">Clear all content?</h3>
                <p class="logout-modal-message">
                    This action will permanently delete all your text. This cannot be undone.
                </p>
            </div>
            <div class="logout-modal-footer">
                <button class="logout-btn logout-btn-cancel" id="clearModalCancel">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-x-square" viewBox="0 0 16 16">
                        <path d="M14 1a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H2a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1zM2 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2z"/>
                        <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708"/>
                    </svg>
                    Cancel
                </button>
                <button class="logout-btn logout-btn-danger" id="clearModalConfirm">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16">
                       <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/>
                       <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/>
                    </svg>
                    Clear Content
                </button>
            </div>
        </div>
    </div>
`;

// Insertar el modal en el DOM si no existe ya
if (!document.getElementById('clearModalOverlay')) {
    document.body.insertAdjacentHTML('beforeend', clearModalHTML);
}

// Elementos del modal
const clearModalOverlay = document.getElementById('clearModalOverlay');
const clearModalCancel = document.getElementById('clearModalCancel');
const clearModalConfirm = document.getElementById('clearModalConfirm');

// Funciones del modal
function showClearModal() {
    if (clearModalOverlay) {
        clearModalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function hideClearModal() {
    if (clearModalOverlay) {
        clearModalOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Event listeners del modal (solo si existen)
if (clearModalCancel) {
    clearModalCancel.addEventListener('click', hideClearModal);
}

if (clearModalOverlay) {
    clearModalOverlay.addEventListener('click', (e) => {
        if (e.target === clearModalOverlay) {
            hideClearModal();
        }
    });
}

// Cerrar modal con ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && clearModalOverlay && clearModalOverlay.classList.contains('active')) {
        hideClearModal();
    }
});

// Event listener del clearBtn (solo si existe)
if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        if (textarea && textarea.value.trim() !== '') {
            showClearModal();
        }
    });
}

// Confirmar acción de limpiar
if (clearModalConfirm) {
    clearModalConfirm.addEventListener('click', () => {
        // Mostrar estado de carga
        clearModalConfirm.classList.add('logout-btn-loading');
        clearModalConfirm.innerHTML = `
            <div class="logout-spinner"></div>
            Clearing...
        `;
        
        // Simular un pequeño delay para mejor UX
        setTimeout(() => {
            if (textarea) {
                textarea.value = '';
                updateCounts();
                textarea.focus();
            }

            // Limpiar el overlay de highlights si existe
            if (window.aiDetector && typeof window.aiDetector.clearTextHighlights === 'function') {
                window.aiDetector.clearTextHighlights();
                console.log('🧹 Overlay limpiado desde botón Clear');
            }
            
            // También limpiar el overlay directamente por si acaso
            const textOverlay = document.getElementById('text-highlight-overlay');
            if (textOverlay) {
                textOverlay.innerHTML = '';
                textOverlay.style.display = 'none';
            }
            
            // Ocultar área de resultados
            const resultsArea = document.getElementById('results-area');
            if (resultsArea) {
                resultsArea.classList.add('hidden');
                resultsArea.classList.remove('show');
            }
            

            showNotification('Content cleared', 'info');
            hideClearModal();
            
            // Restaurar botón
            clearModalConfirm.classList.remove('logout-btn-loading');
            clearModalConfirm.innerHTML = `
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
                Clear Content
            `;
        }, 300);
    });
}

// Copy button
if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
        if (!textarea || textarea.value.trim() === '') {
            showNotification('Nothing to copy', 'warning');
            return;
        }

        try {
            await navigator.clipboard.writeText(textarea.value);
            showNotification('Content copied to clipboard', 'success');
        } catch (err) {
            // Fallback for older browsers
            if (textarea) {
                textarea.select();
                document.execCommand('copy');
                showNotification('Content copied to clipboard', 'success');
            }
        }
    });
}

if (pasteBtn) {
    pasteBtn.addEventListener('click', async () => {
        if (!textarea) {
            showNotification('Textarea not found', 'error');
            return;
        }

        try {
            const text = await navigator.clipboard.readText();
            if (!text) {
                showNotification('Clipboard is empty', 'warning');
                return;
            }

            textarea.value = text;
            showNotification('Content pasted from clipboard', 'success');
        } catch (err) {
            // Fallback for browsers that do not support navigator.clipboard.readText()
            textarea.focus();
            showNotification('Your browser does not support direct paste access. Use Ctrl + V', 'warning');
        }
    });
}

// Save button
if (saveBtn) {
    saveBtn.addEventListener('click', () => {
        if (!textarea || textarea.value.trim() === '') {
            showNotification('Nothing to save', 'warning');
            return;
        }

        const content = textarea.value;
        const filename = 'document_' + new Date().toISOString().slice(0, 19).replace(/:/g, '-') + '.txt';
        
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showNotification('Document saved successfully', 'success');
    });
}

// Auto-resize textarea
function autoResize() {
    if (textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.max(400, textarea.scrollHeight) + 'px';
    }
}

if (textarea) {
    textarea.addEventListener('input', autoResize);
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const colors = {
        success: '#22c55e',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#3b82f6'
    };
    
    notification.style.cssText = `
        position: fixed;
        top: 2rem;
        right: 2rem;
        background: ${colors[type]};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.75rem;
        box-shadow: rgba(0, 0, 0, 0.1) 0px 8px 24px;
        z-index: 3000;
        font-weight: 600;
        animation: slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        max-width: 300px;
        word-wrap: break-word;
    `;
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

// Keyboard shortcuts for text editor
if (textarea) {
    textarea.addEventListener('keydown', (e) => {
        // Ctrl+S or Cmd+S to save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            if (saveBtn) saveBtn.click();
        }
        
        // Ctrl+A or Cmd+A to select all
        if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
            e.preventDefault();
            textarea.select();
        }
        
        // Tab key support
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            
            textarea.value = textarea.value.substring(0, start) + '    ' + textarea.value.substring(end);
            textarea.selectionStart = textarea.selectionEnd = start + 4;
            
            updateCounts();
        }
    });
}

// Initialize counts
updateCounts();

// Add smooth scroll behavior for elements that exist
const tabPanelCard = document.querySelector('.tab-panel-card');
if (tabPanelCard) {
    tabPanelCard.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
    });
}

// Add CSS for notification animations if not already added
if (!document.getElementById('notificationStyles')) {
    const notificationStyle = document.createElement('style');
    notificationStyle.id = 'notificationStyles';
    document.head.appendChild(notificationStyle);
}

console.log('JavaScript loaded successfully');