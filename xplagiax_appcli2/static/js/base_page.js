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
}

function deleteTrashItem(id, type, btn) {
  if (!confirm('Permanently delete this item? This cannot be undone.')) return;
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
}

function trashArchivedFile(id, btn) {
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
}

function _updateOcCount() {
  var items = document.querySelectorAll('#archivedOcBody .xp-arc-item');
  var count = document.getElementById('archivedOcCount');
  var n = items.length;
  if (count) count.textContent = n + ' file' + (n !== 1 ? 's' : '');
  if (n === 0) _renderArchivedOc([]);
}

// Close offcanvases on Escape
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') { closeTrashOc(); closeArchivedOc(); }
});
