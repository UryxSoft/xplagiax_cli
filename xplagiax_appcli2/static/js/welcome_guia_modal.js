let currentSlide = 0;
const totalSlides = 6;
let autoSlideInterval;

// Welcome modal disabled — set to false to re-enable.
const WELCOME_MODAL_DISABLED = true;

// Initialize modal on page load
window.addEventListener('DOMContentLoaded', () => {
    if (WELCOME_MODAL_DISABLED) return; // do not init/show the welcome modal
    createPaginationDots();
    checkAndShowModal();
});

function createPaginationDots() {
    const dotsContainer = document.getElementById('paginationDots');
    dotsContainer.innerHTML = '';
    
    for (let i = 0; i < totalSlides; i++) {
        const dot = document.createElement('div');
        dot.className = `dot ${i === 0 ? 'active' : ''}`;
        dot.onclick = () => goToSlide(i);
        dotsContainer.appendChild(dot);
    }
}

// Check with backend if modal should be shown
async function checkAndShowModal() {
    try {
        const response = await fetch('/api/check-welcome-modal');
        const data = await response.json();
        
    //   console.log(data);

        if (data.success && data.show_modal) {
            setTimeout(() => {
                showWelcomeModal();
            }, 500);
        }
    } catch (error) {
        console.error('Error checking modal status:', error);
    }
}

function showWelcomeModal() {
    if (WELCOME_MODAL_DISABLED) return; // disabled — never show
    const modal = document.getElementById('welcomeModal');
    modal.classList.add('active');
    startAutoSlide();
}

async function closeWelcomeModal() {
    const dontShowCheckbox = document.getElementById('dontShowAgain');
    const closeBtn = document.getElementById('closeBtn');
    
    // Disable button and show loading
    closeBtn.disabled = true;
    closeBtn.innerHTML = 'Saving... <span class="spinner"></span>';
    
    try {
        // Send preference to backend
        const response = await fetch('/api/dismiss-welcome-modal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                dont_show_again: dontShowCheckbox.checked
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Close modal
            const modal = document.getElementById('welcomeModal');
            modal.classList.remove('active');
            stopAutoSlide();
            
            // Reset button
            setTimeout(() => {
                closeBtn.disabled = false;
                closeBtn.innerHTML = '<i class="bi bi-check2-square"></i> Got it';
                goToSlide(0);
            }, 400);
        } else {
            throw new Error(data.error || 'Error saving preference');
        }
    } catch (error) {
        console.error('Error saving preference:', error);
        //alert('Error al guardar la preferencia. Por favor intenta de nuevo.');
        closeBtn.disabled = false;
        closeBtn.innerHTML = '<i class="bi bi-check2-square"></i> Got it';
    }
}

// Reset modal preference (for testing)
async function resetModalPreference() {
    try {
        const response = await fetch('/api/reset-welcome-modal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            //alert('Preferencia reseteada. Recarga la página para ver el modal.');
            location.reload();
        }
    } catch (error) {
        console.error('Error resetting preference:', error);
        //alert('Error al resetear la preferencia.');
    }
}

function manualShowModal() {
    showWelcomeModal();
}

function nextSlide() {
    currentSlide = (currentSlide + 1) % totalSlides;
    updateSlide();
    resetAutoSlide();
}

function prevSlide() {
    currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
    updateSlide();
    resetAutoSlide();
}

function goToSlide(index) {
    currentSlide = index;
    updateSlide();
    resetAutoSlide();
}

function updateSlide() {
    const wrapper = document.getElementById('slidesWrapper');
    wrapper.style.transform = `translateX(-${currentSlide * 100}%)`;
    
    const dots = document.querySelectorAll('.dot');
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === currentSlide);
    });
}

function startAutoSlide() {
    autoSlideInterval = setInterval(() => {
        nextSlide();
    }, 5000);
}

function stopAutoSlide() {
    if (autoSlideInterval) {
        clearInterval(autoSlideInterval);
    }
}

function resetAutoSlide() {
    stopAutoSlide();
    startAutoSlide();
}

// Close modal on overlay click
document.getElementById('welcomeModal').addEventListener('click', (e) => {
    if (e.target.id === 'welcomeModal') {
        closeWelcomeModal();
    }
});

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    const modal = document.getElementById('welcomeModal');
    if (modal.classList.contains('active')) {
        if (e.key === 'ArrowLeft') prevSlide();
        if (e.key === 'ArrowRight') nextSlide();
        if (e.key === 'Escape') closeWelcomeModal();
    }
});