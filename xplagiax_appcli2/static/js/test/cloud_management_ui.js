/**
 * Cloud Storage Management UI Controller
 * Handles context menus, modals, and UI interactions for cloud storage operations
 * Works with StorageManager class for API calls
 */

// ============================================================
// CLOUD CONTEXT MENU
// ============================================================

let cloudContextMenuTarget = null;
let cloudContextMenuType = null;

function initCloudContextMenu() {
    const contextMenu = document.getElementById('cloud-context-menu');
    if (!contextMenu) return;

    // Close menu on click outside
    document.addEventListener('click', (e) => {
        if (!contextMenu.contains(e.target)) {
            hideCloudContextMenu();
        }
    });

    // Handle context menu actions
    contextMenu.querySelectorAll('.context-menu-item').forEach(item => {
        item.addEventListener('click', () => {
            const action = item.dataset.action;
            handleCloudContextAction(action);
            hideCloudContextMenu();
        });
    });

    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideCloudContextMenu();
        }
    });
}

function showCloudContextMenu(e, item, itemType) {
    e.preventDefault();
    e.stopPropagation();

    // Only show for cloud storage items
    if (!window.storageManager || window.storageManager.currentStorage === 'native') {
        return;
    }

    const contextMenu = document.getElementById('cloud-context-menu');
    if (!contextMenu) return;

    cloudContextMenuTarget = item;
    cloudContextMenuType = itemType;

    // Update context menu title
    const title = document.getElementById('context-menu-title');
    if (title) {
        const icon = itemType === 'folder' ? 'bi-folder-fill' : 'bi-file-earmark';
        const name = item.name || item.title || 'Item';
        title.innerHTML = `<i class="bi ${icon}"></i><span>${truncateText(name, 20)}</span>`;
    }

    // Show/hide download option based on type
    const downloadItem = contextMenu.querySelector('[data-action="download"]');
    if (downloadItem) {
        downloadItem.style.display = itemType === 'folder' ? 'none' : 'flex';
    }

    // Show/hide open option based on type
    const openItem = contextMenu.querySelector('[data-action="open"]');
    if (openItem) {
        openItem.style.display = itemType === 'folder' ? 'flex' : 'none';
    }

    // Position the menu
    const x = e.clientX;
    const y = e.clientY;

    contextMenu.style.left = `${Math.min(x, window.innerWidth - 200)}px`;
    contextMenu.style.top = `${Math.min(y, window.innerHeight - 250)}px`;
    contextMenu.classList.add('active');
}

function hideCloudContextMenu() {
    const contextMenu = document.getElementById('cloud-context-menu');
    if (contextMenu) {
        contextMenu.classList.remove('active');
    }
    cloudContextMenuTarget = null;
    cloudContextMenuType = null;
}

function handleCloudContextAction(action) {
    if (!cloudContextMenuTarget || !window.storageManager) return;

    const sm = window.storageManager;
    const item = cloudContextMenuTarget;
    const type = cloudContextMenuType;

    switch (action) {
        case 'open':
            if (type === 'folder') {
                sm.openCloudFolder(item.id, item.name);
            }
            break;
        case 'rename':
            openCloudRenameModal(item, type);
            break;
        case 'move':
            openCloudFolderPicker(item, type);
            break;
        case 'download':
            if (type === 'file') {
                sm.downloadCloudFile(item.id, item.name);
            }
            break;
        case 'delete':
            openCloudDeleteModal(item, type);
            break;
    }
}

// ============================================================
// CLOUD RENAME MODAL
// ============================================================

let renameTarget = null;
let renameTargetType = null;

function openCloudRenameModal(item, type) {
    renameTarget = item;
    renameTargetType = type;

    const modal = document.getElementById('cloud-rename-modal');
    const input = document.getElementById('cloud-rename-input');

    if (!modal || !input) return;

    const name = item.name || item.title || '';
    input.value = name;

    if (typeof populateRenameHero === 'function') {
        populateRenameHero('cloud-rename-hero', name, type, item);
    }

    modal.classList.add('active');
    if (typeof wireRenameValidation === 'function') {
        wireRenameValidation('cloud-rename-input', 'cloud-rename-error', 'confirm-cloud-rename', () => name,
            (result, curName, rawValue) => {
                if (typeof updateRenameExtras === 'function') updateRenameExtras('cloud-rename', result, curName, rawValue);
            });
    }
    if (typeof selectRenameBasename === 'function') {
        selectRenameBasename(input, name, type);
    } else {
        input.focus();
        input.select();
    }
}

function closeCloudRenameModal() {
    const modal = document.getElementById('cloud-rename-modal');
    if (modal) modal.classList.remove('active');
    renameTarget = null;
    renameTargetType = null;
}

async function confirmCloudRename() {
    if (!renameTarget || !window.storageManager) return;

    const input = document.getElementById('cloud-rename-input');
    const currentName = renameTarget.name || renameTarget.title || '';
    const result = typeof validateItemName === 'function'
        ? validateItemName(input?.value, currentName)
        : { valid: !!input?.value?.trim(), trimmed: input?.value?.trim(), isNoop: false };

    if (!result.valid) {
        input.classList.add('is-invalid');
        const errorEl = document.getElementById('cloud-rename-error');
        if (errorEl) { errorEl.textContent = result.error || 'Please enter a name'; errorEl.classList.remove('d-none'); }
        return;
    }

    if (result.isNoop) {
        closeCloudRenameModal();
        return;
    }

    const newName = result.trimmed;
    const sm = window.storageManager;

    // Call the backend directly with the new name
    const endpoint = renameTargetType === 'folder'
        ? `/x_integ/storage/folder/rename/${sm.currentStorage}`
        : `/x_integ/storage/file/rename/${sm.currentStorage}`;

    const bodyKey = renameTargetType === 'folder' ? 'folder_id' : 'file_id';

    const btn = document.getElementById('confirm-cloud-rename');
    const originalBtnHtml = btn ? btn.innerHTML : '';
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...'; }

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [bodyKey]: renameTarget.id, new_name: newName })
        });

        const result2 = await response.json();
        if (result2.success) {
            if (btn) btn.innerHTML = '<i class="bi bi-check-lg"></i> Renamed!';
            showToast('Renamed successfully', 'success');
            await sm.loadStorageContent(sm.currentStorage, sm.cloudFolderId);
            setTimeout(closeCloudRenameModal, 500);
            return;
        } else {
            showToast(result2.error || 'Failed to rename', 'error');
            if (btn) { btn.disabled = false; btn.innerHTML = originalBtnHtml; }
            return;
        }
    } catch (error) {
        console.error('Rename error:', error);
        showToast('Failed to rename', 'error');
        if (btn) { btn.disabled = false; btn.innerHTML = originalBtnHtml; }
    }
}


// ============================================================
// CLOUD DELETE MODAL
// ============================================================

let deleteTarget = null;
let deleteTargetType = null;

function openCloudDeleteModal(item, type) {
    deleteTarget = item;
    deleteTargetType = type;

    const modal = document.getElementById('cloud-delete-modal');
    const title = document.getElementById('cloud-delete-title');
    const message = document.getElementById('cloud-delete-message');
    const folderWarning = document.getElementById('cloud-folder-delete-warning');
    const restoreInfo = document.getElementById('cloud-delete-restore-info');

    if (!modal) return;

    const name = item.name || item.title || 'this item';
    if (typeof populateRenameHero === 'function') populateRenameHero('cloud-delete-hero', name, type, item);

    if (title) title.textContent = 'Delete this item?';
    if (message) message.textContent = `This will move ${type === 'folder' ? 'the folder' : 'the file'} to trash.`;

    if (folderWarning) {
        folderWarning.classList.toggle('d-none', type !== 'folder');
    }

    // Show restore info based on provider capabilities
    if (restoreInfo) {
        const sm = window.storageManager;
        const provider = sm?.currentStorage || '';
        // Dropbox delete is permanent, others have trash
        if (provider === 'dropbox') {
            restoreInfo.innerHTML = '<i class="bi bi-exclamation-triangle"></i> Warning: Dropbox delete may be permanent.';
            restoreInfo.classList.remove('alert-info');
            restoreInfo.classList.add('alert-warning');
        } else {
            restoreInfo.innerHTML = '<i class="bi bi-recycle"></i> You can restore from the cloud provider\'s trash.';
            restoreInfo.classList.remove('alert-warning');
            restoreInfo.classList.add('alert-info');
        }
    }

    modal.classList.add('active');
}

function closeCloudDeleteModal() {
    const modal = document.getElementById('cloud-delete-modal');
    if (modal) modal.classList.remove('active');
    deleteTarget = null;
    deleteTargetType = null;
}

async function confirmCloudDelete() {
    if (!deleteTarget || !window.storageManager) return;

    const sm = window.storageManager;
    await sm.deleteCloudItem(deleteTarget.id, deleteTargetType, deleteTarget.name || deleteTarget.title);
    closeCloudDeleteModal();
}

// ============================================================
// CLOUD FOLDER PICKER MODAL (for Move operations)
// ============================================================

let moveTarget = null;
let moveTargetType = null;
let pickerCurrentFolderId = null;
let pickerBreadcrumbs = [{ id: null, name: 'Root' }];
let selectedMoveDestination = null;
let selectedMoveDestinationName = null;
let pickerRawFolders = [];

function openCloudFolderPicker(item, type) {
    moveTarget = item;
    moveTargetType = type;
    pickerCurrentFolderId = null;
    pickerBreadcrumbs = [{ id: null, name: 'Root' }];
    selectedMoveDestination = undefined;
    selectedMoveDestinationName = null;

    const modal = document.getElementById('cloud-folder-picker-modal');
    const itemName = document.getElementById('move-item-name');
    const itemIconBadge = document.getElementById('move-item-icon-badge');
    const itemMeta = document.getElementById('move-item-meta');
    const confirmBtn = document.getElementById('confirm-cloud-move');
    const searchInput = document.getElementById('picker-search-input');

    if (!modal) return;

    const name = item.name || item.title || 'Item';
    if (itemName) { itemName.textContent = name; itemName.title = name; }

    if (itemIconBadge) {
        if (type === 'folder') {
            itemIconBadge.style.background = '#fef3c7';
            itemIconBadge.innerHTML = '<i class="bi bi-folder-fill" style="color:#b45309;"></i>';
            if (itemMeta) itemMeta.textContent = 'Folder';
        } else if (typeof _nativeFileTypeInfo === 'function') {
            const info = _nativeFileTypeInfo(name);
            itemIconBadge.style.background = info.tagBg;
            itemIconBadge.innerHTML = `<i class="bi ${info.icon}" style="color:${info.tagColor};"></i>`;
            const size = item.size !== undefined && item.size !== null && typeof formatSize === 'function' ? formatSize(item.size) : null;
            if (itemMeta) itemMeta.textContent = size ? `${info.label} File · ${size}` : `${info.label} File`;
        }
    }

    if (confirmBtn) confirmBtn.disabled = true;
    updatePickerMoveLabel();
    hidePickerNewFolderRow();
    if (searchInput) searchInput.value = '';

    modal.classList.add('active');
    loadPickerFolders(null);
}

function closeCloudFolderPicker() {
    const modal = document.getElementById('cloud-folder-picker-modal');
    if (modal) modal.classList.remove('active');
    moveTarget = null;
    moveTargetType = null;
}

function pickerSkeletonHtml() {
    return `
        <div class="picker-skeleton">
            <div class="picker-skeleton-row"></div>
            <div class="picker-skeleton-row"></div>
            <div class="picker-skeleton-row"></div>
            <div class="picker-skeleton-row"></div>
        </div>
    `;
}

async function loadPickerFolders(folderId) {
    pickerCurrentFolderId = folderId;
    // Poka-Yoke: navigating resets any prior selection — a destination
    // picked at a different level no longer applies to the new view.
    selectedMoveDestination = undefined;
    selectedMoveDestinationName = null;
    const confirmBtn = document.getElementById('confirm-cloud-move');
    if (confirmBtn) confirmBtn.disabled = true;
    updatePickerMoveLabel();
    updatePickerDestinationSummary();
    hidePickerNewFolderRow();

    const upBtn = document.getElementById('picker-up-btn');
    if (upBtn) upBtn.disabled = pickerBreadcrumbs.length <= 1;

    const searchInput = document.getElementById('picker-search-input');
    if (searchInput) searchInput.value = '';

    const container = document.getElementById('picker-folder-list');
    if (!container || !window.storageManager) return;

    container.innerHTML = pickerSkeletonHtml();

    try {
        const sm = window.storageManager;
        const provider = sm.currentStorage;

        let url = `/x_integ/storage/folder/${provider}`;
        if (folderId) {
            url += `/${encodeURIComponent(folderId)}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        pickerRawFolders = data.folders || [];
        renderPickerFolders(pickerRawFolders);
        renderPickerBreadcrumbs();
    } catch (error) {
        console.error('Error loading folders:', error);
        container.innerHTML = '<div class="text-center text-danger py-4"><i class="bi bi-exclamation-triangle"></i> Error loading folders</div>';
    }
}

function renderPickerFolders(folders) {
    const container = document.getElementById('picker-folder-list');
    if (!container) return;

    // Filter out the folder being moved (can't move to itself)
    const filteredFolders = folders.filter(f => {
        if (moveTargetType === 'folder' && moveTarget) {
            return f.id !== moveTarget.id;
        }
        return true;
    });

    // "Move to this folder" — explicit, deliberate selection of the folder
    // currently being browsed (nothing is auto-selected just from viewing).
    // Blocked when we've navigated into the very folder being moved.
    const isSelfFolder = moveTargetType === 'folder' && moveTarget && String(pickerCurrentFolderId) === String(moveTarget.id);
    const currentFolderName = pickerBreadcrumbs.length ? pickerBreadcrumbs[pickerBreadcrumbs.length - 1].name : 'Root';
    const currentOptionHtml = isSelfFolder
        ? `<div class="folder-picker-item folder-picker-item--disabled" title="Cannot move a folder into itself">
               <div class="folder-picker-item-icon folder-picker-item-icon--disabled"><i class="bi bi-slash-circle"></i></div>
               <span class="folder-picker-item-name flex-grow-1">Cannot move here (same folder)</span>
           </div>`
        : `<div class="folder-picker-item folder-picker-item--current">
               <div class="folder-picker-item-icon folder-picker-item-icon--current"><i class="bi bi-check2-circle"></i></div>
               <span class="folder-picker-item-name flex-grow-1">Move to this folder</span>
           </div>`;

    const subfoldersHtml = filteredFolders.length === 0
        ? `<div class="picker-empty-state"><i class="bi bi-folder2-open"></i><p>This folder doesn't contain any subfolders.</p></div>`
        : filteredFolders.map(folder => `
        <div class="folder-picker-item" data-id="${folder.id}" data-name="${folder.name}">
            <div class="folder-picker-item-icon"><i class="bi bi-folder-fill"></i></div>
            <span class="folder-picker-item-name flex-grow-1">${folder.name}</span>
            <i class="bi bi-chevron-right folder-picker-item-arrow"></i>
        </div>
    `).join('');

    container.innerHTML = currentOptionHtml + subfoldersHtml;

    // "Move to this folder" row: select-only, no navigation target
    const currentOption = container.querySelector('.folder-picker-item--current');
    if (currentOption) {
        currentOption.addEventListener('click', () => {
            container.querySelectorAll('.folder-picker-item').forEach(i => i.classList.remove('selected'));
            currentOption.classList.add('selected');
            selectedMoveDestination = pickerCurrentFolderId;
            selectedMoveDestinationName = currentFolderName;
            document.getElementById('confirm-cloud-move').disabled = false;
            updatePickerMoveLabel();
            updatePickerDestinationSummary();
        });
    }

    // Subfolder rows: click once to select, click the selected row again to navigate in
    container.querySelectorAll('.folder-picker-item:not(.folder-picker-item--current):not(.folder-picker-item--disabled)').forEach(item => {
        item.addEventListener('click', () => {
            const id = item.dataset.id;
            const name = item.dataset.name;

            if (item.classList.contains('selected')) {
                // Second click on an already-selected row - navigate into it
                pickerBreadcrumbs.push({ id, name });
                loadPickerFolders(id);
            } else {
                container.querySelectorAll('.folder-picker-item').forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
                selectedMoveDestination = id;
                selectedMoveDestinationName = name;
                document.getElementById('confirm-cloud-move').disabled = false;
                updatePickerMoveLabel();
                updatePickerDestinationSummary();
            }
        });

        // Double click to navigate into folder
        item.addEventListener('dblclick', () => {
            const id = item.dataset.id;
            const name = item.dataset.name;
            pickerBreadcrumbs.push({ id, name });
            loadPickerFolders(id);
        });
    });
}

// Client-side filter over the already-loaded current level (not a deep
// recursive search across the whole tree — there's no endpoint for that).
function filterPickerFolders(query) {
    const q = (query || '').trim().toLowerCase();
    if (!q) { renderPickerFolders(pickerRawFolders); return; }
    renderPickerFolders(pickerRawFolders.filter(f => (f.name || '').toLowerCase().includes(q)));
}

function updatePickerMoveLabel() {
    const label = document.getElementById('confirm-cloud-move-label');
    if (label) label.textContent = selectedMoveDestinationName ? `Move to "${truncateText(selectedMoveDestinationName, 24)}"` : 'Move Here';
}

function updatePickerDestinationSummary() {
    const summary = document.getElementById('picker-destination-summary');
    const nameEl = document.getElementById('picker-destination-name');
    if (!summary) return;
    if (selectedMoveDestinationName) {
        if (nameEl) nameEl.textContent = selectedMoveDestinationName;
        summary.classList.remove('d-none');
    } else {
        summary.classList.add('d-none');
    }
}

function hidePickerNewFolderRow() {
    const row = document.getElementById('picker-new-folder-row');
    const input = document.getElementById('picker-new-folder-input');
    if (row) row.classList.add('d-none');
    if (input) input.value = '';
}

function togglePickerNewFolderRow() {
    const row = document.getElementById('picker-new-folder-row');
    const input = document.getElementById('picker-new-folder-input');
    if (!row) return;
    const willShow = row.classList.contains('d-none');
    row.classList.toggle('d-none', !willShow);
    if (willShow && input) input.focus();
    else if (input) input.value = '';
}

async function createFolderFromPicker() {
    const input = document.getElementById('picker-new-folder-input');
    const name = input?.value?.trim();
    if (!name) { input?.focus(); return; }
    if (!window.storageManager) return;

    const confirmBtn = document.getElementById('picker-new-folder-confirm');
    if (confirmBtn) confirmBtn.disabled = true;

    try {
        const sm = window.storageManager;
        const response = await fetch(`/x_integ/storage/folder/create/${sm.currentStorage}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, parent_id: pickerCurrentFolderId })
        });
        const result = await response.json();
        if (result.success) {
            showToast('Folder created', 'success');
            hidePickerNewFolderRow();
            await loadPickerFolders(pickerCurrentFolderId);
        } else {
            showToast(result.error || 'Failed to create folder', 'error');
        }
    } catch (error) {
        console.error('Create folder error:', error);
        showToast('Failed to create folder', 'error');
    } finally {
        if (confirmBtn) confirmBtn.disabled = false;
    }
}

function navigatePickerUp() {
    if (pickerBreadcrumbs.length <= 1) return;
    pickerBreadcrumbs = pickerBreadcrumbs.slice(0, -1);
    const target = pickerBreadcrumbs[pickerBreadcrumbs.length - 1];
    loadPickerFolders(target.id);
}

function renderPickerBreadcrumbs() {
    const container = document.getElementById('picker-breadcrumbs');
    if (!container) return;

    container.innerHTML = pickerBreadcrumbs.map((crumb, index) => {
        const isLast = index === pickerBreadcrumbs.length - 1;
        const icon = index === 0 ? '<i class="bi bi-house-fill"></i> ' : '';
        return `<span class="picker-crumb ${isLast ? 'active' : ''}" data-index="${index}">${icon}${crumb.name}</span>`;
    }).join('<i class="bi bi-chevron-right picker-crumb-sep"></i>');

    // Add click handlers for breadcrumb navigation
    container.querySelectorAll('.picker-crumb').forEach(crumb => {
        crumb.addEventListener('click', () => {
            const index = parseInt(crumb.dataset.index);
            if (index < pickerBreadcrumbs.length - 1) {
                pickerBreadcrumbs = pickerBreadcrumbs.slice(0, index + 1);
                const targetId = pickerBreadcrumbs[index].id;
                loadPickerFolders(targetId);
            }
        });
    });
}

async function confirmCloudMove() {
    if (!moveTarget || !window.storageManager || selectedMoveDestination === undefined) return;

    const sm = window.storageManager;
    const btn = document.getElementById('confirm-cloud-move');
    const originalBtnHtml = btn ? btn.innerHTML : '';
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Moving...'; }

    const success = await sm.moveCloudItem(moveTarget.id, moveTargetType, selectedMoveDestination);

    if (success) {
        if (btn) btn.innerHTML = '<i class="bi bi-check-lg"></i> Moved!';
        setTimeout(closeCloudFolderPicker, 500);
    } else if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalBtnHtml;
    }
}

// Toolbar wiring for the folder picker: search-as-you-type, up-one-level,
// and inline "new folder" creation (Enter confirms, Escape cancels).
document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('picker-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function () {
            filterPickerFolders(this.value);
        }, 200));
    }

    const upBtn = document.getElementById('picker-up-btn');
    if (upBtn) upBtn.addEventListener('click', navigatePickerUp);

    const newFolderBtn = document.getElementById('picker-new-folder-btn');
    if (newFolderBtn) newFolderBtn.addEventListener('click', togglePickerNewFolderRow);

    const newFolderCancel = document.getElementById('picker-new-folder-cancel');
    if (newFolderCancel) newFolderCancel.addEventListener('click', hidePickerNewFolderRow);

    const newFolderConfirm = document.getElementById('picker-new-folder-confirm');
    if (newFolderConfirm) newFolderConfirm.addEventListener('click', createFolderFromPicker);

    const newFolderInput = document.getElementById('picker-new-folder-input');
    if (newFolderInput) {
        newFolderInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') { e.preventDefault(); createFolderFromPicker(); }
            else if (e.key === 'Escape') { e.preventDefault(); hidePickerNewFolderRow(); }
        });
    }

    // Enter confirms the move when a valid destination is selected.
    const moveModalEl = document.getElementById('cloud-folder-picker-modal');
    if (moveModalEl) {
        moveModalEl.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter') return;
            const active = document.activeElement;
            if (active && (active.id === 'picker-search-input' || active.id === 'picker-new-folder-input')) return;
            const confirmBtn = document.getElementById('confirm-cloud-move');
            if (confirmBtn && !confirmBtn.disabled) { e.preventDefault(); confirmBtn.click(); }
        });
    }
});

// ============================================================
// CLOUD CREATE FOLDER MODAL
// ============================================================

function openCloudFolderModal() {
    if (!window.storageManager || window.storageManager.currentStorage === 'native') {
        showToast('Please select a cloud storage first', 'warning');
        return;
    }

    const modal = document.getElementById('cloud-folder-modal');
    const input = document.getElementById('cloud-folder-name-input');
    const parentName = document.getElementById('cloud-folder-parent-name');

    if (!modal) return;

    if (input) input.value = '';

    if (parentName) {
        const sm = window.storageManager;
        const crumbs = sm.cloudBreadcrumbs || [];
        const currentFolder = crumbs.length > 0 ? crumbs[crumbs.length - 1].name : 'Root';
        parentName.textContent = currentFolder;
    }

    modal.classList.add('active');
    if (input) {
        input.focus();
    }
}

function closeCloudFolderModal() {
    const modal = document.getElementById('cloud-folder-modal');
    if (modal) modal.classList.remove('active');
}

async function confirmCloudFolderCreate() {
    const input = document.getElementById('cloud-folder-name-input');
    const name = input?.value?.trim();

    if (!name) {
        showToast('Please enter a folder name', 'warning');
        return;
    }

    if (!window.storageManager) return;

    await window.storageManager.createCloudFolder(name);
    closeCloudFolderModal();
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function showToast(message, type = 'info') {
    // Use existing toast system if available
    if (window.showAlert) {
        window.showAlert(message, type);
    } else if (window.showSuccess && type === 'success') {
        window.showSuccess(message);
    } else if (window.showError && type === 'error') {
        window.showError(message);
    } else {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

// ============================================================
// INTEGRATION WITH STORAGE MANAGER
// ============================================================

function enhanceCloudItemCards() {
    // DISABLED: Context menu moved to card dropdown (3-dot menu)
    // Right-click is no longer used for cloud storage items
    // All cloud management actions are now in the card-menu dropdown

    /* Original right-click implementation disabled
    const addContextMenu = () => {
        if (!window.storageManager || window.storageManager.currentStorage === 'native') {
            return;
        }

        // Folder cards
        document.querySelectorAll('.document-card.folder-card').forEach(card => {
            if (card.dataset.contextMenuBound) return;
            card.dataset.contextMenuBound = 'true';
            
            card.addEventListener('contextmenu', (e) => {
                const folderId = card.dataset.id;
                const folderName = card.querySelector('.card-title')?.textContent || '';
                showCloudContextMenu(e, { id: folderId, name: folderName }, 'folder');
            });
        });

        // File cards (for cloud storage)
        document.querySelectorAll('.document-card:not(.folder-card)').forEach(card => {
            const provider = card.dataset.provider;
            if (!provider || provider === 'native') return;
            if (card.dataset.contextMenuBound) return;
            card.dataset.contextMenuBound = 'true';
            
            card.addEventListener('contextmenu', (e) => {
                const fileId = card.dataset.id;
                const fileName = card.querySelector('.card-title')?.textContent || '';
                showCloudContextMenu(e, { id: fileId, name: fileName, provider }, 'file');
            });
        });

        // List view rows
        document.querySelectorAll('.table-row.folder-row, .table-row.document-item').forEach(row => {
            const provider = row.dataset.provider;
            if (!provider || provider === 'native') return;
            if (row.dataset.contextMenuBound) return;
            row.dataset.contextMenuBound = 'true';
            
            const isFolder = row.classList.contains('folder-row');
            
            row.addEventListener('contextmenu', (e) => {
                const itemId = row.dataset.id;
                const itemName = row.querySelector('.doc-name-cell span:last-child')?.textContent || '';
                showCloudContextMenu(e, { id: itemId, name: itemName, provider }, isFolder ? 'folder' : 'file');
            });
        });
    };

    // Run initially and observe for changes
    addContextMenu();

    // Use MutationObserver to detect when new cards are added
    const observer = new MutationObserver(() => {
        addContextMenu();
    });

    const cardView = document.getElementById('cardView');
    const tableBody = document.getElementById('documentTableBody');

    if (cardView) observer.observe(cardView, { childList: true, subtree: true });
    if (tableBody) observer.observe(tableBody, { childList: true, subtree: true });
    */
}

// ============================================================
// OVERRIDE ACTIONS FOR CLOUD STORAGE
// ============================================================

function setupCloudActionOverrides() {
    // Override the create-folder action when in cloud storage mode
    const originalHandleAction = window.handleAction;

    window.handleAction = function (action) {
        if (window.storageManager && window.storageManager.currentStorage !== 'native') {
            switch (action) {
                case 'create-folder':
                    openCloudFolderModal();
                    return;
                // Add more overrides as needed
            }
        }

        // Call original function for native storage
        if (originalHandleAction) {
            originalHandleAction(action);
        }
    };
}

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', function () {
    // Initialize context menu
    initCloudContextMenu();

    // Setup cloud action overrides
    setupCloudActionOverrides();

    // Enhance cloud item cards after a short delay
    setTimeout(() => {
        enhanceCloudItemCards();
    }, 500);

    // Setup modal button handlers
    const confirmRenameBtn = document.getElementById('confirm-cloud-rename');
    if (confirmRenameBtn) {
        confirmRenameBtn.addEventListener('click', confirmCloudRename);
    }

    const confirmDeleteBtn = document.getElementById('confirm-cloud-delete');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', confirmCloudDelete);
    }

    const confirmMoveBtn = document.getElementById('confirm-cloud-move');
    if (confirmMoveBtn) {
        confirmMoveBtn.addEventListener('click', confirmCloudMove);
    }

    const confirmFolderBtn = document.getElementById('confirm-cloud-folder-create');
    if (confirmFolderBtn) {
        confirmFolderBtn.addEventListener('click', confirmCloudFolderCreate);
    }

    // Handle Enter key in modals
    const renameInput = document.getElementById('cloud-rename-input');
    if (renameInput) {
        renameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') confirmCloudRename();
        });
    }

    const folderInput = document.getElementById('cloud-folder-name-input');
    if (folderInput) {
        folderInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') confirmCloudFolderCreate();
        });
    }

    // Close modals with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeCloudRenameModal();
            closeCloudDeleteModal();
            closeCloudFolderPicker();
            closeCloudFolderModal();
            closeCloudShareModal();
            closeCloudLinkModal();
        }
    });
});

// ============================================================
// CLOUD SHARE MODAL
// ============================================================

let shareTarget = null;
let shareTargetType = null;

// ── Multi-email pills ────────────────────────────────────────
// Los destinatarios se acumulan como pills de color (avatar = inicial del
// email); el color sale de un hash del email para que sea estable.
let sharePillEmails = [];

const SHARE_PILL_COLORS = [
    '#064CDB', '#0e7490', '#7c3aed', '#be185d', '#b45309',
    '#15803d', '#c2410c', '#4338ca', '#0f766e', '#a21caf',
];

function sharePillColor(email) {
    let hash = 0;
    for (let i = 0; i < email.length; i++) {
        hash = ((hash << 5) - hash + email.charCodeAt(i)) | 0;
    }
    return SHARE_PILL_COLORS[Math.abs(hash) % SHARE_PILL_COLORS.length];
}

function renderSharePills() {
    const box = document.getElementById('share-pillbox');
    const input = document.getElementById('share-email-input');
    if (!box || !input) return;
    box.querySelectorAll('.share-pill').forEach(p => p.remove());
    sharePillEmails.forEach(email => {
        const pill = document.createElement('span');
        pill.className = 'share-pill';
        pill.dataset.email = email;
        pill.style.setProperty('--pill-color', sharePillColor(email));
        pill.title = 'Click to edit';

        const avatar = document.createElement('span');
        avatar.className = 'share-pill-avatar';
        avatar.textContent = (email[0] || '?');

        const text = document.createElement('span');
        text.className = 'share-pill-text';
        text.textContent = email;

        const x = document.createElement('button');
        x.type = 'button';
        x.className = 'share-pill-x';
        x.setAttribute('aria-label', 'Remove ' + email);
        x.innerHTML = '<i class="bi bi-x"></i>';
        x.addEventListener('click', (e) => {
            e.stopPropagation();
            removeSharePill(email);
        });

        // Editable: click en la pill devuelve el email al input para corregirlo.
        pill.addEventListener('click', () => {
            removeSharePill(email);
            input.value = email;
            input.focus();
        });

        pill.append(avatar, text, x);
        box.insertBefore(pill, input);
    });
}

function addSharePill(raw) {
    const input = document.getElementById('share-email-input');
    const errorEl = document.getElementById('cloud-share-error');
    const box = document.getElementById('share-pillbox');
    const email = (raw || '').trim().toLowerCase().replace(/[,;]+$/, '');
    if (!email) return false;
    const valid = (typeof isValidEmail === 'function')
        ? isValidEmail(email)
        : /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    if (!valid) {
        if (box) box.classList.add('is-invalid');
        if (errorEl) {
            errorEl.textContent = `"${email}" is not a valid email address`;
            errorEl.classList.remove('d-none');
            errorEl.style.display = 'block';
        }
        return false;
    }
    if (box) box.classList.remove('is-invalid');
    if (errorEl) { errorEl.classList.add('d-none'); errorEl.style.display = ''; }
    if (!sharePillEmails.includes(email)) {
        sharePillEmails.push(email);
        renderSharePills();
    }
    if (input) input.value = '';
    return true;
}

function removeSharePill(email) {
    sharePillEmails = sharePillEmails.filter(e => e !== email);
    renderSharePills();
}

function clearSharePills() {
    sharePillEmails = [];
    renderSharePills();
}

function openCloudShareModal(item, type) {
    shareTarget = item;
    shareTargetType = type;

    const modal = document.getElementById('cloud-share-modal');
    const itemName = document.getElementById('share-item-name');
    const emailInput = document.getElementById('share-email-input');
    const messageInput = document.getElementById('share-message-input');

    if (!modal) return;

    if (itemName) itemName.textContent = item.name || 'Item';
    if (emailInput) emailInput.value = '';
    if (messageInput) messageInput.value = '';
    clearSharePills();

    modal.classList.add('active');
    loadCollaborators(item.id);

    if (emailInput) emailInput.focus();
}

function closeCloudShareModal() {
    const modal = document.getElementById('cloud-share-modal');
    if (modal) modal.classList.remove('active');
    shareTarget = null;
    shareTargetType = null;
}

async function loadCollaborators(fileId) {
    const container = document.getElementById('collaborators-list');
    if (!container || !window.storageManager) return;

    container.innerHTML = '<div class="text-muted small text-center py-2">Loading...</div>';

    try {
        const sm = window.storageManager;
        const response = await fetch(`/x_integ/storage/files/${sm.currentStorage}/shared/${fileId}`);
        const data = await response.json();

        if (data.shared_users && data.shared_users.length > 0) {
            container.innerHTML = data.shared_users.map(user => `
                <div class="d-flex align-items-center gap-2 py-2 border-bottom collaborator-item" data-id="${user.id}" data-email="${user.email || ''}">
                    <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center" style="width: 32px; height: 32px; font-size: 0.8rem;">
                        ${(user.name || user.email || '?').substring(0, 2).toUpperCase()}
                    </div>
                    <div class="flex-grow-1">
                        <div class="small fw-medium">${user.name || user.email || 'Unknown'}</div>
                        <div class="text-muted" style="font-size: 0.7rem;">${user.role || 'Viewer'}</div>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="revokeAccess('${user.id}', '${user.email || ''}')">
                        <i class="bi bi-x"></i>
                    </button>
                </div>
            `).join('');
        } else if (data.warning) {
            // Provider couldn't answer this query (e.g. Dropbox errors on
            // files with no sharing configured) — be honest about that
            // instead of implying we confirmed no one has access.
            container.innerHTML = '<div class="text-muted small text-center py-2"><i class="bi bi-info-circle"></i> Unable to load current collaborators for this file</div>';
        } else {
            container.innerHTML = '<div class="text-muted small text-center py-2">No one else has access</div>';
        }
    } catch (error) {
        console.error('Error loading collaborators:', error);
        container.innerHTML = '<div class="text-danger small text-center py-2">Error loading</div>';
    }
}

async function confirmCloudShare() {
    if (!shareTarget || !window.storageManager) return;

    const emailInput = document.getElementById('share-email-input');
    const errorEl = document.getElementById('cloud-share-error');
    const box = document.getElementById('share-pillbox');
    const role = document.getElementById('share-role-select')?.value || 'reader';
    const notify = document.getElementById('share-notify-check')?.checked ?? true;
    const message = document.getElementById('share-message-input')?.value?.trim() || '';

    const showError = (msg) => {
        if (box) box.classList.add('is-invalid');
        if (errorEl) {
            errorEl.textContent = msg;
            errorEl.classList.remove('d-none');
            errorEl.style.display = 'block';
        }
    };

    // Lo que quedó escrito en el input también cuenta (sin obligar a Enter).
    const pending = emailInput?.value?.trim();
    if (pending && !addSharePill(pending)) return;   // inválido → error ya visible

    const emails = [...sharePillEmails];
    if (!emails.length) {
        showError('Please add at least one email address');
        return;
    }
    if (box) box.classList.remove('is-invalid');
    if (errorEl) { errorEl.classList.add('d-none'); errorEl.style.display = ''; }

    const sm = window.storageManager;
    const shareBtn = document.getElementById('confirm-cloud-share');
    if (shareBtn) shareBtn.disabled = true;

    // Un POST por destinatario; se reporta el resultado agregado y las pills
    // que fallaron se conservan para reintentar.
    const failed = [];
    for (const email of emails) {
        try {
            const response = await fetch(`/x_integ/storage/share/${sm.currentStorage}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file_id: shareTarget.id,
                    email,
                    role,
                    notify,
                    message
                })
            });
            const result = await response.json();
            if (!result.success) failed.push({ email, error: result.error });
        } catch (error) {
            console.error('Share error:', email, error);
            failed.push({ email, error: 'network error' });
        }
    }

    if (shareBtn) shareBtn.disabled = false;

    const okCount = emails.length - failed.length;
    if (!failed.length) {
        showToast(okCount === 1 ? 'Shared successfully!' : `Shared with ${okCount} people!`, 'success');
        clearSharePills();
    } else {
        if (okCount > 0) showToast(`Shared with ${okCount} of ${emails.length}`, 'warning');
        showError('Could not share with: ' + failed.map(f => f.email).join(', '));
        sharePillEmails = failed.map(f => f.email);
        renderSharePills();
    }
    if (okCount > 0) loadCollaborators(shareTarget.id);
}

async function revokeAccess(permissionId, email) {
    if (!shareTarget || !window.storageManager) return;

    const sm = window.storageManager;

    try {
        const response = await fetch(`/x_integ/storage/unshare/${sm.currentStorage}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: shareTarget.id,
                permission_id: permissionId,
                email: email
            })
        });

        const result = await response.json();
        if (result.success) {
            showToast('Access revoked', 'success');
            loadCollaborators(shareTarget.id);
        } else {
            showToast(result.error || 'Failed to revoke access', 'error');
        }
    } catch (error) {
        console.error('Revoke error:', error);
        showToast('Failed to revoke access', 'error');
    }
}

// ============================================================
// CLOUD GET LINK MODAL
// ============================================================

let linkTarget = null;
let linkTargetType = null;
let currentPublicLink = null;

function openCloudLinkModal(item, type) {
    linkTarget = item;
    linkTargetType = type;
    currentPublicLink = null;

    const modal = document.getElementById('cloud-link-modal');
    const itemName = document.getElementById('link-item-name');
    const toggle = document.getElementById('public-link-toggle');
    const linkSettings = document.getElementById('link-settings');
    const noLinkMsg = document.getElementById('no-link-message');
    const removeBtn = document.getElementById('remove-link-btn');

    if (!modal) return;

    if (itemName) itemName.textContent = item.name || 'Item';
    if (toggle) toggle.checked = false;
    if (linkSettings) linkSettings.classList.add('d-none');
    if (noLinkMsg) noLinkMsg.classList.remove('d-none');
    if (removeBtn) removeBtn.classList.add('d-none');

    // Clear inputs
    document.getElementById('public-link-url').value = '';
    document.getElementById('link-expiry-input').value = '';
    document.getElementById('link-password-input').value = '';

    modal.classList.add('active');
}

function closeCloudLinkModal() {
    const modal = document.getElementById('cloud-link-modal');
    if (modal) modal.classList.remove('active');
    linkTarget = null;
    linkTargetType = null;
}

async function createPublicLink() {
    if (!linkTarget || !window.storageManager) return;

    const expiry = document.getElementById('link-expiry-input')?.value;
    const password = document.getElementById('link-password-input')?.value;
    const linkInput = document.getElementById('public-link-url');

    const sm = window.storageManager;
    linkInput.value = 'Generating...';

    try {
        const response = await fetch(`/x_integ/storage/link/${sm.currentStorage}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: linkTarget.id,
                expires_at: expiry ? new Date(expiry).toISOString() : null,
                password: password || null
            })
        });

        const result = await response.json();
        if (result.success && result.link) {
            currentPublicLink = result.link;
            linkInput.value = result.link;
            document.getElementById('remove-link-btn').classList.remove('d-none');
            showToast('Public link created!', 'success');
        } else {
            linkInput.value = '';
            showToast(result.error || 'Failed to create link', 'error');
        }
    } catch (error) {
        console.error('Link error:', error);
        linkInput.value = '';
        showToast('Failed to create link', 'error');
    }
}

async function removePublicLink() {
    if (!linkTarget || !window.storageManager) return;

    const sm = window.storageManager;

    try {
        const response = await fetch(`/x_integ/storage/link/${sm.currentStorage}/${encodeURIComponent(linkTarget.id)}`, {
            method: 'DELETE'
        });

        const result = await response.json();
        if (result.success) {
            currentPublicLink = null;
            document.getElementById('public-link-url').value = '';
            document.getElementById('public-link-toggle').checked = false;
            document.getElementById('link-settings').classList.add('d-none');
            document.getElementById('no-link-message').classList.remove('d-none');
            document.getElementById('remove-link-btn').classList.add('d-none');
            showToast('Public link removed', 'success');
        } else {
            showToast(result.error || 'Failed to remove link', 'error');
        }
    } catch (error) {
        console.error('Remove link error:', error);
        showToast('Failed to remove link', 'error');
    }
}

function flashCopyButton() {
    const btn = document.getElementById('copy-link-btn');
    if (!btn || btn.dataset.flashing) return;
    const original = btn.innerHTML;
    btn.dataset.flashing = '1';
    btn.innerHTML = '<i class="bi bi-check-lg text-success"></i>';
    setTimeout(() => { btn.innerHTML = original; delete btn.dataset.flashing; }, 1200);
}

function copyLinkToClipboard() {
    const linkInput = document.getElementById('public-link-url');
    if (linkInput && linkInput.value) {
        navigator.clipboard.writeText(linkInput.value).then(() => {
            showToast('Link copied!', 'success');
            flashCopyButton();
        }).catch(() => {
            linkInput.select();
            document.execCommand('copy');
            showToast('Link copied!', 'success');
            flashCopyButton();
        });
    }
}

// Setup link modal event listeners
document.addEventListener('DOMContentLoaded', function () {
    // Share modal
    const confirmShareBtn = document.getElementById('confirm-cloud-share');
    if (confirmShareBtn) {
        confirmShareBtn.addEventListener('click', confirmCloudShare);
    }

    // Live duplicate check: warn (don't block) when the typed email already
    // appears in the currently-loaded collaborators list.
    const shareEmailInput = document.getElementById('share-email-input');
    if (shareEmailInput) {
        shareEmailInput.addEventListener('input', debounce(function () {
            const email = this.value.trim().toLowerCase();
            const errorEl = document.getElementById('cloud-share-error');
            const hintEl = document.getElementById('cloud-share-already-has-access');
            const box = document.getElementById('share-pillbox');
            if (box) box.classList.remove('is-invalid');
            if (errorEl) { errorEl.classList.add('d-none'); errorEl.style.display = ''; }

            const match = email && document.querySelector(`#collaborators-list [data-email="${CSS.escape(email)}" i]`);
            if (hintEl) hintEl.classList.toggle('d-none', !match);
        }, 300));

        // Pills: Enter/coma/; confirman el email; Backspace con el input vacío
        // recupera la última pill para editarla; blur confirma lo pendiente.
        shareEmailInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ',' || e.key === ';') {
                e.preventDefault();
                addSharePill(this.value);
            } else if (e.key === 'Backspace' && !this.value && sharePillEmails.length) {
                const last = sharePillEmails[sharePillEmails.length - 1];
                removeSharePill(last);
                this.value = last;
                e.preventDefault();
            }
        });
        shareEmailInput.addEventListener('blur', function () {
            if (this.value.trim()) addSharePill(this.value);
        });
        // Pegar una lista "a@x.com, b@y.com; c@z.com" crea una pill por email.
        shareEmailInput.addEventListener('paste', function (e) {
            const text = (e.clipboardData || window.clipboardData)?.getData('text') || '';
            if (/[,;\s]/.test(text.trim())) {
                e.preventDefault();
                text.split(/[,;\s]+/).forEach(part => part && addSharePill(part));
            }
        });
    }

    // Click en cualquier parte de la caja → enfocar el input de email.
    const sharePillbox = document.getElementById('share-pillbox');
    if (sharePillbox) {
        sharePillbox.addEventListener('click', function (e) {
            if (e.target === this) shareEmailInput?.focus();
        });
    }

    // Icono del selector de permiso acompaña la opción elegida (sin emojis).
    const roleSelect = document.getElementById('share-role-select');
    if (roleSelect) {
        roleSelect.addEventListener('change', function () {
            const icon = document.getElementById('share-role-icon');
            const opt = this.options[this.selectedIndex];
            if (icon && opt) icon.className = 'bi ' + (opt.dataset.icon || 'bi-eye') + ' share-role-icon';
        });
    }

    // Link toggle
    const linkToggle = document.getElementById('public-link-toggle');
    if (linkToggle) {
        linkToggle.addEventListener('change', function () {
            const linkSettings = document.getElementById('link-settings');
            const noLinkMsg = document.getElementById('no-link-message');

            if (this.checked) {
                linkSettings.classList.remove('d-none');
                noLinkMsg.classList.add('d-none');
                createPublicLink();
            } else {
                removePublicLink();
            }
        });
    }

    // Copy link button
    const copyBtn = document.getElementById('copy-link-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', copyLinkToClipboard);
    }

    // Remove link button
    const removeBtn = document.getElementById('remove-link-btn');
    if (removeBtn) {
        removeBtn.addEventListener('click', removePublicLink);
    }
});

// Export functions for global access
window.showCloudContextMenu = showCloudContextMenu;
window.hideCloudContextMenu = hideCloudContextMenu;
window.openCloudRenameModal = openCloudRenameModal;
window.closeCloudRenameModal = closeCloudRenameModal;
window.openCloudDeleteModal = openCloudDeleteModal;
window.closeCloudDeleteModal = closeCloudDeleteModal;
window.openCloudFolderPicker = openCloudFolderPicker;
window.closeCloudFolderPicker = closeCloudFolderPicker;
window.openCloudFolderModal = openCloudFolderModal;
window.closeCloudFolderModal = closeCloudFolderModal;
window.openCloudShareModal = openCloudShareModal;
window.closeCloudShareModal = closeCloudShareModal;
window.openCloudLinkModal = openCloudLinkModal;
window.closeCloudLinkModal = closeCloudLinkModal;
window.revokeAccess = revokeAccess;
window.enhanceCloudItemCards = enhanceCloudItemCards;
