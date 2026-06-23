// Contact Sale CRM - JavaScript
document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const refreshBtn = document.getElementById('refreshBtn');
    const exportBtn = document.getElementById('exportBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const contactsTable = document.getElementById('contactsTable');
    const paginationContainer = document.getElementById('paginationContainer');
    const paginationInfo = document.getElementById('paginationInfo');
    
    // Elementos de estadísticas
    const totalContactsEl = document.getElementById('totalContacts');
    const recentContactsEl = document.getElementById('recentContacts');
    const conversionRateEl = document.getElementById('conversionRate');
    const totalValueEl = document.getElementById('totalValue');
    const overdueFollowupsEl = document.getElementById('overdueFollowups');
    const unassignedContactsEl = document.getElementById('unassignedContacts');
    
    // Filtros
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const priorityFilter = document.getElementById('priorityFilter');
    const serviceFilter = document.getElementById('serviceFilter');
    const assignedFilter = document.getElementById('assignedFilter');
    const dateFromFilter = document.getElementById('dateFromFilter');
    const dateToFilter = document.getElementById('dateToFilter');
    const applyFiltersBtn = document.getElementById('applyFiltersBtn');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    
    // Modals
    const contactModal = new bootstrap.Modal(document.getElementById('contactModal'));
    const interactionModal = new bootstrap.Modal(document.getElementById('interactionModal'));
    const contactInfo = document.getElementById('contactInfo');
    const interactionsList = document.getElementById('interactionsList');
    
    // Botones de modal
    const saveContactBtn = document.getElementById('saveContactBtn');
    const deleteContactBtn = document.getElementById('deleteContactBtn');
    const addInteractionBtn = document.getElementById('addInteractionBtn');
    const saveInteractionBtn = document.getElementById('saveInteractionBtn');
    
    // Variables globales
    let currentPage = 1;
    let currentContactId = null;
    let totalPages = 1;
    let allStats = {};
    let allUsers = [];
    
    // Inicializar gráficos
    const statusChart = echarts.init(document.getElementById('statusChart'));
    const monthlyChart = echarts.init(document.getElementById('monthlyChart'));
    
    // Configuración de gráfico de estados
    const statusChartOption = {
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left'
        },
        series: [
            {
                name: 'Estados',
                type: 'pie',
                radius: '50%',
                data: [],
                emphasis: {
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                }
            }
        ]
    };

    // Configuración de gráfico mensual
    const monthlyChartOption = {
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            type: 'category',
            data: []
        },
        yAxis: {
            type: 'value'
        },
        series: [
            {
                name: 'Contactos',
                type: 'line',
                smooth: true,
                data: [],
                itemStyle: { color: '#007bff' },
                areaStyle: { opacity: 0.3 }
            }
        ]
    };

    statusChart.setOption(statusChartOption);
    monthlyChart.setOption(monthlyChartOption);

    // Funciones para mostrar/ocultar loading
    function showLoading(message = 'Cargando...') {
        if (loadingOverlay) {
            document.getElementById('loadingMessage').textContent = message;
            loadingOverlay.style.display = 'flex';
        }
    }

    function hideLoading() {
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }

    // Cargar estadísticas generales
    async function loadGeneralStats() {
        try {
            const response = await fetch('/contact_sale_bp/api/stats');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            allStats = data.stats;
            
            // Actualizar elementos de estadísticas
            if (totalContactsEl) totalContactsEl.textContent = allStats.total_contacts || 0;
            if (recentContactsEl) recentContactsEl.textContent = allStats.recent_contacts || 0;
            if (conversionRateEl) conversionRateEl.textContent = (allStats.conversion_rate || 0) + '%';
            if (totalValueEl) totalValueEl.textContent = '$' + formatNumber(allStats.total_estimated_value || 0);
            if (overdueFollowupsEl) overdueFollowupsEl.textContent = allStats.overdue_followups || 0;
            if (unassignedContactsEl) unassignedContactsEl.textContent = allStats.unassigned_contacts || 0;
            
            // Actualizar gráficos
            updateStatusChart(allStats.status_distribution || []);
            updateMonthlyChart(allStats.monthly_contacts || []);
            
        } catch (error) {
            console.error('Error al cargar estadísticas:', error);
            showNotification('Error al cargar estadísticas generales', 'error');
        }
    }

    // Actualizar gráfico de estados
    function updateStatusChart(statusData) {
        const colors = {
            'new': '#2196f3',
            'contacted': '#ff9800',
            'qualified': '#9c27b0',
            'proposal': '#4caf50',
            'closed_won': '#8bc34a',
            'closed_lost': '#f44336'
        };

        const chartData = statusData.map(item => ({
            value: item.count,
            name: getStatusLabel(item.status),
            itemStyle: { color: colors[item.status] || '#666' }
        }));

        statusChartOption.series[0].data = chartData;
        statusChart.setOption(statusChartOption);
    }

    // Actualizar gráfico mensual
    function updateMonthlyChart(monthlyData) {
        const months = monthlyData.map(item => {
            const date = new Date(item.month);
            return date.toLocaleDateString('es-ES', { month: 'short', year: '2-digit' });
        });
        const values = monthlyData.map(item => item.count);

        monthlyChartOption.xAxis.data = months;
        monthlyChartOption.series[0].data = values;
        monthlyChart.setOption(monthlyChartOption);
    }

    // Cargar usuarios para asignación
    async function loadUsers() {
        try {
            const response = await fetch('/contact_sale_bp/api/users');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            allUsers = data.users;
            
            // Actualizar filtro de asignación
            const assignedSelect = document.getElementById('assignedFilter');
            assignedSelect.innerHTML = `
                <option value="">Todos</option>
                <option value="unassigned">Sin asignar</option>
            `;
            allUsers.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = user.username;
                assignedSelect.appendChild(option);
            });
            
            // Actualizar select de edición
            const editAssignedSelect = document.getElementById('editAssigned');
            editAssignedSelect.innerHTML = '<option value="">Sin asignar</option>';
            allUsers.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = user.username;
                editAssignedSelect.appendChild(option);
            });
            
        } catch (error) {
            console.error('Error al cargar usuarios:', error);
        }
    }

    // Cargar contactos con filtros y paginación
    async function loadContacts(page = 1) {
        try {
            showLoading('Cargando contactos...');
            
            const params = new URLSearchParams({
                page: page,
                per_page: 20,
                search: searchInput.value || '',
                status: statusFilter.value || '',
                priority: priorityFilter.value || '',
                service: serviceFilter.value || '',
                assigned: assignedFilter.value || '',
                date_from: dateFromFilter.value || '',
                date_to: dateToFilter.value || ''
            });
            
            const response = await fetch(`/contact_sale_bp/api/contacts?${params}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            
            // Actualizar tabla
            updateContactsTable(data.contacts);
            
            // Actualizar paginación
            updatePagination(data.pagination);
            
            currentPage = page;
            totalPages = data.pagination.total_pages;
            
        } catch (error) {
            console.error('Error al cargar contactos:', error);
            showNotification('Error al cargar contactos', 'error');
        } finally {
            hideLoading();
        }
    }

    // Actualizar tabla de contactos
    function updateContactsTable(contacts) {
        if (!contactsTable) return;
        
        contactsTable.innerHTML = '';
        
        if (contacts.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="10" style="text-align: center; padding: 40px; color: #666;">No se encontraron contactos</td>';
            contactsTable.appendChild(row);
            return;
        }
        
        contacts.forEach(contact => {
            const row = document.createElement('tr');
            row.className = 'contact-row';
            row.dataset.contactId = contact.contact_id;
            
            const scoreClass = getScoreClass(contact.lead_score);
            const statusClass = getStatusClass(contact.status);
            const priorityClass = getPriorityClass(contact.priority);
            
            row.innerHTML = `
                <td>
                    <div><strong>${contact.full_name}</strong></div>
                    <small class="text-muted">${contact.phone || 'Sin teléfono'}</small>
                </td>
                <td>${contact.email}</td>
                <td>
                    <div>${contact.company_name || 'N/A'}</div>
                    <small class="text-muted">${contact.job_title || ''}</small>
                </td>
                <td>${contact.service_interest}</td>
                <td><span class="contact-status status-${contact.status}">${getStatusLabel(contact.status)}</span></td>
                <td><span class="contact-status priority-${contact.priority}">${getPriorityLabel(contact.priority)}</span></td>
                <td><span class="lead-score score-${scoreClass}">${contact.lead_score}/100</span></td>
                <td>${contact.assigned_user_name || 'Sin asignar'}</td>
                <td>
                    <div>${formatDateTime(contact.created_at)}</div>
                    <small class="text-muted">${contact.days_since_created} días</small>
                    ${contact.is_overdue_followup ? '<div><small class="text-danger">⚠️ Seguimiento vencido</small></div>' : ''}
                </td>
                <td>
                    <button class="btn btn-action btn-info btn-sm view-contact" data-contact-id="${contact.contact_id}">
                        👁️ Ver
                    </button>
                </td>
            `;
            
            contactsTable.appendChild(row);
        });
        
        // Agregar eventos a los botones
        document.querySelectorAll('.view-contact').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const contactId = btn.dataset.contactId;
                showContactDetails(contactId);
            });
        });
        
        // Agregar eventos a las filas
        document.querySelectorAll('.contact-row').forEach(row => {
            row.addEventListener('click', () => {
                const contactId = row.dataset.contactId;
                showContactDetails(contactId);
            });
        });
    }

    // Mostrar detalles del contacto en modal
    async function showContactDetails(contactId) {
        try {
            showLoading('Cargando detalles...');
            
            const response = await fetch(`/contact_sale_bp/api/contact/${contactId}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            const contact = data.contact;
            
            currentContactId = contactId;
            
            // Llenar información del contacto
            displayContactInfo(contact);
            
            // Llenar formulario de edición
            fillEditForm(contact);
            
            // Mostrar interacciones
            displayInteractions(contact.interactions || []);
            
            contactModal.show();
            
        } catch (error) {
            console.error('Error al cargar detalles:', error);
            showNotification('Error al cargar detalles del contacto', 'error');
        } finally {
            hideLoading();
        }
    }

    // Mostrar información del contacto
    function displayContactInfo(contact) {
        const infoHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h5>Información Personal</h5>
                    <div class="metadata-grid">
                        <div class="metadata-item">
                            <div class="metadata-label">Nombre Completo</div>
                            <div class="metadata-value">${contact.full_name}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Email</div>
                            <div class="metadata-value">${contact.email}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Teléfono</div>
                            <div class="metadata-value">${contact.phone || 'N/A'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Estado</div>
                            <div class="metadata-value">
                                <span class="contact-status status-${contact.status}">${getStatusLabel(contact.status)}</span>
                            </div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Prioridad</div>
                            <div class="metadata-value">
                                <span class="contact-status priority-${contact.priority}">${getPriorityLabel(contact.priority)}</span>
                            </div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Score del Lead</div>
                            <div class="metadata-value">
                                <span class="lead-score score-${getScoreClass(contact.lead_score)}">${contact.lead_score}/100</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <h5>Información de Empresa</h5>
                    <div class="metadata-grid">
                        <div class="metadata-item">
                            <div class="metadata-label">Empresa</div>
                            <div class="metadata-value">${contact.company_name || 'N/A'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Cargo</div>
                            <div class="metadata-value">${contact.job_title || 'N/A'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Tamaño Empresa</div>
                            <div class="metadata-value">${contact.company_size || 'N/A'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Industria</div>
                            <div class="metadata-value">${contact.industry || 'N/A'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Sitio Web</div>
                            <div class="metadata-value">${contact.website ? `<a href="${contact.website}" target="_blank">${contact.website}</a>` : 'N/A'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Servicio de Interés</div>
                            <div class="metadata-value">${contact.service_interest}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-6">
                    <h5>Información de Ventas</h5>
                    <div class="metadata-grid">
                        <div class="metadata-item">
                            <div class="metadata-label">Presupuesto</div>
                            <div class="metadata-value">${contact.budget_range || 'N/A'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Timeline</div>
                            <div class="metadata-value">${contact.timeline || 'N/A'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Valor Estimado</div>
                            <div class="metadata-value">$${formatNumber(contact.estimated_value || 0)}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Asignado a</div>
                            <div class="metadata-value">${contact.assigned_user_name || 'Sin asignar'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Fuente</div>
                            <div class="metadata-value">${contact.source || 'N/A'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Intentos de Contacto</div>
                            <div class="metadata-value">${contact.contact_attempts || 0}</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <h5>Fechas Importantes</h5>
                    <div class="metadata-grid">
                        <div class="metadata-item">
                            <div class="metadata-label">Fecha de Creación</div>
                            <div class="metadata-value">${formatDateTime(contact.created_at)}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Último Contacto</div>
                            <div class="metadata-value">${formatDateTime(contact.last_contact_date) || 'Nunca'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Próximo Seguimiento</div>
                            <div class="metadata-value">${formatDateTime(contact.next_followup_date) || 'No programado'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Primera Vez Contactado</div>
                            <div class="metadata-value">${formatDateTime(contact.contacted_at) || 'No contactado'}</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Días desde Creación</div>
                            <div class="metadata-value">${contact.days_since_created} días</div>
                        </div>
                        <div class="metadata-item">
                            <div class="metadata-label">Días desde Último Contacto</div>
                            <div class="metadata-value">${contact.days_since_last_contact !== null ? contact.days_since_last_contact + ' días' : 'N/A'}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <h5>Mensaje Original</h5>
                <div class="p-3" style="background: #f8f9fa; border-radius: 6px; border-left: 4px solid #007bff;">
                    ${contact.message || 'Sin mensaje'}
                </div>
            </div>
            
            ${contact.internal_notes ? `
            <div class="mt-4">
                <h5>Notas Internas</h5>
                <div class="p-3" style="background: #fff3cd; border-radius: 6px; border-left: 4px solid #ffc107;">
                    ${contact.internal_notes}
                </div>
            </div>
            ` : ''}
        `;
        
        contactInfo.innerHTML = infoHTML;
    }

    // Llenar formulario de edición
    function fillEditForm(contact) {
        document.getElementById('editStatus').value = contact.status || '';
        document.getElementById('editPriority').value = contact.priority || '';
        document.getElementById('editAssigned').value = contact.assigned_to || '';
        document.getElementById('editEstimatedValue').value = contact.estimated_value || '';
        document.getElementById('editLeadScore').value = contact.lead_score || '';
        document.getElementById('editInternalNotes').value = contact.internal_notes || '';
        
        if (contact.next_followup_date) {
            const date = new Date(contact.next_followup_date);
            document.getElementById('editNextFollowup').value = date.toISOString().slice(0, 16);
        }
    }

    // Mostrar interacciones
    function displayInteractions(interactions) {
        if (interactions.length === 0) {
            interactionsList.innerHTML = '<p class="text-muted text-center">No hay interacciones registradas</p>';
            return;
        }
        
        const interactionsHTML = interactions.map(interaction => `
            <div class="interaction-item">
                <div class="interaction-header">
                    <div>
                        <span class="interaction-type type-${interaction.interaction_type}">${getInteractionTypeLabel(interaction.interaction_type)}</span>
                        <strong class="ms-2">${interaction.subject || 'Sin asunto'}</strong>
                    </div>
                    <div>
                        <small class="text-muted">${interaction.user_name} - ${formatDateTime(interaction.created_at)}</small>
                    </div>
                </div>
                <div class="interaction-description">
                    ${interaction.description || 'Sin descripción'}
                </div>
                ${interaction.outcome ? `<div class="mt-2"><strong>Resultado:</strong> ${interaction.outcome}</div>` : ''}
                ${interaction.next_action ? `<div><strong>Próxima acción:</strong> ${interaction.next_action}</div>` : ''}
                ${interaction.duration_minutes ? `<div><strong>Duración:</strong> ${interaction.duration_minutes} minutos</div>` : ''}
            </div>
        `).join('');
        
        interactionsList.innerHTML = interactionsHTML;
    }

    // Guardar cambios del contacto
    async function saveContact() {
        if (!currentContactId) return;
        
        try {
            showLoading('Guardando cambios...');
            
            const formData = {
                status: document.getElementById('editStatus').value,
                priority: document.getElementById('editPriority').value,
                assigned_to: document.getElementById('editAssigned').value || null,
                estimated_value: parseFloat(document.getElementById('editEstimatedValue').value) || null,
                lead_score: parseInt(document.getElementById('editLeadScore').value) || 0,
                internal_notes: document.getElementById('editInternalNotes').value,
                next_followup_date: document.getElementById('editNextFollowup').value || null
            };
            
            const response = await fetch(`/contact_sale_bp/api/contact/${currentContactId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            
            showNotification('Contacto actualizado correctamente', 'success');
            contactModal.hide();
            loadContacts(currentPage);
            loadGeneralStats();
            
        } catch (error) {
            console.error('Error al guardar contacto:', error);
            showNotification('Error al guardar cambios', 'error');
        } finally {
            hideLoading();
        }
    }

    // Eliminar contacto
    async function deleteContact() {
        if (!currentContactId) return;
        
        if (!confirm('¿Estás seguro de que quieres eliminar este contacto? Esta acción no se puede deshacer.')) {
            return;
        }
        
        try {
            showLoading('Eliminando contacto...');
            
            const response = await fetch(`/contact_sale_bp/api/contact/${currentContactId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            showNotification('Contacto eliminado correctamente', 'success');
            contactModal.hide();
            loadContacts(currentPage);
            loadGeneralStats();
            
        } catch (error) {
            console.error('Error al eliminar contacto:', error);
            showNotification('Error al eliminar contacto', 'error');
        } finally {
            hideLoading();
        }
    }

    // Agregar nueva interacción
    async function saveInteraction() {
        if (!currentContactId) return;
        
        try {
            showLoading('Guardando interacción...');
            
            const formData = {
                interaction_type: document.getElementById('interactionType').value,
                subject: document.getElementById('interactionSubject').value,
                description: document.getElementById('interactionDescription').value,
                outcome: document.getElementById('interactionOutcome').value,
                next_action: document.getElementById('interactionNextAction').value,
                next_followup_date: document.getElementById('interactionNextFollowup').value || null
            };
            
            const response = await fetch(`/contact_sale_bp/api/contact/${currentContactId}/interaction`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            showNotification('Interacción agregada correctamente', 'success');
            interactionModal.hide();
            
            // Recargar detalles del contacto
            showContactDetails(currentContactId);
            
            // Limpiar formulario
            document.getElementById('interactionForm').reset();
            
        } catch (error) {
            console.error('Error al guardar interacción:', error);
            showNotification('Error al guardar interacción', 'error');
        } finally {
            hideLoading();
        }
    }

    // Exportar contactos
    async function exportContacts() {
        try {
            showLoading('Preparando exportación...');
            
            const params = new URLSearchParams({
                status: statusFilter.value || '',
                date_from: dateFromFilter.value || '',
                date_to: dateToFilter.value || ''
            });
            
            const response = await fetch(`/contact_sale_bp/api/export?${params}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            
            // Convertir a CSV
            const csvContent = convertToCSV(data.export_data);
            
            // Descargar archivo
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `contactos_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showNotification(`${data.total_records} contactos exportados correctamente`, 'success');
            
        } catch (error) {
            console.error('Error al exportar:', error);
            showNotification('Error al exportar contactos', 'error');
        } finally {
            hideLoading();
        }
    }

    // Convertir datos a CSV
    function convertToCSV(data) {
        if (!data || data.length === 0) return '';
        
        const headers = Object.keys(data[0]);
        const csvRows = [headers.join(',')];
        
        data.forEach(row => {
            const values = headers.map(header => {
                const value = row[header] || '';
                return `"${value.toString().replace(/"/g, '""')}"`;
            });
            csvRows.push(values.join(','));
        });
        
        return csvRows.join('\n');
    }

    // Actualizar paginación
    function updatePagination(pagination) {
        if (!paginationContainer || !paginationInfo) return;
        
        paginationInfo.textContent = `Mostrando ${pagination.current_page * pagination.per_page - pagination.per_page + 1}-${Math.min(pagination.current_page * pagination.per_page, pagination.total_items)} de ${pagination.total_items} resultados`;
        
        let paginationHTML = '<nav><ul class="pagination justify-content-center">';
        
        if (pagination.has_prev) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.current_page - 1}">Anterior</a></li>`;
        }
        
        const startPage = Math.max(1, pagination.current_page - 2);
        const endPage = Math.min(pagination.total_pages, pagination.current_page + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === pagination.current_page ? 'active' : '';
            paginationHTML += `<li class="page-item ${activeClass}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
        
        if (pagination.has_next) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.current_page + 1}">Siguiente</a></li>`;
        }
        
        paginationHTML += '</ul></nav>';
        paginationContainer.innerHTML = paginationHTML;
        
        paginationContainer.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(link.dataset.page);
                if (page) loadContacts(page);
            });
        });
    }

    // Funciones helper
    function formatDateTime(dateString) {
        if (!dateString) return null;
        try {
            return new Date(dateString).toLocaleString('es-ES', {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit'
            });
        } catch (error) {
            return null;
        }
    }

    function formatNumber(number) {
        return new Intl.NumberFormat('es-ES').format(number);
    }

    function getStatusLabel(status) {
        const labels = {
            'new': 'Nuevo',
            'contacted': 'Contactado',
            'qualified': 'Calificado',
            'proposal': 'Propuesta',
            'closed_won': 'Ganado',
            'closed_lost': 'Perdido'
        };
        return labels[status] || status;
    }

    function getPriorityLabel(priority) {
        const labels = {
            'low': 'Baja',
            'medium': 'Media',
            'high': 'Alta',
            'urgent': 'Urgente'
        };
        return labels[priority] || priority;
    }

    function getInteractionTypeLabel(type) {
        const labels = {
            'email': 'Email',
            'call': 'Llamada',
            'meeting': 'Reunión',
            'note': 'Nota',
            'status_change': 'Cambio Estado'
        };
        return labels[type] || type;
    }

    function getScoreClass(score) {
        if (score >= 70) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    }

    function getStatusClass(status) {
        return status;
    }

    function getPriorityClass(priority) {
        return priority;
    }

    function showNotification(message, type = 'info', duration = 4000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icons = {
            success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️'
        };
        
        const icon = icons[type] || icons.info;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.2em;">${icon}</span>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        notification.addEventListener('click', () => notification.remove());
        setTimeout(() => notification.parentNode && notification.remove(), duration);
    }

    // Event listeners
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadGeneralStats();
            loadContacts(currentPage);
        });
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', exportContacts);
    }

    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', () => {
            currentPage = 1;
            loadContacts(1);
        });
    }

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            searchInput.value = '';
            statusFilter.value = '';
            priorityFilter.value = '';
            serviceFilter.value = '';
            assignedFilter.value = '';
            dateFromFilter.value = '';
            dateToFilter.value = '';
            currentPage = 1;
            loadContacts(1);
        });
    }

    if (saveContactBtn) {
        saveContactBtn.addEventListener('click', saveContact);
    }

    if (deleteContactBtn) {
        deleteContactBtn.addEventListener('click', deleteContact);
    }

    if (addInteractionBtn) {
        addInteractionBtn.addEventListener('click', () => {
            interactionModal.show();
        });
    }

    if (saveInteractionBtn) {
        saveInteractionBtn.addEventListener('click', saveInteraction);
    }

    // Eventos de teclado para filtros
    [searchInput, dateFromFilter, dateToFilter].forEach(input => {
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    currentPage = 1;
                    loadContacts(1);
                }
            });
        }
    });

    // Redimensionar gráficos
    window.addEventListener('resize', () => {
        statusChart.resize();
        monthlyChart.resize();
    });

    // Inicialización
    function initializeCRM() {
        showNotification('Cargando CRM...', 'info');
        
        loadUsers();
        loadGeneralStats();
        loadContacts(1);
        
        setTimeout(() => {
            showNotification('CRM cargado correctamente', 'success');
        }, 1500);
    }

    // Manejar visibilidad de la página
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            loadGeneralStats();
            loadContacts(currentPage);
        }
    });

    // Inicializar
    initializeCRM();
});