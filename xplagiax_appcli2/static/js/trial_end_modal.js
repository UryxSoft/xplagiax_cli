
// Initialize modal on page load
window.addEventListener('DOMContentLoaded', () => {
    showTrialModal();
});

class TrialStatusModal {
    constructor() {
        this.modal = document.getElementById('trialModal');
        this.progressBar = document.getElementById('modalProgressBar');
        this.progressText = document.getElementById('modalProgressText');
        this.timeRemaining = document.getElementById('modalTimeRemaining');
        this.modalTitle = document.getElementById('modalTitle');
        this.modalSubtitle = document.getElementById('modalSubtitle');
        this.modalIcon = document.getElementById('modalTrialIcon');
        this.messageBox = document.getElementById('modalMessageBox');
        this.upgradeBtn = document.getElementById('upgradeBtn');
        this.totalTrialDays = 5; // Default
    }

    async loadAndShow() {
        await this.loadTrialStatus();
        this.show();
    }

    async loadTrialStatus() {
        try {
            const response = await fetch('/auth_bp/check-trial-status');
            const data = await response.json();
            
            if (data.trial_expired) {
                this.showExpiredState();
                return;
            }
            
            if (data.is_on_trial && data.trial_ends_at) {
                this.trialEndsAt = new Date(data.trial_ends_at);
                this.totalTrialDays = data.total_trial_days || 5;
                this.updateDisplay();
            } else {
                this.showNoTrialState();
            }
        } catch (error) {
            console.error('Error loading trial status:', error);
            this.showErrorState();
        }
    }

    updateDisplay() {
        const now = new Date();
        const timeLeft = this.trialEndsAt - now;
        
        if (timeLeft <= 0) {
            this.showExpiredState();
            return;
        }
        
        const nowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const endDate = new Date(this.trialEndsAt.getFullYear(), this.trialEndsAt.getMonth(), this.trialEndsAt.getDate());
        const daysLeft = Math.ceil((endDate - nowDate) / (1000 * 60 * 60 * 24));
        
        const hoursLeft = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutesLeft = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        
        const percentage = Math.max(5, (daysLeft / this.totalTrialDays) * 100);
        
        // Update text
        let displayText;
        if (daysLeft > 0) {
            displayText = `${daysLeft} day${daysLeft !== 1 ? 's' : ''}`;
        } else if (hoursLeft > 0) {
            displayText = `${hoursLeft} hour${hoursLeft !== 1 ? 's' : ''}`;
        } else {
            displayText = `${minutesLeft} minute${minutesLeft !== 1 ? 's' : ''}`;
        }
        
        this.timeRemaining.textContent = displayText;
        this.progressText.textContent = `${Math.round(percentage)}%`;
        this.progressBar.style.width = `${Math.max(5, percentage)}%`;
        
        this.updateProgressBarStyle(daysLeft);
        this.updateModalIcon(daysLeft);
        this.updateMessageBox(daysLeft);
        this.updateHeaderStyle(daysLeft);
    }

    updateProgressBarStyle(daysLeft) {
        this.progressBar.classList.remove(
            'progress-excellent', 'progress-good', 'progress-warning', 
            'progress-critical', 'progress-expired'
        );
        
        if (daysLeft > 0) {
            this.progressBar.classList.add('settings-progress-bar-animated');
        }
        
        if (daysLeft >= 4) {
            this.progressBar.classList.add('progress-excellent');
        } else if (daysLeft >= 3) {
            this.progressBar.classList.add('progress-good');
        } else if (daysLeft >= 2) {
            this.progressBar.classList.add('progress-warning');
        } else if (daysLeft >= 1) {
            this.progressBar.classList.add('progress-critical');
        } else {
            this.progressBar.classList.add('progress-expired');
        }
    }

    updateModalIcon(daysLeft) {
        this.modalIcon.className = 'fas trial-icon';
        this.modalIcon.style.animation = '';
        
        if (daysLeft >= 4) {
            this.modalIcon.classList.add('fa-clock');
            this.modalIcon.style.color = '#00c851';
            this.modalIcon.style.animation = 'rotate-slow 8s linear infinite';
        } else if (daysLeft >= 3) {
            this.modalIcon.classList.add('fa-hourglass-half');
            this.modalIcon.style.color = '#2196f3';
        } else if (daysLeft >= 2) {
            this.modalIcon.classList.add('fa-exclamation-triangle');
            this.modalIcon.style.color = '#ff9800';
            this.modalIcon.style.animation = 'pulse-warning 2s ease-in-out infinite';
        } else if (daysLeft >= 1) {
            this.modalIcon.classList.add('fa-bolt');
            this.modalIcon.style.color = '#f44336';
            this.modalIcon.style.animation = 'pulse-critical 1s ease-in-out infinite';
        }
    }

    updateMessageBox(daysLeft) {
        this.messageBox.className = 'trial-message-box';
        
        if (daysLeft === 1) {
            this.messageBox.classList.add('trial-expired-message');
            this.messageBox.innerHTML = `
                <i class="fas fa-bolt trial-message-icon" style="animation: pulse-critical 1s infinite;"></i>
                <div class="trial-message-content">
                    <strong>LAST DAY!</strong>
                    Your trial expires in less than 24 hours. Upgrade now to avoid losing access!
                </div>
            `;
        } else if (daysLeft <= 2) {
            this.messageBox.classList.add('trial-warning-message');
            this.messageBox.innerHTML = `
                <i class="fas fa-exclamation-triangle trial-message-icon"></i>
                <div class="trial-message-content">
                    <strong>Only ${daysLeft} days left!</strong>
                    Your trial expires very soon. Consider upgrading your plan.
                </div>
            `;
        } else if (daysLeft <= 4) {
            this.messageBox.classList.add('trial-info-message');
            this.messageBox.innerHTML = `
                <i class="fas fa-info-circle trial-message-icon"></i>
                <div class="trial-message-content">
                    <strong>There are ${daysLeft} trial days left.</strong>
                    Explore all the features and consider upgrading your plan.
                </div>
            `;
        } else {
            this.messageBox.classList.add('trial-info-message');
            this.messageBox.innerHTML = `
                <i class="fas fa-check-circle trial-message-icon"></i>
                <div class="trial-message-content">
                    <strong>Your trial is active</strong>
                    Make the most of all the features available during your trial period.
                </div>
            `;
        }
    }

    updateHeaderStyle(daysLeft) {
        if (daysLeft <= 1) {
            this.modalTitle.textContent = 'URGENT: Trial Ending!';
            this.modalSubtitle.textContent = 'Act now to keep your access';
        } else if (daysLeft <= 2) {
            this.modalTitle.textContent = 'Trial Ending Soon';
            this.modalSubtitle.textContent = 'Your trial expires in ' + daysLeft + ' days';
        } else {
            this.modalTitle.textContent = 'Trial Status';
            this.modalSubtitle.textContent = 'Your trial period is active';
        }
    }

    showExpiredState() {
        this.modalTitle.textContent = 'Trial Expired';
        this.modalSubtitle.textContent = 'Upgrade to continue using our service';
        
        this.modalIcon.className = 'fas fa-times-circle trial-icon';
        this.modalIcon.style.color = '#f44336';
        this.modalIcon.style.animation = '';
        
        this.timeRemaining.textContent = 'Expired';
        this.progressBar.style.width = '100%';
        this.progressText.textContent = '0%';
        this.progressBar.classList.remove('settings-progress-bar-animated');
        this.progressBar.classList.add('progress-expired');
        
        this.messageBox.className = 'trial-message-box trial-expired-message';
        this.messageBox.innerHTML = `
            <i class="fas fa-times-circle trial-message-icon"></i>
            <div class="trial-message-content">
                <strong>Trial Expired!</strong>
                Your trial period has ended. Upgrade your plan now to continue using all features.
            </div>
        `;
        
        this.upgradeBtn.className = 'trial-btn trial-btn-danger';
        this.upgradeBtn.innerHTML = '<i class="fas fa-crown"></i> Upgrade Now';
    }

    showNoTrialState() {
        this.modalTitle.textContent = 'No Active Trial';
        this.modalSubtitle.textContent = 'Start your free trial today';
        this.timeRemaining.textContent = 'N/A';
        this.progressBar.style.width = '0%';
        this.progressText.textContent = '0%';
        this.progressBar.classList.add('progress-expired');
        
        this.modalIcon.className = 'fas fa-rocket trial-icon';
        this.modalIcon.style.color = '#667eea';
        
        this.messageBox.className = 'trial-message-box trial-info-message';
        this.messageBox.innerHTML = `
            <i class="fas fa-gift trial-message-icon"></i>
            <div class="trial-message-content">
                <strong>Start Your Free Trial</strong>
                Get ${this.totalTrialDays} days of full access to all premium features, no credit card required.
            </div>
        `;
        
        this.upgradeBtn.innerHTML = '<i class="fas fa-rocket"></i> Start Free Trial';
    }

    showErrorState() {
        this.modalTitle.textContent = 'Error Loading Status';
        this.modalSubtitle.textContent = 'Unable to retrieve trial information';
        this.timeRemaining.textContent = 'Error';
        this.progressBar.style.width = '100%';
        this.progressText.textContent = 'N/A';
        this.progressBar.classList.add('progress-expired');
        
        this.modalIcon.className = 'fas fa-exclamation-circle trial-icon';
        this.modalIcon.style.color = '#e74c3c';
        
        this.messageBox.className = 'trial-message-box trial-expired-message';
        this.messageBox.innerHTML = `
            <i class="fas fa-exclamation-circle trial-message-icon"></i>
            <div class="trial-message-content">
                <strong>Connection Error</strong>
                We couldn't load your trial status. Please refresh the page or contact support.
            </div>
        `;
    }

    show() {
        this.modal.classList.add('active');
    }

    close() {
        this.modal.classList.remove('active');
    }
    }

    // Instancia global
    let trialModalInstance;

    // Inicializar al cargar la página
    document.addEventListener('DOMContentLoaded', () => {
    trialModalInstance = new TrialStatusModal();

    // Mostrar automáticamente al cargar (opcional)
    // setTimeout(() => {
    //     trialModalInstance.loadAndShow();
    // }, 1000);
    });

    // Funciones globales
    function showTrialModal() {
    if (!trialModalInstance) {
        trialModalInstance = new TrialStatusModal();
    }
    trialModalInstance.loadAndShow();
    }

    function closeTrialModal() {
    if (trialModalInstance) {
        trialModalInstance.close();
    }
    }

    function handleUpgrade() {
    // Redirigir a página de planes o abrir modal de pago
    if (confirm('¿Deseas ver los planes disponibles?')) {
        window.location.href = '/pricing'; // Cambiar por tu URL
    }
    }

    // Cerrar modal al hacer clic fuera
    document.getElementById('trialModal').addEventListener('click', (e) => {
    if (e.target.id === 'trialModal') {
        closeTrialModal();
    }
    });

    // Cerrar con tecla Escape
    document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeTrialModal();
    }
});