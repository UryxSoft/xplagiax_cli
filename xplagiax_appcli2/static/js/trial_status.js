class TrialStatusValidator {
    constructor() {
        this.progressBar  = document.getElementById('progressBar');
        this.trialText    = document.getElementById('trialText');
        this.unlockButton = document.getElementById('unlockButton');
        this.trialIcon    = document.getElementById('trialIcon');
        this.trialMessage = document.getElementById('trialMessage');

        // Bail out silently if the trial-status widget is not present on this page.
        if (!this.progressBar || !this.trialText) return;

        this.init();
    }
    
    async init() {
        await this.loadTrialStatus();
        this.startCountdown();
        this.setupUnlockButton();
    }
    
    async loadTrialStatus() {
        try {
            const response = await fetch('/auth_bp/check-trial-status');
            const data = await response.json();
            
            if (data.trial_expired) {
                this.showExpiredTrial();
                return;
            }
            
            if (data.is_on_trial && data.trial_ends_at) {
                this.trialEndsAt = new Date(data.trial_ends_at);
                // ✅ OBTENER DÍAS TOTALES DEL SERVIDOR
                this.totalTrialDays = data.total_trial_days || 5; // Default 5 días
                this.updateTrialDisplay();
            } else {
                this.showNoTrialStatus();
            }
        } catch (error) {
            console.error('Error loading trial status:', error);
            this.showErrorStatus();
        }
    }
    
    updateTrialDisplay() {
        const now = new Date();
        const timeLeft = this.trialEndsAt - now;
        
        if (timeLeft <= 0) {
            this.showExpiredTrial();
            return;
        }
        
        // ✅ CORRECCIÓN: Usar el mismo cálculo que MySQL DATEDIFF()
        // Contar días desde el inicio hasta el final, incluyendo el día actual
        const nowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const endDate = new Date(this.trialEndsAt.getFullYear(), this.trialEndsAt.getMonth(), this.trialEndsAt.getDate());
        const daysLeft = Math.ceil((endDate - nowDate) / (1000 * 60 * 60 * 24));
        
        const hoursLeft = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutesLeft = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        
        // ✅ CORRECCIÓN: Usar días totales dinámicos basados en los datos del servidor
        const totalTrialDays = this.totalTrialDays || 5; // Default 5 días
        const percentage = Math.max(5, (daysLeft / totalTrialDays) * 100);
        
        // Actualizar texto
        let displayText;
        if (daysLeft > 0) {
            displayText = `${daysLeft} day${daysLeft !== 1 ? 's' : ''} left`;
        } else if (hoursLeft > 0) {
            displayText = `${hoursLeft} hour${hoursLeft !== 1 ? 's' : ''} left`;
        } else {
            displayText = `${minutesLeft} minute${minutesLeft !== 1 ? 's' : ''} left`;
        }
        
        if (this.trialText)    this.trialText.textContent = displayText;
        if (this.progressBar)  this.progressBar.style.width = `${Math.max(5, percentage)}%`;
        
        // Cambiar colores según tiempo restante
        this.updateProgressBarStyle(daysLeft, totalTrialDays);
        this.updateTrialIcon(daysLeft);
        this.showTrialMessage(daysLeft);
    }
    
    updateProgressBarStyle(daysLeft, totalDays = 5) {
        if (!this.progressBar) return;
        // Remover todas las clases anteriores
        this.progressBar.classList.remove(
            'progress-excellent', 'progress-good', 'progress-warning', 
            'progress-critical', 'progress-expired'
        );
        
        // Aplicar animación siempre excepto para expired
        if (daysLeft > 0) {
            this.progressBar.classList.add('settings-progress-bar-animated');
        } else {
            this.progressBar.classList.remove('settings-progress-bar-animated');
        }
        
        // ✅ CORRECCIÓN: Ajustar rangos para 5 días
        if (daysLeft >= 4) {           // Días 4-5: Verde
            this.progressBar.classList.add('progress-excellent');
        } else if (daysLeft >= 3) {    // Día 3: Azul  
            this.progressBar.classList.add('progress-good');
        } else if (daysLeft >= 2) {    // Día 2: Naranja
            this.progressBar.classList.add('progress-warning');
        } else if (daysLeft >= 1) {    // Día 1: Rojo
            this.progressBar.classList.add('progress-critical');
        } else {                       // Día 0: Expirado
            this.progressBar.classList.add('progress-expired');
        }
    }
    
    updateTrialIcon(daysLeft) {
        if (!this.trialIcon) return;
        this.trialIcon.classList.remove(
            'fa-hourglass-half', 'fa-hourglass-end', 'fa-exclamation-triangle', 
            'fa-times-circle', 'fa-clock', 'fa-bolt'
        );
        
        // Resetear color
        this.trialIcon.style.color = '';
        this.trialIcon.style.filter = '';
        this.trialIcon.style.animation = '';
        
        // ✅ CORRECCIÓN: Ajustar rangos para 5 días
        if (daysLeft >= 4) {           // Días 4-5: Verde - Reloj
            this.trialIcon.classList.add('fa-clock');
            this.trialIcon.style.color = '#00c851';
            this.trialIcon.style.filter = 'drop-shadow(0 0 8px rgba(0, 200, 81, 0.6))';
        } else if (daysLeft >= 3) {    // Día 3: Azul - Hourglass
            this.trialIcon.classList.add('fa-hourglass-half');
            this.trialIcon.style.color = '#2196f3';
            this.trialIcon.style.filter = 'drop-shadow(0 0 8px rgba(33, 150, 243, 0.6))';
        } else if (daysLeft >= 2) {    // Día 2: Naranja - Advertencia
            this.trialIcon.classList.add('fa-exclamation-triangle');
            this.trialIcon.style.color = '#ff9800';
            this.trialIcon.style.filter = 'drop-shadow(0 0 8px rgba(255, 152, 0, 0.6))';
            this.trialIcon.style.animation = 'pulse-warning 2s ease-in-out infinite';
        } else if (daysLeft >= 1) {    // Día 1: Rojo - Rayo crítico
            this.trialIcon.classList.add('fa-bolt');
            this.trialIcon.style.color = '#f44336';
            this.trialIcon.style.filter = 'drop-shadow(0 0 12px rgba(244, 67, 54, 0.8))';
            this.trialIcon.style.animation = 'pulse-critical 1s ease-in-out infinite';
        } else {                       // Día 0: Expirado
            this.trialIcon.classList.add('fa-times-circle');
            this.trialIcon.style.color = '#607d8b';
        }
    }
    
    showTrialMessage(daysLeft) {
        if (!this.trialMessage) return;
        this.trialMessage.style.display = 'block';
        
        if (daysLeft <= 0) {
            this.trialMessage.className = 'trial-expired-message';
            this.trialMessage.innerHTML = `
                <i class="fas fa-times-circle" style="color: #f44336; margin-right: 8px;"></i>
                <strong>Trial Expired!</strong> Your trial period has ended.
                Upgrade your plan to continue using all features.
            `;
        } else if (daysLeft === 1) {
            this.trialMessage.className = 'trial-expired-message';
            this.trialMessage.innerHTML = `
                <i class="fas fa-bolt" style="color: #f44336; margin-right: 8px; animation: pulse-critical 1s ease-in-out infinite;"></i>
                <strong>LAST DAY!</strong> Your trial expires in less than 24 hours.
                    Update now to avoid losing access!
            `;
        } else if (daysLeft <= 2) {
            this.trialMessage.className = 'trial-warning-message';
            this.trialMessage.innerHTML = `
                <i class="fas fa-exclamation-triangle" style="color: #ff9800; margin-right: 8px;"></i>
                <strong>Only left ${daysLeft} days!</strong> Your trial expires very soon.
                Consider upgrading your plan to avoid interrupting your work.
            `;
        } else if (daysLeft <= 4) {
            this.trialMessage.className = 'trial-warning-message';
            this.trialMessage.innerHTML = `
                <i class="fas fa-info-circle" style="color: #2196f3; margin-right: 8px;"></i>
                <strong>There are left ${daysLeft} trial days.</strong> 
                Explore all the features and consider upgrading your plan.
            `;
        } else {
            this.trialMessage.style.display = 'none';
        }
    }
    
    showExpiredTrial() {
        if (this.trialText)    this.trialText.textContent = 'Trial expired';
        if (this.progressBar) {
            this.progressBar.style.width = '100%';
            this.progressBar.classList.remove('progress-active', 'progress-warning', 'progress-danger');
            this.progressBar.classList.add('progress-expired');
        }
        if (this.trialIcon) {
            this.trialIcon.classList.remove('fa-hourglass-half');
            this.trialIcon.classList.add('fa-times-circle');
            this.trialIcon.style.color = '#e74c3c';
        }
        if (this.unlockButton) {
            this.unlockButton.disabled = false;
            this.unlockButton.innerHTML = '<i class="fas fa-crown"></i> Upgrade Now';
            this.unlockButton.style.background = 'linear-gradient(45deg, #e74c3c, #c0392b)';
        }
        if (this.trialMessage) {
            this.trialMessage.style.display = 'block';
            this.trialMessage.className = 'trial-expired-message';
            this.trialMessage.innerHTML = `
                <i class="fas fa-times-circle"></i>
                <strong>Trial expired!</strong> Your trial period has ended.
                Upgrade your plan now to continue using the service.
            `;
        }
    }
    
    showNoTrialStatus() {
        if (this.trialText)    this.trialText.textContent = 'No trial active';
        if (this.progressBar) {
            this.progressBar.style.width = '100%';
            this.progressBar.classList.add('progress-expired');
        }
        if (this.unlockButton) this.unlockButton.innerHTML = '<i class="fas fa-rocket"></i> Start Trial';
    }
    
    showErrorStatus() {
        if (this.trialText)    this.trialText.textContent = 'Error loading status';
        if (this.progressBar) {
            this.progressBar.style.width = '100%';
            this.progressBar.classList.add('progress-expired');
        }
    }
    
    startCountdown() {
        // Actualizar cada minuto
        setInterval(() => {
            if (this.trialEndsAt) {
                this.updateTrialDisplay();
            }
        }, 60000);
    }
    
    setupUnlockButton() {
        if (!this.unlockButton) return;
        this.unlockButton.addEventListener('click', () => {
            // Aquí puedes redirigir a la página de planes o abrir un modal
            this.handleUnlockClick();
        });
    }
    
    handleUnlockClick() {
        // Ejemplo de redirección o modal
        if (confirm('Do you want to see the available plans?')) {
            window.location.href = '/pricing'; // Cambia por tu URL de planes
        }
    }
}

// Inicializar cuando se carga la página
document.addEventListener('DOMContentLoaded', () => {
    new TrialStatusValidator();
});

// Funciones utilitarias para uso en otras partes de tu app
window.TrialUtils = {
    async checkTrialStatus() {
        try {
            const response = await fetch('/auth_bp/profile');
            const data = await response.json();
            return {
                isOnTrial: data.is_on_trial,
                trialEndsAt: data.trial_ends_at ? new Date(data.trial_ends_at) : null,
                isExpired: data.trial_ends_at ? new Date(data.trial_ends_at) < new Date() : false
            };
        } catch (error) {
            console.error('Error checking trial status:', error);
            return null;
        }
    },
    
    formatTimeRemaining(trialEndsAt) {
        const now = new Date();
        const timeLeft = new Date(trialEndsAt) - now;
        
        if (timeLeft <= 0) return 'Expired';
        
        const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        
        if (days > 0) return `${days} day${days !== 1 ? 's' : ''} left`;
        if (hours > 0) return `${hours} hour${hours !== 1 ? 's' : ''} left`;
        
        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        return `${minutes} minute${minutes !== 1 ? 's' : ''} left`;
    }
};