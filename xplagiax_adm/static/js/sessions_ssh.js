document.addEventListener('DOMContentLoaded', () => {
    const newSessionBtn = document.getElementById('newSessionBtn');
    const sessionModal = document.getElementById('sessionModal');
    const closeModal = document.getElementById('closeModal');
    const cancelBtn = document.getElementById('cancelBtn');
    const saveSessionBtn = document.getElementById('saveSessionBtn');
    const sessionForm = document.getElementById('sessionForm');
    const authTypeSelect = document.getElementById('authTypeSelect');
    const passwordGroup = document.getElementById('passwordGroup');
    const keyGroup = document.getElementById('keyGroup');
    const sessionsList = document.getElementById('sessionsList');

    // Toggle auth method fields
    authTypeSelect.addEventListener('change', () => {
        if (authTypeSelect.value === 'password') {
            passwordGroup.style.display = 'block';
            keyGroup.style.display = 'none';
        } else {
            passwordGroup.style.display = 'none';
            keyGroup.style.display = 'block';
        }
    });

    // Modal controls
    newSessionBtn.addEventListener('click', () => {
        sessionModal.classList.add('show');
    });

    closeModal.addEventListener('click', closeSessionModal);
    cancelBtn.addEventListener('click', closeSessionModal);

    function closeSessionModal() {
        sessionModal.classList.remove('show');
        sessionForm.reset();
    }

    // Save session
    saveSessionBtn.addEventListener('click', async () => {
        const formData = new FormData(sessionForm);
        const sessionData = Object.fromEntries(formData.entries());
        
        try {
            const response = await fetch('/sessionsssh_bp/api/sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(sessionData)
            });
            
            if (response.ok) {
                closeSessionModal();
                loadSessions();
            } else {
                alert('Error creating session');
            }
        } catch (error) {
            console.error('Error creating session:', error);
        }
    });

    // Load sessions
    async function loadSessions() {
        try {
            const response = await fetch('/sessionsssh_bp/api/sessions');
            const sessions = await response.json();
            
            sessionsList.innerHTML = '';
            sessions.forEach(session => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${session.name}</td>
                    <td>${session.hostname}:${session.port}</td>
                    <td>${session.username}</td>
                    <td>
                        <span class="status-badge ${session.is_active ? 'status-active' : 'status-inactive'}">
                            ${session.is_active ? 'Activa' : 'Inactiva'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-secondary connect-btn" data-id="${session.id}">
                            Conectar
                        </button>
                        <button class="btn btn-danger delete-btn" data-id="${session.id}">
                            Eliminar
                        </button>
                    </td>
                `;
                sessionsList.appendChild(row);
            });
            
            // Add event listeners to buttons
            document.querySelectorAll('.connect-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const sessionId = btn.getAttribute('data-id');
                    window.location.href = `/terminal/${sessionId}`;
                });
            });
            
            document.querySelectorAll('.delete-btn').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const sessionId = btn.getAttribute('data-id');
                    if (confirm('¿Estás seguro de eliminar esta sesión?')) {
                        await fetch(`/sessionsssh_bp/api/sessions/${sessionId}`, {
                            method: 'DELETE'
                        });
                        loadSessions();
                    }
                });
            });
        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    }

    loadSessions();
});