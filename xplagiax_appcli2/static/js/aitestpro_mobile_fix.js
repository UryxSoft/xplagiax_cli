// AI Detector Pro - Mobile Optimized JavaScript
// Fixed version for Android Chrome issues

class AIDetectorApp {
    constructor() {
        // Configuration
        this.config = {
            maxWords: 5000,
            maxParagraphs: 100,
            analysisDelay: 1000,
            cacheMaxAge: 10 * 60 * 1000, // 10 minutes
            maxFreeUses4: 100,
            apiUrl: window.location.origin,
            fetchTimeout: 30000, // 30 segundos timeout
            maxRetries: 3
        };

        // State
        this.state = {
            analysisTimeout: null,
            previousText: '',
            currentUses: this.getSafeStorageValue('aiDetectorUses', 0),
            isAnalyzing: false,
            retryCount: 0
        };

        // Mobile-safe cache
        this.cache = new Map();
        
        // DOM elements cache
        this.elements = {};
        
        // Mobile detection
        this.isMobile = this.detectMobile();
        
        // Initialize with mobile-specific checks
        this.init();
    }

    // Mobile detection utility
    detectMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    // Safe localStorage wrapper for mobile
    getSafeStorageValue(key, defaultValue) {
        try {
            const value = localStorage.getItem(key);
            return value ? parseInt(value) : defaultValue;
        } catch (e) {
            //console.warn('localStorage not available:', e);
            return defaultValue;
        }
    }

    setSafeStorageValue(key, value) {
        try {
            localStorage.setItem(key, value);
            return true;
        } catch (e) {
            //console.warn('localStorage write failed:', e);
            return false;
        }
    }

    init() {
        //console.log('Initializing AI Detector Pro... Mobile:', this.isMobile);
        
        // Cache DOM elements
        this.cacheElements();
        
        // *** AGREGAR ESTA LÍNEA ***
        this.addHighlightStyles(); // Agregar estilos CSS necesarios

        this.createTextHighlightOverlay();    

        // Initialize modules
        this.initTextAnalysis();
        
        this.initEventListeners();
        
        // Mobile-specific initialization
        if (this.isMobile) {
            this.initMobileOptimizations();
        }
        
        // Setup periodic tasks
        this.startPeriodicTasks();
        
        // Initial state setup
        this.updateUsageDisplay();
        this.autoResizeTextarea();
        
        // Check for initial text
        const initialText = this.elements.textarea?.value?.trim();
        if (initialText) {
            this.updateWordCount();
            this.scheduleAnalysis();
        }
        
        //console.log('AI Detector Pro initialized successfully');
    }

    // Mobile-specific optimizations
    initMobileOptimizations() {
        // Prevent zoom on input focus (already in CSS but adding JS fallback)
        const inputs = document.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.style.fontSize = '16px';
        });

        // Add touch event listeners for better responsiveness
        document.addEventListener('touchstart', () => {}, { passive: true });
        
        // Optimize for mobile viewport
        const viewport = document.querySelector('meta[name=viewport]');
        if (viewport) {
            viewport.setAttribute('content', 
                'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes, viewport-fit=cover'
            );
        }

        // Add visibility change handler for mobile tab switching
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
    }

    handleVisibilityChange() {
        if (document.hidden && this.state.isAnalyzing) {
            //console.log('Tab became hidden during analysis, maintaining state');
        }
    }

    cacheElements() {
        // Cache frequently used elements for performance
        const selectors = {
            textarea: '#main-textarea',
            wordCounter: '.word-counter',
            resultsArea: '#results-area',
            analysisResults: '#analysis-results',
            loadingOverlay: '#loading-overlay',
            scannerAnimation: '.scanner-animation',
            scoreCircle: '#score-circle',
            scoreValue: '#score-value',
            scoreMessage: '#score-message',
            humanPercentage: '#human-percentage',
            aiPercentage: '#ai-percentage',
            humanBar: '#human-bar',
            aiBar: '#ai-bar',
            usageCounter: '#usage-counter'
        };

        Object.entries(selectors).forEach(([key, selector]) => {
            this.elements[key] = document.querySelector(selector);
        });

        // Cache sidebar links
        this.elements.sidebarLinks = document.querySelectorAll('.sidebar-links a');
        this.elements.searchInput = document.querySelector('#sidebar-search');
        
        // Cache accessibility checkboxes
        this.elements.accessibilityCheckboxes = {
            highContrast: document.querySelector('#high-contrast-toggle'),
            largerText: document.querySelector('#larger-text-toggle'),
            reduceMotion: document.querySelector('#reduce-motion-toggle')
        };
    }



    // ===== TEXT ANALYSIS MODULE =====
    initTextAnalysis() {
        const { textarea } = this.elements;
        if (!textarea) return;

        // Optimize event listeners with passive listeners where possible
        textarea.addEventListener('input', this.handleTextInput.bind(this));
        textarea.addEventListener('paste', () => {
            // Use setTimeout instead of requestAnimationFrame for mobile compatibility
            setTimeout(() => {
                this.updateWordCount();
                this.autoResizeTextarea();
                this.scheduleAnalysis();
            }, 10);
        });

        // Focus events
        textarea.addEventListener('focus', () => {
            textarea.parentNode.classList.add('focused');
        });
        textarea.addEventListener('blur', () => {
            textarea.parentNode.classList.remove('focused');
        });

        // Initially hide results
        this.elements.resultsArea?.classList.add('hidden');
    }

    handleTextInput_() {
        this.updateWordCount();
        this.autoResizeTextarea();
        this.scheduleAnalysis();
        //  CAMBIO 4: Limpiar highlights si el textarea está vacío
        const currentText = this.elements.textarea?.value?.trim();
        if (!currentText && this.elements.textOverlay) {
            this.elements.textOverlay.innerHTML = '';
            this.elements.textOverlay.style.display = 'none';
            console.log('🧹 Textarea vacío - highlights limpiados automáticamente');
        }
    }

    handleTextInput() {
        this.updateWordCount();
        this.autoResizeTextarea();
        this.scheduleAnalysis();
        
        //  Limpiar highlights automáticamente si está vacío
        const currentText = this.elements.textarea?.value || '';
        
        if (!currentText.trim() && this.elements.textOverlay) {
            console.log('Input vacío - limpiando overlay automáticamente');
            this.elements.textOverlay.innerHTML = '';
            this.elements.textOverlay.style.display = 'none';
            
            // También ocultar resultados
            const resultsArea = document.getElementById('results-area');
            if (resultsArea) {
                resultsArea.classList.add('hidden');
                resultsArea.classList.remove('show');
            }
        }
    }

    updateWordCount() {
        const { textarea, wordCounter } = this.elements;
        if (!textarea || !wordCounter) return;

        const text = textarea.value;
        const wordCount = text.trim() === '' ? 0 : text.trim().split(/\s+/).length;
        
        wordCounter.textContent = `${wordCount}/${this.config.maxWords} words`;
        
        // Performance optimization: only toggle class when needed
        const shouldHaveLimit = wordCount > this.config.maxWords;
        const hasLimit = wordCounter.classList.contains('limit-reached');
        
        if (shouldHaveLimit !== hasLimit) {
            wordCounter.classList.toggle('limit-reached', shouldHaveLimit);
        }
    }

    autoResizeTextarea() {
        const { textarea } = this.elements;
        if (!textarea) return;
        
        // Use setTimeout for better mobile compatibility instead of requestAnimationFrame
        setTimeout(() => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(500, Math.max(300, textarea.scrollHeight)) + 'px';
        }, 10);
    }

    scheduleAnalysis() {
        // Auto-análisis DESACTIVADO: pegar o escribir texto en #main-textarea ya
        // NO dispara un análisis automático. El análisis solo se ejecuta de forma
        // manual (botón Analysis / Ctrl+Enter). Se cancela cualquier análisis
        // pendiente y no se programa ninguno nuevo.
        if (this.state.analysisTimeout) {
            clearTimeout(this.state.analysisTimeout);
            this.state.analysisTimeout = null;
        }
        return;
    }

    // Mobile-optimized fetch with timeout and retry logic
    async fetchWithTimeout(url, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.fetchTimeout);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - please check your connection');
            }
            throw error;
        }
    }

    async analyzeText(text) {
        if (!this.checkUsageLimit() || this.state.isAnalyzing) return;

        this.state.isAnalyzing = true;
        this.state.retryCount = 0;

        // Check cache
        const cacheKey = this.hashText(text);
        if (this.cache.has(cacheKey)) {
            this.displayResults(this.cache.get(cacheKey));
            this.state.isAnalyzing = false;
            return;
        }

        //  VALIDAR LÍMITE ANTES DE MOSTRAR LOADING
        try {
            const statsResponse = await fetch('/x_analysiscounter/api/analysis/stats');
            const statsData = await statsResponse.json();
            
            if (statsData.success && statsData.data.remaining === 0) {
                //  Límite alcanzado - mostrar modal directamente
                this.state.isAnalyzing = false;
                
                const modal = document.getElementById('upgradeModal');
                if (modal) {
                    modal.classList.add('active');
                    document.body.style.overflow = 'hidden';
                }
                
                this.loadAndRenderPlans();
                this.showNotification('Daily analysis limit reached. Please upgrade your plan.', 'warning');
                return; // ⚠️ Detener aquí - no continuar con el análisis
            }
        } catch (error) {
            console.error('Error checking stats:', error);
            // Continuar con el análisis si falla la validación
        }

        // Show loading state (solo si pasó la validación)
        this.showLoadingState();

        await this.performAnalysisWithRetry(text, cacheKey);
    }


    async performAnalysisWithRetry(text, cacheKey) {
        try {
            // Split text into paragraphs for batch analysis
            const paragraphs = text.split(/\n\s*\n/)
                .filter(p => p.trim() !== '')
                .slice(0, this.config.maxParagraphs);
                    
            if (paragraphs.length === 0) {
                this.hideLoadingState();
                this.state.isAnalyzing = false;
                return;
            }

            // Mobile-optimized API request with timeout
            const response = await this.fetchWithTimeout(`/x_analysiscounter/api/analysis/validate-and-analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ texts: paragraphs })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // ACTUALIZAR EL CONTADOR Y VERIFICAR SI SE BLOQUEÓ
            const canContinue = this.updateMiniProgress(data);
            
            //  Si updateMiniProgress devuelve false, detener el análisis
            if (!canContinue) {
                this.hideLoadingState();
                this.state.isAnalyzing = false;
                return;
            }
                    
            if (data.success) {
                // Cache the result with timestamp
                data.timestamp = Date.now();
                this.cache.set(cacheKey, data.result);
                            
                // Increment usage counter
                this.incrementUsageCounter();
                            
                // Display results with slight delay for UX
                setTimeout(() => {
                    this.displayResults(data.result);
                    this.hideLoadingState();
                    this.state.isAnalyzing = false;
                }, 500);
            } else {
                // ⚠️ Si el servidor indica límite alcanzado, no throw error
                if (data.limit_reached) {
                    this.hideLoadingState();
                    this.state.isAnalyzing = false;
                    return;
                }
                throw new Error(data.error || 'Analysis failed');
            }
        } catch (error) {
            console.error('Error analyzing text:', error);
                    
            // Retry logic for mobile networks
            if (this.state.retryCount < this.config.maxRetries &&
                (error.message.includes('timeout') || error.message.includes('network') || error.message.includes('fetch'))) {
                            
                this.state.retryCount++;
                            
                // Update loading text to show retry
                const loadingText = document.querySelector('.loading-text');
                if (loadingText) {
                    loadingText.textContent = `Retrying... (${this.state.retryCount}/${this.config.maxRetries})`;
                }
                            
                // Wait before retry with exponential backoff
                setTimeout(() => {
                    this.performAnalysisWithRetry(text, cacheKey);
                }, 1000 * this.state.retryCount);
                            
                return;
            }
                    
            this.displayError(error.message);
            this.hideLoadingState();
            this.state.isAnalyzing = false;
        }
    }

    //  NUEVO MÉTODO: Cargar y renderizar planes
    async loadAndRenderPlans() {
        try {
            const response = await fetch('/x_analysiscounter/api/analysis/plans');
            const data = await response.json();
            
            if (data.success) {
                this.renderPlansInModal(data.plans, data.current_plan);
            } else {
                // Mostrar mensaje de error en el container
                const container = document.getElementById('pricingCardsContainer');
                if (container) {
                    container.innerHTML = `
                        <div class="error-loading-plans">
                            <i class="fas fa-exclamation-circle"></i>
                            <p>Unable to load plans. Please refresh the page.</p>
                        </div>
                    `;
                }
            }
        } catch (error) {
            console.error('Error loading plans:', error);
            const container = document.getElementById('pricingCardsContainer');
            if (container) {
                container.innerHTML = `
                    <div class="error-loading-plans">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>Network error. Please check your connection.</p>
                    </div>
                `;
            }
        }
    }

    //  MÉTODO ACTUALIZADO: Actualizar Mini Progress 
    updateMiniProgress(data) {
        
        // Verificar si hay stats en la respuesta
        if (!data || !data.stats) {
            //console.warn('⚠️ No stats available in response');
            return true;
        }
        
        const stats = data.stats;
        const { used, limit, remaining, percentage } = stats;
        
        // 1. Actualizar el número del contador
        const numberEl = document.getElementById('miniProgressNumber');
        if (numberEl) {
            numberEl.textContent = `${remaining}/${limit}`;
            //console.log(`✅ Número actualizado: ${remaining}/${limit}`);
        }
        
        // 2. Actualizar barra circular
        const progressBar = document.getElementById('miniProgressBar');
        if (progressBar) {
            const circumference = 125.66; // 2 * PI * 20
            const remainingPercentage = (remaining / limit) * 100;
            const offset = circumference - (remainingPercentage / 100 * circumference);
            
            progressBar.style.strokeDashoffset = offset;
            
            // Cambiar color según porcentaje restante
            progressBar.classList.remove('blue', 'green', 'red', 'orange');
            if (remainingPercentage > 50) {
                progressBar.classList.add('green');
            } else if (remainingPercentage > 30) {
                progressBar.classList.add('blue');
            } else if (remainingPercentage > 10) {
                progressBar.classList.add('orange');
            } else {
                progressBar.classList.add('red');
            }
            
        }
        
        // 3. Actualizar badge crítico/advertencia
        const badge = document.getElementById('criticalBadge');
        if (badge) {
            badge.classList.remove('show', 'critical-badge', 'warning-badge');
            
            const remainingPercentage = (remaining / limit) * 100;
            
            if (remaining === 0) {
                // Estado crítico (rojo) - agotado
                badge.classList.add('critical-badge', 'show');
                badge.textContent = '!';
            } else if (remainingPercentage <= 20) {
                // Estado advertencia (naranja) - 20% o menos
                badge.classList.add('warning-badge', 'show');
                badge.textContent = '⚠';
            }
        }
        
        // 4. Actualizar tooltip si existe
        const tooltipRemaining = document.getElementById('tooltipRemaining');
        const tooltipLimit = document.getElementById('tooltipLimit');
        if (tooltipRemaining) tooltipRemaining.textContent = remaining;
        if (tooltipLimit) tooltipLimit.textContent = limit;
        
        // 5. MOSTRAR MODAL SI EL CONTADOR LLEGÓ A 0 
        if (remaining === 0) {            
            // Mostrar modal primero
            const modal = document.getElementById('upgradeModal');
            if (modal) {
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
            
            // Siempre cargar planes con nuestra lógica personalizada
            this.loadAndRenderPlans();
            
            // Mostrar notificación
            this.showNotification('Daily analysis limit reached. Please upgrade your plan.', 'warning');
        }
        
        // 6. Manejar límite alcanzado desde el servidor (por si acaso)
        if (!data.success && data.limit_reached) {
            
            if (window.analysisTracker && typeof window.analysisTracker.showUpgradeModal === 'function') {
                window.analysisTracker.stats = stats;
                window.analysisTracker.showUpgradeModal();
            } else {
                this.showUpgradeModalFallback();
            }
            
            //this.showNotification('Daily analysis limit reached. Please upgrade your plan.', 'warning');
            
            // Detener el análisis
            this.hideLoadingState();
            this.state.isAnalyzing = false;
            
            return false;
        }
        
        // 7. Manejar sesión expirada
        if (!data.success && data.requires_login) {
            //console.log('🔒 Sesión expirada');
            this.showNotification('Your session has expired. Please login again.', 'error');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
            return false;
        }
        
        //console.log('✅ Mini-progress actualizado completamente');
        return true;
    }

    //  NUEVO MÉTODO: Fallback para mostrar modal y cargar planes 
    async showUpgradeModalFallback() {
        
        const modal = document.getElementById('upgradeModal');
        if (!modal) {
            return;
        }
        
        // Mostrar modal
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        //console.log('✅ Modal mostrado');
        
        // Cargar planes desde el API
        try {
            const response = await fetch('/x_analysiscounter/api/analysis/plans');
            const data = await response.json();
            
            if (data.success) {
                this.renderPlansInModal(data.plans, data.current_plan);
            } else {
                return;
            }
        } catch (error) {
            return;
        }
    }

    renderPlansInModal(plans, currentPlan) {
        const container = document.getElementById('pricingCardsContainer');
        if (!container) {
            return;
        }
        
        // Jerarquía de planes
        const planHierarchy = {
            'Starter': 0,
            'Scholar Suite': 1,
            'Individual': 2,
            'Research Essentials': 3
        };
        
        const currentPlanLevel = planHierarchy[currentPlan] || 0;
        
        // Lógica de filtrado según plan actual
        let filteredPlans;
        
        if (currentPlan === 'Starter') {
            filteredPlans = plans.filter(p => 
                p.name === 'Scholar Suite' || 
                p.name === 'Individual' || 
                p.name === 'Research Essentials'
            );
        } else if (currentPlan === 'Scholar Suite') {
            filteredPlans = plans.filter(p => 
                p.name === 'Individual' || 
                p.name === 'Research Essentials'
            );
        } else if (currentPlan === 'Individual') {
            filteredPlans = plans.filter(p => 
                p.name === 'Research Essentials'
            );
        } else if (currentPlan === 'Research Essentials') {
            // ✅ MOSTRAR MENSAJE CON TEMPORIZADOR CORRECTO
            container.innerHTML = `
                <div class="max-plan-message">
                    <div class="max-plan-icon">
                        <i class="fas fa-crown"></i>
                    </div>
                    <h3>You're on the highest plan!</h3>
                    <p>You have access to all features and the maximum daily analysis limit.</p>
                    <div class="reset-timer-large">
                        <i class="fas fa-clock"></i>
                        <span>Your daily limit resets in: <strong id="countdownTimerLarge">--:--:--</strong></span>
                    </div>
                    <div class="limit-info-large">
                        <p class="limit-reached-info" id="limitReachedInfo"></p>
                    </div>
                </div>
            `;
            
            // ✅ Iniciar temporizador correcto
            this.startPersonalizedCountdown();
            return;
            
        } else {
            filteredPlans = plans.filter(p => 
                p.name !== 'Starter' && p.name !== 'Institutes'
            );
        }
        
        // Ordenar y renderizar planes
        const planPriority = ['Scholar Suite', 'Individual', 'Research Essentials'];
        const sortedPlans = filteredPlans.sort((a, b) => 
            planPriority.indexOf(a.name) - planPriority.indexOf(b.name)
        );
        
        // ✅ AGREGAR TEMPORIZADOR EN LA PARTE SUPERIOR DEL MODAL
        let timerHtml = '';
        if (this.currentStats && this.currentStats.remaining === 0) {
            timerHtml = `
                <div class="modal-timer-section">
                    <div class="timer-header">
                        <i class="fas fa-hourglass-half"></i>
                        <h4>Limit Reached</h4>
                    </div>
                    <div class="reset-timer-display">
                        <p>Your daily limit will reset in:</p>
                        <div class="countdown-display" id="countdownTimerModal">--:--:--</div>
                        <p class="timer-subtitle" id="limitReachedInfoModal"></p>
                    </div>
                </div>
                <div class="modal-divider">
                    <span>Or upgrade your plan now</span>
                </div>
            `;
        }
        
        container.innerHTML = timerHtml + sortedPlans.map((plan) => {
            const isCurrent = plan.name === currentPlan;
            const isFeatured = plan.name === 'Individual';
            const storageGB = (plan.storage_mb / 1024).toFixed(0);
            
            const planLevel = planHierarchy[plan.name] || 0;
            const isDisabled = planLevel <= currentPlanLevel;
            
            return `
                <div class="pricing-card ${isFeatured ? 'featured' : ''} ${isCurrent ? 'current-plan' : ''} ${isDisabled ? 'disabled-plan' : ''}">
                    ${isCurrent ? '<div class="current-plan-badge">Your Current Plan</div>' : ''}
                    ${isDisabled && !isCurrent ? '<div class="not-upgrade-badge">Not an Upgrade</div>' : ''}
                    <div class="plan-name">${this.escapeHtml(plan.name)}</div>
                    <div class="plan-description">${this.escapeHtml(plan.description)}</div>
                    <div class="plan-price">$${plan.price_monthly}</div>
                    <div class="plan-period">per month</div>
                    
                    <ul class="plan-features">
                        <li><strong>${plan.daily_analysis_limit}</strong> daily analyses</li>
                        <li><strong>${storageGB} GB</strong> storage</li>
                        <li>Advanced plagiarism detection</li>
                        <li>Priority support</li>
                    </ul>
                    
                    <button class="plan-button ${isFeatured && !isDisabled ? 'primary' : 'secondary'}" 
                            onclick="window.location.href='/checkout?plan=${encodeURIComponent(plan.name)}'"
                            ${isDisabled ? 'disabled' : ''}>
                        ${isCurrent ? 'Current Plan' : isDisabled ? 'Not Available' : 'Upgrade Now'}
                    </button>
                </div>
            `;
        }).join('');
        
        // ✅ Iniciar temporizador si hay uno en el modal
        if (timerHtml) {
            this.startPersonalizedCountdown('countdownTimerModal', 'limitReachedInfoModal');
        }
    }

    // ✅ NUEVO MÉTODO: Iniciar temporizador personalizado de 24 horas
    startPersonalizedCountdown(timerId = 'countdownTimerLarge', infoId = 'limitReachedInfo') {
        fetch('/x_analysiscounter/api/analysis/stats')
            .then(response => response.json())
            .then(data => {
                if (!data.success || !data.data) {
                    return;
                }
                
                const stats = data.data;
                
                // ✅ Usar reset_in_seconds del servidor (calculado desde limit_reached_at)
                let secondsRemaining = stats.reset_in_seconds || 0;
                
                // Mostrar información de cuándo se alcanzó el límite
                const infoEl = document.getElementById(infoId);
                if (infoEl && stats.limit_reached_at) {
                    const limitDate = new Date(stats.limit_reached_at);
                    const resetDate = new Date(stats.reset_at);
                    
                    infoEl.innerHTML = `
                        <small>
                            Limit reached: ${limitDate.toLocaleString()}<br>
                            Resets at: ${resetDate.toLocaleString()}
                        </small>
                    `;
                }
                
                // Actualizar cada segundo
                const updateTimer = () => {
                    if (secondsRemaining <= 0) {
                        // ✅ Cuando llega a 0, recargar la página
                        const timerEl = document.getElementById(timerId);
                        if (timerEl) {
                            timerEl.innerHTML = '<span style="color: #28a745;">✓ Reset Complete!</span>';
                        }
                        
                        setTimeout(() => {
                            location.reload();
                        }, 2000);
                        return;
                    }
                    
                    const hours = Math.floor(secondsRemaining / 3600);
                    const minutes = Math.floor((secondsRemaining % 3600) / 60);
                    const seconds = secondsRemaining % 60;
                    
                    const timeString = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                    
                    const timerEl = document.getElementById(timerId);
                    if (timerEl) {
                        timerEl.textContent = timeString;
                        
                        // ✅ Cambiar color según tiempo restante
                        if (hours < 1) {
                            timerEl.style.color = '#d9534f'; // Rojo si queda menos de 1 hora
                        } else if (hours < 6) {
                            timerEl.style.color = '#f0ad4e'; // Naranja si quedan menos de 6 horas
                        } else {
                            timerEl.style.color = '#5bc0de'; // Azul normal
                        }
                    }
                    
                    secondsRemaining--;
                };
                
                // Iniciar actualización
                updateTimer();
                const intervalId = setInterval(updateTimer, 1000);
                
                // Guardar interval para limpiarlo si es necesario
                this.countdownInterval = intervalId;
            })
            .catch(error => {
                console.error('Error loading countdown:', error);
                const timerEl = document.getElementById(timerId);
                if (timerEl) {
                    timerEl.textContent = 'Error loading timer';
                    timerEl.style.color = '#d9534f';
                }
            });
    }

    // ✅ MÉTODO ACTUALIZADO: Remover el método anterior y usar este
    updateCountdownInMessage() {
        // Usar el nuevo método personalizado
        this.startPersonalizedCountdown();
    }

    // ✅ AGREGAR: Limpiar interval cuando se cierra el modal
    closeUpgradeModal() {
        const modal = document.getElementById('upgradeModal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
        
        // Limpiar interval del countdown
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
    }

    showChunkSummary(statistics) {
        if (!this.elements.analysisResults) return;
        
        // Model mapping (same as original)
        const modelTexts = {
            0: '13B', 1: '30B', 2: '65B', 3: '7B', 4: 'GLM130B', 5: 'bloom_7b',
            6: 'bloomz', 7: 'cohere', 8: 'davinci', 9: 'dolly', 10: 'dolly-v2-12b',
            11: 'flan_t5_base', 12: 'flan_t5_large', 13: 'flan_t5_small',
            14: 'flan_t5_xl', 15: 'flan_t5_xxl', 16: 'gemma-7b-it', 17: 'gemma2-9b-it',
            18: 'gpt-3.5-turbo', 19: 'gpt-35', 20: 'gpt4', 21: 'gpt4o',
            22: 'gpt_j', 23: 'gpt_neox', 24: 'human', 25: 'llama3-70b', 26: 'llama3-8b',
            27: 'mixtral-8x7b', 28: 'opt_1.3b', 29: 'opt_125m', 30: 'opt_13b',
            31: 'opt_2.7b', 32: 'opt_30b', 33: 'opt_350m', 34: 'opt_6.7b',
            35: 'opt_iml_30b', 36: 'opt_iml_max_1.3b', 37: 't0_11b', 38: 't0_3b',
            39: 'text-davinci-002', 40: 'text-davinci-003'
        };

        const modelImages = {
            0: '🤖', 1: '🤖', 2: '🤖', 
            3: '🤖', 
            4: '/static/img/models/GML103B.webp',
            5: '/static/img/models/BLOOM7B.webp', 
            6: '/static/img/models/BLOOMZ.webp',
            7: '/static/img/models/cohere-color.webp',
            8: '/static/img/models/davinci.webp', 
            9: '/static/img/models/llm-dolly.webp', 
            10: 'static/img/models/llm-dolly.webp', 
            11: '/static/img/models/flan-t5-llm.webp',
            12: '/static/img/models/flan-t5-llm.webp', 
            13: '/static/img/models/flan-t5-llm.webp', 
            14: '/static/img/models/flan-t5-llm.webp', 
            15: '/static/img/models/flan-t5-llm.webp', 
            16: '/static/img/models/gemma2LLM.webp',
            17: '/static/img/models/gemma2LLM.webp', 
            18: '/static/img/models/CHATGPT.webp', 
            19: '/static/img/models/CHATGPT.webp',  
            20: '/static/img/models/CHATGPT4.webp', 
            21: '/static/img/models/GPT-J.webp', 
            22: '/static/img/models/GPT-NEOX.webp',
            23: 'static/img/models/GPT-NEOX.webp', 
            24: '/static/img/models/Llama-AI-3.webp',
            25: '/static/img/models/Llama-AI-3.webp', 
            26: '/static/img/models/Llama-AI-3.webp', 
            27: 'static/img/models/MISTRAL.webp',
            28: '/static/img/models/OPT.webp',
            29: '/static/img/models/OPT.webp', 
            30: '/static/img/models/OPT.webp', 
            31: '/static/img/models/OPT.webp', 
            32: '/static/img/models/OPT.webp', 
            33: '/static/img/models/OPT.webp',
            34: '/static/img/models/OPT.webp', 
            35: '/static/img/models/OPT.webp', 
            36: 'static/img/models/OPT.webp', 
            37: 'static/img/models/OPT.webp', 
            38: 'static/img/models/OPT.webp', 
            39: 'static/img/models/OPT.webp',
            40: '/static/img/models/davinci.webp', 
            41: '/static/img/models/davinci.webp'
        };
        
        const summaryElement = document.createElement('div');
        summaryElement.className = 'chunk-summary';
        
        const textToIndex = {
            '13B': 0, '30B': 1, '65B': 2, '7B': 3, 'GLM130B': 4, 'bloom_7b': 5,
            'bloomz': 6, 'cohere': 7, 'davinci': 8, 'dolly': 9, 'dolly-v2-12b': 10,
            'flan_t5_base': 11, 'flan_t5_large': 12, 'flan_t5_small': 13,
            'flan_t5_xl': 14, 'flan_t5_xxl': 15, 'gemma-7b-it': 16, 'gemma2-9b-it': 17,
            'gpt-3.5-turbo': 18, 'gpt-35': 19, 'gpt4': 20, 'gpt4o': 21,
            'gpt_j': 22, 'gpt_neox': 23, 'human': 24, 'llama3-70b': 25, 'llama3-8b': 26,
            'mixtral-8x7b': 27, 'opt_1.3b': 28, 'opt_125m': 29, 'opt_13b': 30,
            'opt_2.7b': 31, 'opt_30b': 32, 'opt_350m': 33, 'opt_6.7b': 34,
            'opt_iml_30b': 35, 'opt_iml_max_1.3b': 36, 't0_11b': 37, 't0_3b': 38,
            'text-davinci-002': 39, 'text-davinci-003': 40
        };

        let pillHTML = '';
        if (statistics.global_model !== null && statistics.global_model !== undefined) {
            let modelIndex = statistics.global_model;
            
            if (typeof statistics.global_model === 'string') {
                modelIndex = textToIndex[statistics.global_model];
            }
            
            if (modelIndex !== undefined && modelTexts[modelIndex]) {
                const modelText = modelTexts[modelIndex];
                const modelImage = modelImages[modelIndex];
                
                pillHTML = `
                    <div style="display: inline-flex; align-items: center; background-color: #e5e7eb; border-radius: 25px; padding: 8px 16px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); margin-left: 10px;">
                        <div style="width: 30px; height: 30px; background-color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); font-size: 18px;">
                            <img src="${modelImage}" height="25px">
                        </div>
                        <span style="color: #374151; font-weight: 500; font-size: 15px;">
                            ${modelText}
                        </span>
                    </div>
                `;
            }
        }
        
        summaryElement.innerHTML = `

            <div class="aixrow">
                <div class="aixcol-8">
                    <div class="summary-header">
                        <i class="fas fa-info-circle"></i>
                        <span>Summary of the analysis</span>
                    </div>
                   The predominant model detected is :
                </div>
                <div class="aixcol-4">
                    <p style="font-size:29px; display: flex; align-items: center;">
                          ${pillHTML}
                    </p>
                </div>
            </div>
        `;
        
        this.elements.analysisResults.insertBefore(summaryElement, this.elements.analysisResults.firstChild);
    }

    displayResults(data) {
        if (!data?.results || !data?.statistics) {
            this.displayError('Invalid response data');
            return;
        }

        //console.log('Displaying results:', data);

        const { results, statistics } = data;
        
    // AGREGAR: Forzar visibilidad del área de resultados
    const resultsArea = document.getElementById('results-area');
    if (resultsArea) {
        resultsArea.classList.remove('hidden');
        resultsArea.classList.add('show');
        resultsArea.style.display = 'block'; // Forzar display block
    }
    
    // AGREGAR: Ajustar layout de columnas inmediatamente
    const sideCol = document.getElementById('side-col');
    const mainCol = document.getElementById('main-col');
    
    if (sideCol) {
        sideCol.style.display = 'block';
        sideCol.classList.remove('col-0');
        sideCol.classList.add('col-5');
    }
    
    if (mainCol) {
        mainCol.classList.remove('col-12');
        mainCol.classList.add('col-7');
    }


        // Clear previous results efficiently
        if (this.elements.analysisResults) {
            this.elements.analysisResults.innerHTML = '';
        }

        this.showChunkSummary(statistics);
        
        // Update score visualization
        this.updateScoreVisualization(statistics);

        // Create analysis blocks with batch DOM updates
        this.createAnalysisBlocks(results);

        // *** VERIFICAR QUE ESTA LÍNEA ESTÉ PRESENTE ***
        setTimeout(() => this.highlightTextInOverlay(results), 100);

        // AGREGAR: Forzar actualización del layout después de mostrar resultados
        setTimeout(() => {
            if (typeof adjustLayout === 'function') {
                adjustLayout();
            }
        }, 200);

        // Smooth scroll to results
        setTimeout(() => {
            this.elements.resultsArea?.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }, 300);
    }

    updateScoreVisualization(statistics) {
        const aiPerc = statistics.ai_percentage || 0;
        const humanPerc = statistics.human_percentage || 0;
        const avgAiProb = statistics.average_ai_probability || 0;

        // Animate score circle
        if (this.elements.scoreCircle) {
            this.elements.scoreCircle.style.setProperty('--percentage', `${aiPerc}%`);
        }

        // Animate score value
        if (this.elements.scoreValue) {
            this.animateNumber(this.elements.scoreValue, 0, aiPerc, '%');
        }

        // Update percentages
        if (this.elements.humanPercentage) this.elements.humanPercentage.textContent = `${humanPerc}%`;
        if (this.elements.aiPercentage) this.elements.aiPercentage.textContent = `${aiPerc}%`;



        // Animate bars with setTimeout for mobile compatibility
        setTimeout(() => {
            if (this.elements.humanBar) this.elements.humanBar.style.width = `${humanPerc}%`;
            if (this.elements.aiBar) this.elements.aiBar.style.width = `${aiPerc}%`;
        }, 300);

        // Update score message
        this.updateScoreMessage(aiPerc, avgAiProb);
    }

    // Métodos corregidos para integrar en tu clase AIDetectorApp
// Reemplaza estos métodos en tu clase existente

// ===== HIGHLIGHT SYSTEM METHODS - Integrados en AIDetectorApp =====

createTextHighlightOverlay() {
    if (!this.elements.textarea) {
        console.log('Textarea no encontrado');
        return;
    }
    
    const container = this.elements.textarea.parentNode;
    
    // Asegurar que el contenedor tenga position relative
    if (getComputedStyle(container).position === 'static') {
        container.style.position = 'relative';
    }

    // Crear overlay
    const overlay = document.createElement('div');
    overlay.id = 'text-highlight-overlay';
    overlay.className = 'text-highlight-overlay';
    
    // Insertar el overlay ANTES del textarea para que esté detrás
    container.insertBefore(overlay, this.elements.textarea);
    
    // Hacer que el textarea sea transparente en el fondo pero mantenga el texto visible
    this.elements.textarea.style.backgroundColor = 'transparent';
    this.elements.textarea.style.position = 'relative';
    this.elements.textarea.style.zIndex = '2';
    
    // Cachear el overlay
    this.elements.textOverlay = overlay;
    
    // Aplicar estilos y configurar eventos
    this.syncOverlayStyles();
    this.setupOverlaySync();
    
    console.log('✅ Overlay creado y configurado correctamente');
}

syncOverlayStyles() {
    if (!this.elements.textOverlay || !this.elements.textarea) return;

    const textarea = this.elements.textarea;
    const overlay = this.elements.textOverlay;
    const textareaStyle = getComputedStyle(textarea);

    // Calcular posición exacta
    const top = textarea.offsetTop;
    const left = textarea.offsetLeft;

    // Aplicar estilos exactos
    overlay.style.cssText = `
        position: absolute;
        top: ${top}px;
        left: ${left}px;
        width: ${textarea.offsetWidth}px;
        height: ${textarea.offsetHeight}px;
        padding: ${textareaStyle.padding};
        margin: 0;
        border: ${textareaStyle.borderWidth} solid transparent;
        font-family: ${textareaStyle.fontFamily};
        font-size: ${textareaStyle.fontSize};
        font-weight: ${textareaStyle.fontWeight};
        line-height: ${textareaStyle.lineHeight};
        letter-spacing: ${textareaStyle.letterSpacing};
        word-spacing: ${textareaStyle.wordSpacing};
        text-align: ${textareaStyle.textAlign};
        text-indent: ${textareaStyle.textIndent};
        box-sizing: ${textareaStyle.boxSizing};
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow: hidden;
        pointer-events: none;
        z-index: 1;
        background: ${textareaStyle.backgroundColor};
        color: transparent;
        resize: none;
        outline: none;
    `;

    console.log('Estilos del overlay sincronizados');
}

setupOverlaySync() {
    if (!this.elements.textarea || !this.elements.textOverlay) return;

    const syncFunction = () => {
        this.syncOverlayPosition();
        this.syncOverlayScroll();
    };

    // Sincronización de scroll
    this.elements.textarea.addEventListener('scroll', () => {
        this.syncOverlayScroll();
    });

    // Sincronización en input (cuando cambia el tamaño del textarea)
    this.elements.textarea.addEventListener('input', () => {
        setTimeout(() => this.syncOverlayStyles(), 10);
    });

    // Sincronización en resize de ventana
    window.addEventListener('resize', this.debounce(() => {
        this.syncOverlayStyles();
    }, 100));

    // Observador de resize si está disponible
    if (window.ResizeObserver) {
        this.resizeObserver = new ResizeObserver(() => {
            this.syncOverlayStyles();
        });
        this.resizeObserver.observe(this.elements.textarea);
    }

    // Sincronización inicial
    setTimeout(syncFunction, 100);
    
    console.log('Event listeners de overlay configurados');
}

syncOverlayPosition() {
    if (!this.elements.textOverlay || !this.elements.textarea) return;
    
    const textarea = this.elements.textarea;
    const overlay = this.elements.textOverlay;
    
    overlay.style.top = textarea.offsetTop + 'px';
    overlay.style.left = textarea.offsetLeft + 'px';
    overlay.style.width = textarea.offsetWidth + 'px';
    overlay.style.height = textarea.offsetHeight + 'px';
}

syncOverlayScroll() {
    if (!this.elements.textOverlay || !this.elements.textarea) return;
    
    const textarea = this.elements.textarea;
    const overlay = this.elements.textOverlay;
    
    overlay.scrollTop = textarea.scrollTop;
    overlay.scrollLeft = textarea.scrollLeft;
}

highlightTextInOverlay_original(results) {
    console.log('=== INICIANDO SISTEMA DE HIGHLIGHT INTEGRADO ===');
    console.log('Resultados recibidos:', results?.length || 0);
    
    if (!this.elements.textOverlay || !this.elements.textarea || !results || !Array.isArray(results)) {
        console.log('Elementos no disponibles para highlighting');
        return;
    }
    
    const textareaValue = this.elements.textarea.value;
    
    if (!textareaValue.trim()) {
        console.log('Textarea vacío, limpiando overlay');
        this.elements.textOverlay.innerHTML = '';
        return;
    }
    
    // Procesar highlights
    const highlights = this.processHighlights(results, textareaValue);
    
    // Aplicar highlights al overlay
    this.applyHighlightsToOverlay(textareaValue, highlights);
}

highlightTextInOverlay_(results) {
    console.log('=== INICIANDO SISTEMA DE HIGHLIGHT INTEGRADO ===');
    console.log('Resultados recibidos:', results?.length || 0);
    
    if (!this.elements.textOverlay || !this.elements.textarea) {
        console.log('Elementos no disponibles para highlighting');
        return;
    }
    
    const textareaValue = this.elements.textarea.value;
    
    //  CAMBIO 1: Limpiar overlay si no hay texto O no hay resultados
    if (!textareaValue.trim() || !results || !Array.isArray(results) || results.length === 0) {
        console.log('Limpiando overlay - sin texto o sin resultados');
        this.elements.textOverlay.innerHTML = '';
        this.elements.textOverlay.style.display = 'none'; // Ocultar completamente
        return;
    }
    
    // Mostrar overlay cuando hay contenido
    this.elements.textOverlay.style.display = 'block';
    // Procesar highlights
    const highlights = this.processHighlights(results, textareaValue);
    
    // Aplicar highlights al overlay
    this.applyHighlightsToOverlay(textareaValue, highlights);
}

highlightTextInOverlay(results) {
    console.log('=== INICIANDO SISTEMA DE HIGHLIGHT INTEGRADO ===');
    console.log('Resultados recibidos:', results?.length || 0);
    
    if (!this.elements.textOverlay || !this.elements.textarea) {
        console.log('Elementos no disponibles para highlighting');
        return;
    }
    
    const textareaValue = this.elements.textarea.value;
    
    //  VALIDACIÓN MEJORADA: Limpiar si no hay texto o resultados
    if (!textareaValue || textareaValue.trim() === '') {
        console.log('🧹 Textarea vacío - limpiando overlay completamente');
        this.elements.textOverlay.innerHTML = '';
        this.elements.textOverlay.style.display = 'none';
        return;
    }
    
    if (!results || !Array.isArray(results) || results.length === 0) {
        console.log('⚠️ Sin resultados - mostrando texto sin highlights');
        this.elements.textOverlay.innerHTML = this.escapeHtml(textareaValue)
            .replace(/\n/g, '<br>');
        this.elements.textOverlay.style.display = 'block';
        return;
    }
    
    // Mostrar overlay cuando hay contenido
    this.elements.textOverlay.style.display = 'block';
    
    //  NUEVO ENFOQUE: Procesar TODO el texto del textarea
    this.processAndApplyHighlights(results, textareaValue);
}

processAndApplyHighlights(results, textareaValue) {
    console.log(' Procesando highlights con cobertura completa');
    
    // Crear mapa de caracteres con su tipo (AI/Human/Neutral)
    const charMap = new Array(textareaValue.length).fill(null);
    
    results.forEach((result, index) => {
        if (!result?.text || !result.text.trim()) {
            console.log(`Resultado ${index} sin texto válido, saltando`);
            return;
        }
        
        const searchText = result.text.trim();
        const color = this.getHighlightColor(result.is_human);
        
        console.log(`🔍 Buscando: "${searchText.substring(0, 50)}..."`);
        
        // Buscar todas las coincidencias (no solo la primera)
        let startIndex = 0;
        while (startIndex < textareaValue.length) {
            const foundIndex = textareaValue.indexOf(searchText, startIndex);
            
            if (foundIndex === -1) break;
            
            // Marcar caracteres como procesados
            for (let i = foundIndex; i < foundIndex + searchText.length; i++) {
                if (i < charMap.length) {
                    charMap[i] = {
                        color: color,
                        confidence: result.confidence || 0,
                        type: result.is_human ? 'human' : 'ai'
                    };
                }
            }
            
            console.log(` Coincidencia encontrada en posición ${foundIndex}`);
            startIndex = foundIndex + searchText.length;
        }
    });
    
    // Contar cobertura
    const coveredChars = charMap.filter(c => c !== null).length;
    const coverage = (coveredChars / textareaValue.length * 100).toFixed(1);
    console.log(` Cobertura: ${coverage}% (${coveredChars}/${textareaValue.length} caracteres)`);
    
    //  Renderizar con cobertura completa
    this.renderFullCoverageHighlights(textareaValue, charMap);
}

//  NUEVO MÉTODO: Renderizar con cobertura total
renderFullCoverageHighlights(text, charMap) {
    let html = '';
    let i = 0;
    
    while (i < text.length) {
        const char = text[i];
        const highlightData = charMap[i];
        
        if (highlightData) {
            // Carácter con highlight - buscar segmento continuo del mismo tipo
            let segmentEnd = i;
            while (
                segmentEnd < text.length && 
                charMap[segmentEnd] !== null &&
                charMap[segmentEnd].color === highlightData.color
            ) {
                segmentEnd++;
            }
            
            const segment = text.substring(i, segmentEnd);
            html += `<span class="text-highlight" style="background-color: ${highlightData.color}44; border-bottom: 2px solid ${highlightData.color};">${this.escapeHtml(segment)}</span>`;
            
            i = segmentEnd;
        } else {
            // Carácter sin highlight - mostrar sin formato
            html += this.escapeHtml(char);
            i++;
        }
    }
    
    this.elements.textOverlay.innerHTML = html;
    
    // Sincronizar scroll
    setTimeout(() => {
        this.syncOverlayScroll();
    }, 10);
    
    console.log('Highlights renderizados con cobertura completa');
}

processHighlights(results, textareaValue) {
    const highlights = [];
    
    results.forEach((result, index) => {
        console.log(`\n--- Procesando resultado ${index} ---`);
        
        if (!result?.text || !result.text.trim()) {
            console.log('Resultado sin texto válido, saltando');
            return;
        }
        
        const searchText = result.text.trim();
        const color = this.getHighlightColor(result.is_human);
        
        console.log('Texto a buscar:', searchText.substring(0, 50) + '...');
        console.log('Color asignado:', color);
        
        // Búsqueda exacta primero
        const exactMatch = this.findExactMatch(textareaValue, searchText);
        if (exactMatch) {
            highlights.push({
                start: exactMatch.start,
                end: exactMatch.end,
                color: color,
                type: 'exact',
                confidence: result.confidence || 0
            });
            console.log(`✅ Coincidencia exacta en posición ${exactMatch.start}`);
            return;
        }
        
        // Búsqueda por oraciones si no hay coincidencia exacta
        const sentenceMatches = this.findSentenceMatches(textareaValue, searchText, color);
        highlights.push(...sentenceMatches);
    });
    
    console.log(`Total highlights procesados: ${highlights.length}`);
    return highlights;
}

getHighlightColor(isHuman) {
    if (isHuman === true) {
        return '#22c55e'; // Verde para humano
    } else if (isHuman === false) {
        return '#ef4444'; // Rojo para AI
    } else {
        return '#6b7280'; // Gris para incierto
    }
}

findExactMatch(text, searchText) {
    const index = text.indexOf(searchText);
    return index !== -1 ? { start: index, end: index + searchText.length } : null;
}

findSentenceMatches(textareaValue, searchText, color) {
    const matches = [];
    
    // Dividir en oraciones
    const sentences = searchText
        .split(/[.!?]+/)
        .map(s => s.trim())
        .filter(s => s.length > 10); // Solo oraciones significativas
    
    console.log(`Buscando ${sentences.length} oraciones`);
    
    sentences.forEach((sentence, sIndex) => {
        const index = textareaValue.indexOf(sentence);
        
        if (index !== -1) {
            matches.push({
                start: index,
                end: index + sentence.length,
                color: color,
                type: 'sentence'
            });
            console.log(`✅ Oración ${sIndex} encontrada en posición ${index}`);
        } else {
            console.log(`❌ Oración ${sIndex} no encontrada: "${sentence.substring(0, 30)}..."`);
        }
    });
    
    return matches;
}

applyHighlightsToOverlay(originalText, highlights) {
    console.log('Aplicando highlights al overlay...');
    
    // ✅ CAMBIO 2: Si no hay highlights, mostrar texto completo sin formato
    if (highlights.length === 0) {
        console.log('Sin highlights, mostrando texto normal completo');
        // Mostrar TODO el texto del textarea sin highlights
        this.elements.textOverlay.innerHTML = this.escapeHtml(originalText)
            .replace(/\n/g, '<br>'); // Respetar saltos de línea
        return;
    }

    // Resolver overlaps
    const resolvedHighlights = this.resolveHighlightOverlaps(highlights);
    console.log(`Highlights después de resolver overlaps: ${resolvedHighlights.length}`);
    
    // Ordenar por posición (de atrás hacia adelante para no alterar índices)
    resolvedHighlights.sort((a, b) => b.start - a.start);
    
    // ✅ CAMBIO 3: NUEVO - Crear cobertura completa del texto
    let coveredRanges = new Set();
    resolvedHighlights.forEach(h => {
        for (let i = h.start; i < h.end; i++) {
            coveredRanges.add(i);
        }
    });

    // Verificar si hay texto sin cubrir
    const totalChars = originalText.length;
    const coveredChars = coveredRanges.size;
    const coverage = (coveredChars / totalChars * 100).toFixed(1);
    console.log(`📊 Cobertura de texto: ${coverage}% (${coveredChars}/${totalChars} caracteres)`);

    // Si la cobertura es menor al 80%, agregar el texto restante sin highlight
    if (coverage < 80) {
        console.log('⚠️ Cobertura baja, mostrando todo el texto');
    }

    let result = originalText;
    
    // Aplicar cada highlight
    resolvedHighlights.forEach((highlight, index) => {
        const before = result.substring(0, highlight.start);
        const text = result.substring(highlight.start, highlight.end);
        const after = result.substring(highlight.end);
        
        const highlightSpan = `<span class="text-highlight" style="background-color: ${highlight.color}44; border-bottom: 2px solid ${highlight.color}; display: inline; position: relative;">${this.escapeHtml(text)}</span>`;
        
        result = before + highlightSpan + after;
        console.log(`✅ Aplicado highlight ${index}: ${highlight.type}`);
    });
    
    // Aplicar al overlay
    this.elements.textOverlay.innerHTML = result;
    
    // Forzar sincronización inmediata
    setTimeout(() => {
        this.syncOverlayScroll();
    }, 10);
    
    console.log('🎉 Highlights aplicados correctamente al overlay');
}

resolveHighlightOverlaps(highlights) {
    if (highlights.length <= 1) return highlights;
    
    // Ordenar por posición de inicio
    highlights.sort((a, b) => a.start - b.start);
    
    const resolved = [];
    let current = { ...highlights[0] };
    
    for (let i = 1; i < highlights.length; i++) {
        const next = highlights[i];
        
        if (next.start <= current.end) {
            // Hay overlap, fusionar
            current.end = Math.max(current.end, next.end);
            // Mantener el color del highlight más confiable
            if ((next.confidence || 0) > (current.confidence || 0)) {
                current.color = next.color;
            }
        } else {
            // No hay overlap, agregar el actual y continuar
            resolved.push(current);
            current = { ...next };
        }
    }
    
    // Agregar el último
    resolved.push(current);
    
    console.log(`Overlaps resueltos: ${highlights.length} -> ${resolved.length}`);
    return resolved;
}

// Método para limpiar highlights (agregar a tu clase)
clearTextHighlights_() {
    if (this.elements.textOverlay) {
        const textareaValue = this.elements.textarea?.value || '';
        
        if (textareaValue.trim()) {
            // Si hay texto, mostrar sin highlights
            this.elements.textOverlay.innerHTML = this.escapeHtml(textareaValue)
                .replace(/\n/g, '<br>');
            this.elements.textOverlay.style.display = 'block';
        } else {
            // Si no hay texto, ocultar completamente el overlay
            this.elements.textOverlay.innerHTML = '';
            this.elements.textOverlay.style.display = 'none';
        }
        
        console.log(' Highlights limpiados correctamente');
    }
}

clearTextHighlights() {
    console.log(' Limpiando highlights...');
    
    if (!this.elements.textOverlay) {
        console.log(' No hay overlay para limpiar');
        return;
    }
    
    const textareaValue = this.elements.textarea?.value || '';
    
    if (textareaValue.trim()) {
        // Si hay texto, mostrar sin highlights
        console.log(' Mostrando texto sin highlights');
        this.elements.textOverlay.innerHTML = this.escapeHtml(textareaValue)
            .replace(/\n/g, '<br>');
        this.elements.textOverlay.style.display = 'block';
    } else {
        // Si no hay texto, ocultar completamente
        console.log(' Textarea vacío - ocultando overlay');
        this.elements.textOverlay.innerHTML = '';
        this.elements.textOverlay.style.display = 'none';
    }
}

// CSS requerido - agregar este estilo a tu documento
addHighlightStyles() {
    const styleId = 'highlight-system-styles';
    
    // Evitar duplicar estilos
    if (document.getElementById(styleId)) return;
    
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
        .text-highlight-overlay {
            font-family: inherit !important;
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }

        .text-highlight {
            transition: background-color 0.2s ease;
            display: inline;
        }

        .text-highlight:hover {
            filter: brightness(1.1);
        }

        /* Asegurar que el textarea mantenga su funcionalidad */
        .main-textarea {
            background: rgba(255, 255, 255, 0.9) !important;
            position: relative !important;
            z-index: 2 !important;
        }

        [data-theme="dark"] .main-textarea {
            background: rgba(31, 41, 55, 0.9) !important;
        }

        /* Mejorar contraste en modo oscuro */
        [data-theme="dark"] .text-highlight {
            background-color: rgba(255, 255, 255, 0.1) !important;
        }
    `;
    
    document.head.appendChild(style);
    console.log('Estilos de highlighting agregados');
}

    updateScoreMessage(aiPercentage, avgProbability) {
        if (!this.elements.scoreMessage) return;

        const messages = [
            { threshold: 75, text: "Your text shows strong indicators of AI generation. Multiple linguistic patterns typical of AI systems were detected." },
            { threshold: 50, text: "Your text contains a mix of human and AI-generated characteristics. Some sections show algorithmic patterns while others appear more natural." },
            { threshold: 25, text: "Your text appears mostly human-written, though some elements might have been AI-assisted or automatically processed." },
            { threshold: 0, text: "Your text demonstrates natural human writing patterns. No significant AI generation indicators were found." }
        ];
        
        const message = messages.find(m => aiPercentage >= m.threshold);
        
        this.elements.scoreMessage.textContent = message.text;
        this.elements.scoreMessage.classList.add('fade-in');
    }

    createAnalysisBlocks(results) {
        if (!this.elements.analysisResults || !results) return;

        // Create document fragment for efficient DOM manipulation
        const fragment = document.createDocumentFragment();

        results.forEach((result, index) => {
            const blockElement = this.createAnalysisBlock(result, index);
            if (blockElement) {
                fragment.appendChild(blockElement);
            }
        });

        // Single DOM update
        this.elements.analysisResults.appendChild(fragment);
    }

    createAnalysisBlock(result, index) {
        if (!result) return null;

        const blockElement = document.createElement('div');
        blockElement.className = `analysis-block analysis-block-${index}`;
        blockElement.style.animationDelay = `${index * 0.1}s`;
        blockElement.setAttribute('role', 'listitem');

        const isHuman = result.is_human;
        const confidence = result.confidence || 0;
        const aiModel = result.ai_model;
        const text = result.text || 'No text available';

        const config = this.getBlockConfig(isHuman);
        
        blockElement.classList.add(config.blockClass);
        blockElement.innerHTML = this.getBlockHTML(config, confidence, text, aiModel);

        // Animate confidence bar with setTimeout for mobile compatibility
        setTimeout(() => {
            const confidenceFill = blockElement.querySelector('.confidence-fill');
            if (confidenceFill) {
                confidenceFill.style.width = `${confidence}%`;
            }
        }, 300 + (index * 100));

        blockElement.classList.add('slide-up');
        return blockElement;
    }

    getBlockConfig(isHuman) {
        if (isHuman === true) {
            return {
                blockClass: 'block-human',
                iconClass: 'fas fa-user',
                typeName: 'Human Written',
                confidenceColor: 'var(--human-color)'
            };
        } else if (isHuman === false) {
            return {
                blockClass: 'block-ai',
                iconClass: 'fas fa-robot',
                typeName: 'AI Generated',
                confidenceColor: 'var(--ai-color)'
            };
        } else {
            return {
                blockClass: 'block-neutral',
                iconClass: 'fas fa-question',
                typeName: 'Uncertain',
                confidenceColor: 'var(--neutral-color)'
            };
        }
    }

    getBlockHTML(config, confidence, text, aiModel) {
        const modelInfo = aiModel ? 
            `<div class="model-tag"><i class="fas fa-tag"></i> ${this.escapeHtml(aiModel)}</div>` : '';

        return `
            <div class="block-header">
                <div class="block-info">
                    <div class="block-icon" style="color: ${config.confidenceColor}">
                        <i class="${config.iconClass}"></i>
                    </div>
                    <div class="block-details">
                        <div class="block-type">${config.typeName}</div>
                        <div class="block-confidence">Confidence: ${confidence.toFixed(1)}%</div>
                    </div>
                </div>
                <div class="confidence-meter">
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: 0%; background: ${config.confidenceColor}"></div>
                    </div>
                </div>
            </div>
            <div class="block-content">
                <p>${this.escapeHtml(text)}</p>
            </div>
        `;
    }

    showLoadingState() {
        this.elements.scannerAnimation?.classList.add('active');
        setTimeout(() => {
            this.elements.loadingOverlay?.classList.add('active');
        }, 200);
        
        // Reset loading text
        const loadingText = document.querySelector('.loading-text');
        if (loadingText) {
            loadingText.textContent = 'Analyzing content...';
        }
    }

    hideLoadingState() {
        this.elements.scannerAnimation?.classList.remove('active');
        this.elements.loadingOverlay?.classList.remove('active');
    }

    displayError(message) {
        //console.error('Display error:', message);
        
        this.elements.resultsArea?.classList.remove('hidden');
        this.elements.resultsArea?.classList.add('show');

        if (this.elements.analysisResults) {
            this.elements.analysisResults.innerHTML = `
                <div class="error-message fade-in" role="alert">
                    <div class="error-icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="error-content">
                        <h4>Analysis Error</h4>
                        <p>${this.escapeHtml(message)}</p>
                        <button class="retry-btn" onclick="location.reload()">
                            <i class="fas fa-redo"></i> Retry
                        </button>
                    </div>
                </div>
            `;
        }

        this.showNotification('Analysis failed. Please try again.', 'error');
    }

    // ===== USAGE MANAGEMENT =====
    checkUsageLimit() {
        //if (this.state.currentUses >= this.config.maxFreeUses4) {
        //    this.showUsageLimitModal();
        //    return false;
        //}
        return true;
    }

    incrementUsageCounter() {
        this.state.currentUses++;
        this.setSafeStorageValue('aiDetectorUses', this.state.currentUses);
        this.updateUsageDisplay();

        if (this.state.currentUses >= this.config.maxFreeUses4) {
            setTimeout(() => this.showUsageLimitModal(), 2000);
        }
    }

    updateUsageDisplay() {
        if (!this.elements.usageCounter) return;
        
        const remaining = this.config.maxFreeUses4 - this.state.currentUses;
        
        if (remaining <= 0) {
            this.elements.usageCounter.textContent = 'Limit reached';
            this.elements.usageCounter.style.background = 'var(--ai-color-light)';
            this.elements.usageCounter.style.color = 'var(--ai-color)';
        } else {
            this.elements.usageCounter.textContent = `${remaining} analyses remaining`;
        }
    }

    showUsageLimitModal() {
        //this.showNotification('You have reached the limit of free analyses. Upgrade to continue.', 'warning');
    }

    // ===== EVENT LISTENERS =====
    initEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));

        // Error handling
        window.addEventListener('error', this.handleGlobalError.bind(this));
        window.addEventListener('unhandledrejection', this.handleUnhandledRejection.bind(this));
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Enter to analyze
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            const text = this.elements.textarea?.value?.trim();
            if (text && !this.state.isAnalyzing) {
                this.analyzeText(text);
            }
        }
        
        // Escape to close menus
        if (e.key === 'Escape') {
            this.elements.accessibilityMenu?.classList.remove('show');
            this.closeMobileMenu();
        }
    }

    handleGlobalError(e) {
        //console.error('Global error:', e.error);
        this.showNotification('An unexpected error occurred. Please refresh the page.', 'error');
    }

    handleUnhandledRejection(e) {
        //console.error('Unhandled promise rejection:', e.reason);
        this.showNotification('A network error occurred. Please check your connection.', 'error');
    }

    // ===== UTILITY METHODS =====
    animateNumber(element, start, end, suffix = '') {
        if (!element) return;

        const duration = 1500;
        const startTime = Date.now();
        
        const updateNumber = () => {
            const currentTime = Date.now();
            const elapsedTime = currentTime - startTime;
            
            if (elapsedTime < duration) {
                const progress = this.easeOutQuart(elapsedTime / duration);
                const currentValue = Math.round(start + (end - start) * progress);
                element.textContent = `${currentValue}${suffix}`;
                
                // Use setTimeout instead of requestAnimationFrame for better mobile compatibility
                setTimeout(updateNumber, 16);
            } else {
                element.textContent = `${end}${suffix}`;
            }
        };
        
        updateNumber();
    }

    easeOutQuart(t) {
        return 1 - Math.pow(1 - t, 4);
    }

    hashText(text) {
        let hash = 0;
        for (let i = 0; i < text.length; i++) {
            const char = text.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return hash;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'polite');
        
        const config = {
            success: { color: '#22c55e', icon: 'fas fa-check-circle' },
            warning: { color: '#f59e0b', icon: 'fas fa-exclamation-triangle' },
            error: { color: '#ef4444', icon: 'fas fa-times-circle' },
            info: { color: '#3b82f6', icon: 'fas fa-info-circle' }
        };
        
        const { color, icon } = config[type];
        
        notification.style.cssText = `
            position: fixed; top: 2rem; right: 2rem; background: ${color};
            color: white; padding: 1rem 1.5rem; border-radius: 0.75rem;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1); z-index: 3000;
            font-weight: 500; animation: slideInRight 0.3s ease;
            max-width: 350px; word-wrap: break-word; display: flex;
            align-items: center; gap: 0.75rem;
        `;
        
        notification.innerHTML = `
            <i class="${icon}" aria-hidden="true"></i>
            <span>${this.escapeHtml(message)}</span>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove notification
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.style.animation = 'slideOutRight 0.3s ease forwards';
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        document.body.removeChild(notification);
                    }
                }, 300);
            }
        }, 4000);
    }

    // ===== PERIODIC TASKS =====
    startPeriodicTasks() {
        // Cache cleanup every 5 minutes
        setInterval(() => this.cleanupCache(), 5 * 60 * 1000);
    }

    cleanupCache() {
        const now = Date.now();
        this.cache.forEach((value, key) => {
            if (now - (value.timestamp || 0) > this.config.cacheMaxAge) {
                this.cache.delete(key);
            }
        });
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Add required CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .reduce-motion * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    `;
    document.head.appendChild(style);

    // Initialize the application
    window.aiDetector = new AIDetectorApp();
    
    // Service worker registration for progressive web app
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/service-worker.js')
                .then(registration => console.log('SW registered:', registration))
                .catch(error => console.log('SW registration failed:', error));
        });
    }
});