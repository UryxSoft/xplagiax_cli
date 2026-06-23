// Script para el panel de almacenamiento del usuario
document.addEventListener('DOMContentLoaded', function() {
    // Cargar información de almacenamiento al cargar la página
    loadStorageInfo();
    
    // Configurar listener para botón de eliminar archivo
    //document.getElementById('confirm-delete').addEventListener('click', deleteSelectedFile);
});

// Variables globales
let currentFileToDelete = null;
let storageData = null;

// Función para cargar información de almacenamiento
function loadStorageInfo() {
    fetch('/x_buck/api/storage/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al obtener información de almacenamiento');
            }
            return response.json();
        })
        .then(data => {
            // Guardar datos para uso posterior
            storageData = data;
            
            // Actualizar indicadores de almacenamiento
            document.getElementById('storage-used').textContent = `${data.used_storage_mb.toFixed(2)} MB`;
            document.getElementById('storage-total').textContent = `${data.total_storage_mb.toFixed(2)} MB`;
            document.getElementById('storage-remaining').textContent = `${data.remaining_storage_mb.toFixed(2)} MB`;
            //document.getElementById('current-plan').textContent = data.user_type ? data.user_type : 'Plan no asignado';
            const planElement = document.getElementById('current-plan');

            let icon = '';
            switch (data.user_type) {
                case 'Starter':
                    icon = `<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" fill="currentColor" class="bi bi-backpack" viewBox="0 0 16 16">
                                <path d="M4.04 7.43a4 4 0 0 1 7.92 0 .5.5 0 1 1-.99.14 3 3 0 0 0-5.94 0 .5.5 0 1 1-.99-.14M4 9.5a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-.5.5h-7a.5.5 0 0 1-.5-.5zm1 .5v3h6v-3h-1v.5a.5.5 0 0 1-1 0V10z"/>
                                <path d="M6 2.341V2a2 2 0 1 1 4 0v.341c2.33.824 4 3.047 4 5.659v5.5a2.5 2.5 0 0 1-2.5 2.5h-7A2.5 2.5 0 0 1 2 13.5V8a6 6 0 0 1 4-5.659M7 2v.083a6 6 0 0 1 2 0V2a1 1 0 0 0-2 0m1 1a5 5 0 0 0-5 5v5.5A1.5 1.5 0 0 0 4.5 15h7a1.5 1.5 0 0 0 1.5-1.5V8a5 5 0 0 0-5-5"/>
                            </svg>`;
                    break;
                case 'Individual':
                    icon = `<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" fill="currentColor" class="bi bi-mortarboard" viewBox="0 0 16 16">
                                <path d="M8.211 2.047a.5.5 0 0 0-.422 0l-7.5 3.5a.5.5 0 0 0 .025.917l7.5 3a.5.5 0 0 0 .372 0L14 7.14V13a1 1 0 0 0-1 1v2h3v-2a1 1 0 0 0-1-1V6.739l.686-.275a.5.5 0 0 0 .025-.917zM8 8.46 1.758 5.965 8 3.052l6.242 2.913z"/>
                                <path d="M4.176 9.032a.5.5 0 0 0-.656.327l-.5 1.7a.5.5 0 0 0 .294.605l4.5 1.8a.5.5 0 0 0 .372 0l4.5-1.8a.5.5 0 0 0 .294-.605l-.5-1.7a.5.5 0 0 0-.656-.327L8 10.466zm-.068 1.873.22-.748 3.496 1.311a.5.5 0 0 0 .352 0l3.496-1.311.22.748L8 12.46z"/>
                            </svg>`;
                    break;
                case 'Institutes':
                    icon = `<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" fill="currentColor" class="bi bi-bank" viewBox="0 0 16 16">
                                <path d="m8 0 6.61 3h.89a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-.5.5H15v7a.5.5 0 0 1 .485.38l.5 2a.498.498 0 0 1-.485.62H.5a.498.498 0 0 1-.485-.62l.5-2A.5.5 0 0 1 1 13V6H.5a.5.5 0 0 1-.5-.5v-2A.5.5 0 0 1 .5 3h.89zM3.777 3h8.447L8 1zM2 6v7h1V6zm2 0v7h2.5V6zm3.5 0v7h1V6zm2 0v7H12V6zM13 6v7h1V6zm2-1V4H1v1zm-.39 9H1.39l-.25 1h13.72z"/>
                            </svg>`;
                    break;
                default:
                    icon = '';
            }


            // Actualizar el plan
            planElement.innerHTML = data.user_type 
                ? `${data.user_type} ${icon}` 
                : 'Plan no asignado';

            // Actualizar barra de progreso personalizada
            const progressBar = document.getElementById('settin-storage-progress');
            const percentage = data.storage_usage_percentage.toFixed(1);

            // Actualizar el ancho y texto
            progressBar.style.width = `${percentage}%`;
            progressBar.textContent = `${percentage}% Used`;

            // Limpiar clases anteriores de color
            progressBar.className = 'settings-progress-bar';

            // Asignar color según el porcentaje de uso
            if (percentage < 50) {
                progressBar.classList.add('progress-success');
            } else if (percentage >= 50 && percentage < 80) {
                progressBar.classList.add('progress-warning');  
            } else if (percentage >= 80 && percentage < 90) {
                progressBar.classList.add('progress-danger-light');
            } else if (percentage >= 90) {
                progressBar.classList.add('progress-danger');
            }

            // Agregar animación si se desea
            progressBar.classList.add('progress-animated');
            
            // Mostrar complementos activos
            displayActiveAddons(data.current_addons);
            
            // Mostrar planes disponibles
            displayAvailablePlans(data.available_plans, data.current_plan);
            
            // Mostrar complementos disponibles
            displayAvailableAddons(data.available_addons);
        })
   
}


// Función para mostrar complementos activos
function displayActiveAddons(addons) {
    const activeAddonsDiv = document.getElementById('active-addons');
    activeAddonsDiv.innerHTML = '';
    
    if (addons && addons.length > 0) {
        addons.forEach(addon => {
            const col = document.createElement('div');
            col.classList.add('col-md-6', 'mb-3');
            
            const expiryDate = addon.expiry_date ? new Date(addon.expiry_date).toLocaleDateString() : 'No expira';
            
            col.innerHTML = `
                <div class="card h-100 addon-card">
                    <div class="card-body">
                        <h5 class="card-title">${addon.name}</h5>
                        <p class="card-text">Espacio adicional: ${addon.storage_gb.toFixed(1)} GB</p>
                        <p class="card-text">Vence: ${expiryDate}</p>
                        <p class="card-text">
                            <small class="text-white">
                                ${addon.auto_renew ? 
                                    '<i class="bi bi-arrow-repeat"></i> Renovación automática activa' : 
                                    '<i class="bi bi-x-circle"></i> Sin renovación automática'}
                            </small>
                        </p>
                        ${addon.auto_renew ? 
                            `<button class="btn btn-sm btn-light cancel-addon" data-subscription-id="${addon.id}">
                                Cancelar renovación
                            </button>` : ''}
                    </div>
                </div>
            `;
            activeAddonsDiv.appendChild(col);
        });
        
        // Agregar event listeners a los botones de cancelar renovación
        document.querySelectorAll('.cancel-addon').forEach(button => {
            button.addEventListener('click', function() {
                const subscriptionId = this.getAttribute('data-subscription-id');
                cancelAddonSubscription(subscriptionId);
            });
        });
    } else {
        activeAddonsDiv.innerHTML = '<div class="col-12"><p class="text-center">No tienes complementos activos</p></div>';
    }
}

// Función para mostrar planes disponibles
function displayAvailablePlans(plans, currentPlan) {
    const availablePlansDiv = document.getElementById('available-plans');
    availablePlansDiv.innerHTML = '';
    
    if (plans && plans.length > 0) {
        plans.forEach(plan => {
            const col = document.createElement('div');
            col.classList.add('col-md-6', 'mb-3');
            
            // Determinar si este es el plan actual
            const isCurrentPlan = currentPlan && plan.id === currentPlan.id;
            
            col.innerHTML = `
                <div class="card h-100 upgrade-card">
                    <div class="card-body">
                        <h5 class="card-title">${plan.name}</h5>
                        <p class="card-text">Almacenamiento: ${plan.storage_gb.toFixed(1)} GB</p>
                        <p class="card-text">${plan.description || ''}</p>
                        ${isCurrentPlan ? 
                            '<button class="btn btn-light" disabled>Plan Actual</button>' : 
                            `<button class="btn btn-light upgrade-plan" data-plan-id="${plan.id}">
                                Actualizar a este Plan
                            </button>`}
                    </div>
                </div>
            `;
            availablePlansDiv.appendChild(col);
        });
        
        // Agregar event listeners a los botones de actualizar plan
        document.querySelectorAll('.upgrade-plan').forEach(button => {
            button.addEventListener('click', function() {
                const planId = this.getAttribute('data-plan-id');
                upgradeToPlan(planId);
            });
        });
    } else {
        availablePlansDiv.innerHTML = '<div class="col-12"><p class="text-center">No hay planes disponibles para actualizar</p></div>';
    }
}

// Función para mostrar complementos disponibles
function displayAvailableAddons(addons) {
    const availableAddonsDiv = document.getElementById('available-addons');
    availableAddonsDiv.innerHTML = '';
    
    if (addons && addons.length > 0) {
        addons.forEach(addon => {
            const col = document.createElement('div');
            col.classList.add('col-md-6', 'mb-3');
            
            col.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">${addon.name}</h5>
                        <p class="card-text">Espacio adicional: ${addon.storage_gb.toFixed(1)} GB</p>
                        <p class="card-text">Precio: $${addon.price_monthly_usd.toFixed(2)}/mes</p>
                        <button class="btn btn-success purchase-addon" data-addon-id="${addon.id}">
                            Adquirir Ahora
                        </button>
                    </div>
                </div>
            `;
            availableAddonsDiv.appendChild(col);
        });
        
        // Agregar event listeners a los botones de comprar complemento
        document.querySelectorAll('.purchase-addon').forEach(button => {
            button.addEventListener('click', function() {
                const addonId = this.getAttribute('data-addon-id');
                purchaseAddon(addonId);
            });
        });
    } else {
        availableAddonsDiv.innerHTML = '<div class="col-12"><p class="text-center">No hay complementos disponibles para tu plan actual</p></div>';
    }
}

// Función para mostrar el modal de confirmación de eliminación
function showDeleteConfirmation(fileId, fileName) {
    const deleteFileNameSpan = document.getElementById('delete-file-name');
    deleteFileNameSpan.textContent = fileName;
    currentFileToDelete = fileId;
    
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    deleteModal.show();
}

// Función para eliminar el archivo seleccionado
function deleteSelectedFile() {
    if (!currentFileToDelete) return;
    
    fetch(`/api/files/${currentFileToDelete}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error al eliminar archivo');
        }
        return response.json();
    })
    .then(data => {
        // Cerrar modal
        const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
        deleteModal.hide();
        
        // Mostrar mensaje de éxito
        showAlert('Archivo eliminado correctamente', 'success');
        
        // Recargar información de almacenamiento
        loadStorageInfo();
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('No se pudo eliminar el archivo', 'danger');
    });
}

// Función para actualizar plan
function upgradeToPlan(planId) {
    fetch(`/api/storage/upgrade-plan/${planId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error al actualizar plan');
        }
        return response.json();
    })
    .then(data => {
        // Cerrar modal
        const upgradeModal = bootstrap.Modal.getInstance(document.getElementById('upgradeModal'));
        upgradeModal.hide();
        
        // Mostrar mensaje de éxito
        showAlert(data.message, 'success');
        
        // Recargar información de almacenamiento
        loadStorageInfo();
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('No se pudo actualizar el plan', 'danger');
    });
}

// Función para comprar complemento
function purchaseAddon(addonId) {
    fetch(`/api/storage/purchase-addon/${addonId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error al adquirir complemento');
        }
        return response.json();
    })
    .then(data => {
        // Cerrar modal
        const addonsModal = bootstrap.Modal.getInstance(document.getElementById('addonsModal'));
        addonsModal.hide();
        
        // Mostrar mensaje de éxito
        showAlert(data.message, 'success');
        
        // Recargar información de almacenamiento
        loadStorageInfo();
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('No se pudo adquirir el complemento', 'danger');
    });
}

// Función para cancelar suscripción a complemento
function cancelAddonSubscription(subscriptionId) {
    fetch(`/api/storage/cancel-addon/${subscriptionId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error al cancelar suscripción');
        }
        return response.json();
    })
    .then(data => {
        // Mostrar mensaje de éxito
        showAlert(data.message, 'success');
        
        // Recargar información de almacenamiento
        loadStorageInfo();
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('No se pudo cancelar la suscripción', 'danger');
    });
}

// Función para mostrar alertas
function showAlert(message, type) {
    const alertsContainer = document.createElement('div');
    alertsContainer.className = 'alert-container';
    alertsContainer.style.position = 'fixed';
    alertsContainer.style.top = '20px';
    alertsContainer.style.right = '20px';
    alertsContainer.style.zIndex = '9999';
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertsContainer.appendChild(alertElement);
    document.body.appendChild(alertsContainer);
    
    // Auto-cerrar después de 5 segundos
    setTimeout(() => {
        alertElement.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(alertsContainer);
        }, 150);
    }, 5000);
}