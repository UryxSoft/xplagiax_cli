(function () {
  var SESSION_KEY = 'xpx_sc';
  var CLIENT_TTL  = 60000; // 1-minute client-side cache (server has 5-min TTL)

  function setBadge(id, n) {
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = n;
    el.dataset.empty = (n === 0) ? 'true' : 'false';
  }

  function apply(data) {
    setBadge('countAll',        data.total        || 0);
    setBadge('realArchivedCount', data.archived   || 0);
    setBadge('archivedCount',   data.trash        || 0);
    setBadge('countNewFiles',   data.new_files    || 0);
    setBadge('countNewFolders', data.new_folders  || 0);
    setBadge('countSharedToMe', data.shared_to_me || 0);
    setBadge('countSharedWith', data.shared_by_me || 0);
  }

  function fetch(force) {
    if (!force) {
      try {
        var raw = sessionStorage.getItem(SESSION_KEY);
        if (raw) {
          var parsed = JSON.parse(raw);
          if (Date.now() - parsed.ts < CLIENT_TTL) {
            apply(parsed.data);
            return;
          }
        }
      } catch (e) {}
    }

    window.fetch('/x_buck/api/sidebar-counts')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        try { sessionStorage.setItem(SESSION_KEY, JSON.stringify({ ts: Date.now(), data: data })); } catch (e) {}
        apply(data);
      })
      .catch(function () {});
  }

  window.refreshSidebarCounts = function () { fetch(true); };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { fetch(false); });
  } else {
    fetch(false);
  }
})();
