// ── Confirm modal reutilizable (Trash / Archived / Auto-Archived) ─────────────
// Modal profesional con el estándar visual del proyecto (confirm_modal.css,
// mismo lenguaje que el modal de logout). Reemplaza los confirm() nativos y
// agrega confirmación a las acciones de restaurar. Devuelve Promise<boolean>.
//
//   xpConfirm({ variant:'danger'|'restore', title, message, confirmLabel,
//               confirmIcon })  →  Promise<true|false>
(function () {
  var current = null; // { overlay, resolve, onKey }

  function build() {
    var overlay = document.createElement('div');
    overlay.className = 'xpc-overlay';
    overlay.innerHTML =
      '<div class="xpc-container" role="dialog" aria-modal="true">' +
        '<div class="xpc-header">' +
          '<div class="xpc-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></svg></div>' +
          '<h3 class="xpc-title"></h3>' +
          '<p class="xpc-message"></p>' +
        '</div>' +
        '<div class="xpc-footer">' +
          '<button type="button" class="xpc-btn xpc-btn-cancel"><i class="bi bi-x-square"></i> Cancel</button>' +
          '<button type="button" class="xpc-btn xpc-btn-action"></button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(overlay);
    return overlay;
  }

  var ICONS = {
    danger:  '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6"/><path d="M14 11v6"/>',
    restore: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>'
  };

  function close(result) {
    if (!current) return;
    var c = current; current = null;
    c.overlay.classList.remove('active');
    document.removeEventListener('keydown', c.onKey);
    var r = c.resolve;
    setTimeout(function () { r(result); }, 200); // esperar la transición
  }

  window.xpConfirm = function (opts) {
    opts = opts || {};
    var variant = opts.variant === 'restore' ? 'restore' : 'danger';
    return new Promise(function (resolve) {
      // Si ya hay uno abierto, resolver el anterior como cancelado.
      if (current) close(false);

      var overlay = window.__xpcOverlay || (window.__xpcOverlay = build());
      overlay.className = 'xpc-overlay xpc-overlay--' + variant;

      overlay.querySelector('.xpc-icon svg').innerHTML = ICONS[variant];
      overlay.querySelector('.xpc-title').textContent = opts.title || (variant === 'restore' ? 'Restore item' : 'Delete item');
      overlay.querySelector('.xpc-message').textContent = opts.message || '';

      var actionBtn = overlay.querySelector('.xpc-btn-action');
      actionBtn.className = 'xpc-btn xpc-btn-action ' + (variant === 'restore' ? 'xpc-btn-restore' : 'xpc-btn-danger');
      var icon = opts.confirmIcon ? '<i class="bi ' + opts.confirmIcon + '"></i> ' : '';
      actionBtn.innerHTML = icon + (opts.confirmLabel || (variant === 'restore' ? 'Restore' : 'Delete'));

      var cancelBtn = overlay.querySelector('.xpc-btn-cancel');
      var containerClick = function (e) { if (e.target === overlay) close(false); };
      var onKey = function (e) { if (e.key === 'Escape') close(false); };

      actionBtn.onclick = function () { close(true); };
      cancelBtn.onclick = function () { close(false); };
      overlay.onclick = containerClick;
      document.addEventListener('keydown', onKey);

      current = { overlay: overlay, resolve: resolve, onKey: onKey };
      // Forzar reflow para que la transición de entrada corra.
      // eslint-disable-next-line no-unused-expressions
      overlay.offsetWidth;
      overlay.classList.add('active');
    });
  };
})();

// ── Profile dropdown ──────────────────────────────────────────────────────────
const profile = document.querySelector('.profile__btn');
const dropdown = document.querySelector('.dropdown__wrapper_bar');

if (profile && dropdown) {
  profile.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.remove('none');
    dropdown.classList.toggle('hide');
  });

  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target) && !profile.contains(e.target)) {
      dropdown.classList.add('hide');
    }
  });
}

// ── Sidebar panel toggle ──────────────────────────────────────────────────────
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebarPanel  = document.getElementById('sidebarPanel');
const mainDashboard = document.getElementById('mainDashboard');

if (sidebarToggle && sidebarPanel && mainDashboard) {
  sidebarToggle.addEventListener('click', () => {
    const isCollapsed = sidebarPanel.classList.toggle('collapsed');
    mainDashboard.style.setProperty('--sidebar-w', isCollapsed ? '68px' : '230px');
    sidebarToggle.setAttribute('aria-expanded', String(!isCollapsed));
  });
}

// ── Sidebar item: Trash → open trash offcanvas ─────────────────────────────
document.getElementById('sidebarItemTrash')?.addEventListener('click', () => {
  openTrashOc();
});

// ── Trash offcanvas ────────────────────────────────────────────────────────
function _trashItemHtml(item) {
  var isFolder = item.item_type === 'folder';
  var name     = isFolder ? (item.name || 'Unnamed folder') : (item.original_filename || item.name || 'Unnamed');
  var iconClass = isFolder ? 'xp-arc-icon--folder' : '';
  var iconSvg   = isFolder
    ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m6 14 1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18a2 2 0 0 1 2 2v2"/></svg>'
    : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>';
  var iconColor = isFolder ? '#fbbf24' : _fileIcon(item.mime_type);
  var size = (!isFolder && item.size) ? _fmtBytes(item.size) : '';
  var type = item.item_type || 'file';

  return `
    <div class="xp-arc-item" data-id="${item.id}" data-type="${type}">
      <div class="xp-arc-icon ${iconClass}" style="${isFolder ? '' : 'background:' + iconColor + '18;'}">
        ${iconSvg.replace('stroke="currentColor"', 'stroke="' + iconColor + '"')}
      </div>
      <div class="xp-arc-meta">
        <div class="xp-arc-name" title="${name}">${name}</div>
        <div class="xp-arc-info">${isFolder ? 'Folder' : (size || 'File')}</div>
      </div>
      <div class="xp-arc-actions">
        <button class="xp-arc-btn xp-arc-btn--restore" title="Restore"
          onclick="restoreTrashItem(${item.id},'${type}',this)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>
          </svg>
        </button>
        <button class="xp-arc-btn xp-arc-btn--trash" title="Delete permanently"
          onclick="deleteTrashItem(${item.id},'${type}',this)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      </div>
    </div>`;
}

function _renderTrashOc(folders, files) {
  var body  = document.getElementById('trashOcBody');
  var count = document.getElementById('trashOcCount');
  if (!body) return;

  var all = folders.map(function(f) { return Object.assign({}, f, { item_type: 'folder' }); })
    .concat(files.map(function(f) { return Object.assign({}, f, { item_type: 'file' }); }));

  if (all.length === 0) {
    body.innerHTML = `
      <div class="xp-oc-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
          <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        </svg>
        <span>Trash is empty</span>
      </div>`;
    if (count) count.textContent = '0 items';
    return;
  }
  body.innerHTML = all.map(_trashItemHtml).join('');
  if (count) count.textContent = all.length + ' item' + (all.length !== 1 ? 's' : '');
}

function openTrashOc() {
  var overlay = document.getElementById('trashOcOverlay');
  var oc      = document.getElementById('trashOc');
  var body    = document.getElementById('trashOcBody');
  if (!oc) return;

  overlay && overlay.classList.add('open');
  oc.classList.add('open');
  document.body.style.overflow = 'hidden';

  if (body) body.innerHTML = '<div class="xp-oc-loading"><div class="xp-oc-spinner xp-oc-spinner--red"></div><span>Loading…</span></div>';

  window.fetch('/x_doc/folders?trash=true')
    .then(function(r) { return r.ok ? r.json() : null; })
    .then(function(data) {
      if (data) _renderTrashOc(data.folders || [], data.files || []);
    })
    .catch(function() {
      if (body) body.innerHTML = '<div class="xp-oc-empty"><span>Error loading trash</span></div>';
    });
}

function closeTrashOc() {
  var overlay = document.getElementById('trashOcOverlay');
  var oc      = document.getElementById('trashOc');
  overlay && overlay.classList.remove('open');
  oc && oc.classList.remove('open');
  document.body.style.overflow = '';
}

function restoreTrashItem(id, type, btn) {
  xpConfirm({
    variant: 'restore',
    title: 'Restore item',
    message: 'This item will be moved back to your documents.',
    confirmLabel: 'Restore', confirmIcon: 'bi-arrow-counterclockwise'
  }).then(function(ok) {
    if (!ok) return;
    if (btn) btn.disabled = true;
    window.fetch('/x_doc/organize/restore', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: id, type: type })
    }).then(function(r) {
      if (r.ok) {
        var el = document.querySelector('#trashOcBody .xp-arc-item[data-id="' + id + '"][data-type="' + type + '"]');
        _removeTrashEl(el);
        if (window.refreshSidebarCounts) window.refreshSidebarCounts();
        if (window._listCacheClear) window._listCacheClear('native');
      } else { if (btn) btn.disabled = false; }
    }).catch(function() { if (btn) btn.disabled = false; });
  });
}

function deleteTrashItem(id, type, btn) {
  xpConfirm({
    variant: 'danger',
    title: 'Delete permanently',
    message: 'This item will be permanently deleted. This action cannot be undone.',
    confirmLabel: 'Delete', confirmIcon: 'bi-trash'
  }).then(function(ok) {
    if (!ok) return;
    if (btn) btn.disabled = true;
    window.fetch('/x_doc/organize/permanent-delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: id, type: type })
    }).then(function(r) {
      if (r.ok) {
        var el = document.querySelector('#trashOcBody .xp-arc-item[data-id="' + id + '"][data-type="' + type + '"]');
        _removeTrashEl(el);
        if (window.refreshSidebarCounts) window.refreshSidebarCounts();
      } else { if (btn) btn.disabled = false; }
    }).catch(function() { if (btn) btn.disabled = false; });
  });
}

function _removeTrashEl(el) {
  if (!el) return;
  el.style.transition = 'opacity .22s, transform .22s';
  el.style.opacity = '0';
  el.style.transform = 'translateX(20px)';
  setTimeout(function() {
    el.remove();
    var remaining = document.querySelectorAll('#trashOcBody .xp-arc-item').length;
    var count = document.getElementById('trashOcCount');
    if (count) count.textContent = remaining + ' item' + (remaining !== 1 ? 's' : '');
    if (remaining === 0) _renderTrashOc([], []);
  }, 240);
}

// expose globally so clean_javascript.js can call openTrashOc()
window.openTrashOc  = openTrashOc;
window.closeTrashOc = closeTrashOc;

// ── Sidebar item: Archive → open offcanvas ─────────────────────────────────
document.getElementById('sidebarItemArchive')?.addEventListener('click', () => {
  openArchivedOc();
});

// ── Archived offcanvas helpers ─────────────────────────────────────────────
function _fmtBytes(b) {
  if (!b) return '—';
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
  return (b / 1048576).toFixed(1) + ' MB';
}

function _fileIcon(mime) {
  if (!mime) return '#6b7280';
  if (mime.includes('pdf'))  return '#ef4444';
  if (mime.includes('word') || mime.includes('docx')) return '#3b82f6';
  if (mime.includes('text')) return '#10b981';
  return '#fbbf24';
}

function _arcItemHtml(f) {
  var daysLeft = f.days_left;
  var expiryLabel = daysLeft === null ? '' : (daysLeft === 0 ? 'Expires today' : daysLeft + 'd left');
  var urgentClass = daysLeft !== null && daysLeft <= 2 ? ' urgent' : '';
  var iconColor = _fileIcon(f.mime_type);
  var size = _fmtBytes(f.size);
  return `
    <div class="xp-arc-item" data-id="${f.id}">
      <div class="xp-arc-icon" style="background:${iconColor}18;">
        <svg viewBox="0 0 24 24" fill="none" stroke="${iconColor}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
          <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
        </svg>
      </div>
      <div class="xp-arc-meta">
        <div class="xp-arc-name" title="${f.name}">${f.name}</div>
        <div class="xp-arc-info">${size}</div>
      </div>
      ${expiryLabel ? `<span class="xp-arc-expiry${urgentClass}">${expiryLabel}</span>` : ''}
      <div class="xp-arc-actions">
        <button class="xp-arc-btn xp-arc-btn--restore" title="Restore" onclick="restoreArchivedFile(${f.id}, this)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>
          </svg>
        </button>
        <button class="xp-arc-btn xp-arc-btn--trash" title="Move to trash" onclick="trashArchivedFile(${f.id}, this)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      </div>
    </div>`;
}

function _renderArchivedOc(files) {
  var body = document.getElementById('archivedOcBody');
  var count = document.getElementById('archivedOcCount');
  if (!body) return;

  if (!files || files.length === 0) {
    body.innerHTML = `
      <div class="xp-oc-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect width="20" height="5" x="2" y="3" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/></svg>
        <span>No archived files</span>
      </div>`;
    if (count) count.textContent = '0 files';
    return;
  }
  body.innerHTML = files.map(_arcItemHtml).join('');
  if (count) count.textContent = files.length + ' file' + (files.length !== 1 ? 's' : '');
}

function openArchivedOc() {
  var overlay = document.getElementById('archivedOcOverlay');
  var oc = document.getElementById('archivedOc');
  var body = document.getElementById('archivedOcBody');
  if (!oc) return;

  overlay && overlay.classList.add('open');
  oc.classList.add('open');
  document.body.style.overflow = 'hidden';

  // Show spinner while loading
  if (body) body.innerHTML = '<div class="xp-oc-loading"><div class="xp-oc-spinner"></div><span>Loading…</span></div>';

  fetch('/x_buck/api/archived')
    .then(function(r) { return r.ok ? r.json() : null; })
    .then(function(data) { if (data) _renderArchivedOc(data.files); })
    .catch(function() {
      if (body) body.innerHTML = '<div class="xp-oc-empty"><span>Error loading files</span></div>';
    });
}

function closeArchivedOc() {
  var overlay = document.getElementById('archivedOcOverlay');
  var oc = document.getElementById('archivedOc');
  overlay && overlay.classList.remove('open');
  oc && oc.classList.remove('open');
  document.body.style.overflow = '';
}

function restoreArchivedFile(id, btn) {
  xpConfirm({
    variant: 'restore',
    title: 'Restore file',
    message: 'This file will be moved back to your documents as a draft.',
    confirmLabel: 'Restore', confirmIcon: 'bi-arrow-counterclockwise'
  }).then(function(ok) {
    if (!ok) return;
    if (btn) btn.disabled = true;
    fetch('/x_doc/files/' + id + '/status', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'Borrador' })
    }).then(function(r) {
      if (r.ok) {
        var item = document.querySelector('.xp-arc-item[data-id="' + id + '"]');
        if (item) {
          item.style.transition = 'opacity .25s, transform .25s';
          item.style.opacity = '0';
          item.style.transform = 'translateX(20px)';
          setTimeout(function() { item.remove(); _updateOcCount(); }, 260);
        }
        if (window.refreshSidebarCounts) window.refreshSidebarCounts();
        if (window._listCacheClear) window._listCacheClear('native');
      } else {
        if (btn) btn.disabled = false;
      }
    }).catch(function() { if (btn) btn.disabled = false; });
  });
}

function trashArchivedFile(id, btn) {
  xpConfirm({
    variant: 'danger',
    title: 'Move to trash',
    message: 'This file will be moved to Trash, where it is permanently deleted after 30 days.',
    confirmLabel: 'Move to trash', confirmIcon: 'bi-trash'
  }).then(function(ok) {
    if (!ok) return;
    if (btn) btn.disabled = true;
    fetch('/x_doc/organize/trash', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: id, type: 'file' })
    }).then(function(r) {
      if (r.ok) {
        var item = document.querySelector('.xp-arc-item[data-id="' + id + '"]');
        if (item) {
          item.style.transition = 'opacity .25s, transform .25s';
          item.style.opacity = '0';
          item.style.transform = 'translateX(-20px)';
          setTimeout(function() { item.remove(); _updateOcCount(); }, 260);
        }
        if (window.refreshSidebarCounts) window.refreshSidebarCounts();
      } else {
        if (btn) btn.disabled = false;
      }
    }).catch(function() { if (btn) btn.disabled = false; });
  });
}

function _updateOcCount() {
  var items = document.querySelectorAll('#archivedOcBody .xp-arc-item');
  var count = document.getElementById('archivedOcCount');
  var n = items.length;
  if (count) count.textContent = n + ' file' + (n !== 1 ? 's' : '');
  if (n === 0) _renderArchivedOc([]);
}

// ── Auto-Archive offcanvas helpers (independent from the manual Archive panel above) ──
function _fmtCountdown(deleteAtIso) {
  if (!deleteAtIso) return '';
  var ms = new Date(deleteAtIso) - new Date();
  if (ms <= 0) return 'Deleting soon';
  var days = Math.floor(ms / 86400000);
  if (days >= 1) return days + 'd left';
  var hours = Math.floor(ms / 3600000);
  if (hours >= 1) return hours + 'h left';
  return Math.max(1, Math.floor(ms / 60000)) + 'm left';
}

function _autoArcItemHtml(f) {
  var countdown = _fmtCountdown(f.auto_archive_delete_at);
  var ms = f.auto_archive_delete_at ? (new Date(f.auto_archive_delete_at) - new Date()) : null;
  var urgentClass = (ms !== null && ms <= 172800000) ? ' urgent' : ''; // <= 2 days
  var iconColor = _fileIcon(f.mime_type);
  var size = _fmtBytes(f.size);
  return `
    <div class="xp-arc-item xp-arc-item--stack" data-id="${f.id}">
      <div class="xp-arc-top">
        <div class="xp-arc-icon" style="background:${iconColor}18;" onclick="_toggleAutoArchiveDetails(${f.id}, this)">
          <svg viewBox="0 0 24 24" fill="none" stroke="${iconColor}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
            <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
          </svg>
        </div>
        <div class="xp-arc-meta" onclick="_toggleAutoArchiveDetails(${f.id}, this)">
          <div class="xp-arc-name" title="${f.name}">${f.name}</div>
          <div class="xp-arc-info">${size}</div>
        </div>
        ${countdown ? `<span class="xp-arc-expiry${urgentClass}">${countdown}</span>` : ''}
        <div class="xp-arc-actions">
          <button class="xp-arc-btn xp-arc-btn--restore" title="Restore" onclick="restoreAutoArchivedFile(${f.id}, this)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>
            </svg>
          </button>
          <a class="xp-arc-btn xp-arc-btn--download" title="Download" href="/x_buck/api/files/${f.id}/download">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </a>
          <button class="xp-arc-btn xp-arc-btn--trash" title="Delete now" onclick="deleteNowAutoArchivedFile(${f.id}, this)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
              <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
        </div>
      </div>
      <div class="xp-arc-details" id="autoArcDetails${f.id}" style="display:none;"></div>
    </div>`;
}

function _toggleAutoArchiveDetails(id, rowEl) {
  var box = document.getElementById('autoArcDetails' + id);
  if (!box) return;
  var isOpen = box.style.display !== 'none';
  if (isOpen) { box.style.display = 'none'; return; }

  box.style.display = 'block';
  if (box.dataset.loaded === '1') return;
  box.innerHTML = '<div class="xp-arc-details-loading">Loading details…</div>';

  fetch('/x_doc/history/file/' + id)
    .then(function(r) { return r.ok ? r.json() : null; })
    .then(function(data) {
      var rows = (data && data.history) || [];
      if (rows.length === 0) {
        box.innerHTML = '<div class="xp-arc-details-empty">No history yet.</div>';
        return;
      }
      box.innerHTML = rows.map(function(h) {
        return '<div class="xp-arc-details-row"><span class="xp-arc-details-action">' + h.action + '</span>' +
          '<span class="xp-arc-details-date">' + (h.date || '') + '</span></div>';
      }).join('');
      box.dataset.loaded = '1';
    })
    .catch(function() { box.innerHTML = '<div class="xp-arc-details-empty">Could not load details.</div>'; });
}

function _renderAutoArchiveOc(files) {
  var body = document.getElementById('autoArchiveOcBody');
  var count = document.getElementById('autoArchiveOcCount');
  if (!body) return;

  if (!files || files.length === 0) {
    body.innerHTML = `
      <div class="xp-oc-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
        <span>No auto-archived files</span>
      </div>`;
    if (count) count.textContent = '0 files';
    return;
  }
  body.innerHTML = files.map(_autoArcItemHtml).join('');
  if (count) count.textContent = files.length + ' file' + (files.length !== 1 ? 's' : '');
}

function openAutoArchiveOc() {
  var overlay = document.getElementById('autoArchiveOcOverlay');
  var oc = document.getElementById('autoArchiveOc');
  var body = document.getElementById('autoArchiveOcBody');
  if (!oc) return;

  overlay && overlay.classList.add('open');
  oc.classList.add('open');
  document.body.style.overflow = 'hidden';

  if (body) body.innerHTML = '<div class="xp-oc-loading"><div class="xp-oc-spinner"></div><span>Loading…</span></div>';

  fetch('/x_doc/auto-archive/files')
    .then(function(r) { return r.ok ? r.json() : null; })
    .then(function(data) { if (data) _renderAutoArchiveOc(data.files); })
    .catch(function() {
      if (body) body.innerHTML = '<div class="xp-oc-empty"><span>Error loading files</span></div>';
    });
}

function closeAutoArchiveOc() {
  var overlay = document.getElementById('autoArchiveOcOverlay');
  var oc = document.getElementById('autoArchiveOc');
  overlay && overlay.classList.remove('open');
  oc && oc.classList.remove('open');
  document.body.style.overflow = '';
}

function restoreAutoArchivedFile(id, btn) {
  xpConfirm({
    variant: 'restore',
    title: 'Restore file',
    message: 'This file will be moved back to your documents.',
    confirmLabel: 'Restore', confirmIcon: 'bi-arrow-counterclockwise'
  }).then(function(ok) {
    if (!ok) return;
    if (btn) btn.disabled = true;
    fetch('/x_doc/auto-archive/files/' + id + '/restore', { method: 'POST' })
      .then(function(r) {
        if (r.ok) {
          var item = document.querySelector('#autoArchiveOcBody .xp-arc-item[data-id="' + id + '"]');
          if (item) {
            item.style.transition = 'opacity .25s, transform .25s';
            item.style.opacity = '0';
            item.style.transform = 'translateX(20px)';
            setTimeout(function() { item.remove(); _updateAutoArchiveOcCount(); }, 260);
          }
          if (window.refreshSidebarCounts) window.refreshSidebarCounts();
          if (window._listCacheClear) window._listCacheClear('native');
        } else { if (btn) btn.disabled = false; }
      }).catch(function() { if (btn) btn.disabled = false; });
  });
}

function deleteNowAutoArchivedFile(id, btn) {
  xpConfirm({
    variant: 'danger',
    title: 'Delete permanently',
    message: 'This document will be permanently deleted now. This action cannot be undone.',
    confirmLabel: 'Delete', confirmIcon: 'bi-trash'
  }).then(function(ok) {
    if (!ok) return;
    if (btn) btn.disabled = true;
    fetch('/x_doc/auto-archive/files/' + id + '/delete-now', { method: 'POST' })
      .then(function(r) {
        if (r.ok) {
          var item = document.querySelector('#autoArchiveOcBody .xp-arc-item[data-id="' + id + '"]');
          if (item) {
            item.style.transition = 'opacity .25s, transform .25s';
            item.style.opacity = '0';
            item.style.transform = 'translateX(-20px)';
            setTimeout(function() { item.remove(); _updateAutoArchiveOcCount(); }, 260);
          }
          if (window.refreshSidebarCounts) window.refreshSidebarCounts();
        } else { if (btn) btn.disabled = false; }
      }).catch(function() { if (btn) btn.disabled = false; });
  });
}

function _updateAutoArchiveOcCount() {
  var items = document.querySelectorAll('#autoArchiveOcBody .xp-arc-item');
  var count = document.getElementById('autoArchiveOcCount');
  var n = items.length;
  if (count) count.textContent = n + ' file' + (n !== 1 ? 's' : '');
  if (n === 0) _renderAutoArchiveOc([]);
}

window.openAutoArchiveOc = openAutoArchiveOc;
window.closeAutoArchiveOc = closeAutoArchiveOc;

// Close offcanvases on Escape
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { closeTrashOc(); closeArchivedOc(); closeAutoArchiveOc(); }
});
