/* ════════════════════════════════════════════════════════════════
   XPLAGIAX · HOME DASHBOARD engine
   masonry layout · animated counters · slider · rotating content
═══════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* ───────────────────────── MASONRY (variable-width bin packing) ─────────────────────────
     Cards are absolutely positioned. Each card has a width span (w1..w6) read from its class.
     We place each card, in DOM order, into the column range that sits highest up (shortest),
     which produces a tightly packed, gap-minimized board. */
  function layout() {
    var grid = document.getElementById('hdBento');
    if (!grid) return;
    var hd = document.querySelector('.hd');
    var N = parseInt(getComputedStyle(hd).getPropertyValue('--hd-cols'), 10) || 6;
    var gap = parseInt(getComputedStyle(hd).getPropertyValue('--hd-gap'), 10) || 18;
    var W = grid.clientWidth;
    if (W <= 0) return;
    var colW = (W - (N - 1) * gap) / N;
    var colH = [];
    for (var i = 0; i < N; i++) colH.push(0);

    var cards = Array.prototype.slice.call(grid.querySelectorAll('.hd-card'));
    // clear any stale height before measuring natural card heights (uniform gaps, no stretching)
    cards.forEach(function (card) { card.style.height = ''; });

    cards.forEach(function (card) {
      var m = card.className.match(/\bw(\d+)\b/);
      var span = Math.min(N, m ? parseInt(m[1], 10) : 1);

      // place into the column range that sits highest up (shortest), then leftmost → balanced columns
      var bestCol = 0, bestY = Infinity;
      for (var c = 0; c <= N - span; c++) {
        var y = 0;
        for (var k = c; k < c + span; k++) if (colH[k] > y) y = colH[k];
        if (y < bestY - 0.5) { bestY = y; bestCol = c; }
      }

      var x = Math.round(bestCol * (colW + gap));
      card.style.width = (span * colW + (span - 1) * gap) + 'px';
      card.style.left = x + 'px';
      card.style.top = Math.round(bestY) + 'px';

      var h = card.offsetHeight; // ignores reveal transform → stable
      var newY = bestY + h + gap; // uniform gap below every card
      for (var k2 = bestCol; k2 < bestCol + span; k2++) colH[k2] = newY;
    });

    var maxH = 0;
    for (var j = 0; j < N; j++) if (colH[j] > maxH) maxH = colH[j];
    grid.style.height = (maxH - gap > 0 ? maxH - gap : maxH) + 'px';
  }
  var _t;
  function relayout() { clearTimeout(_t); _t = setTimeout(layout, 60); }
  window.addEventListener('resize', relayout);
  window.addEventListener('load', function () { layout(); });
  window.hdRelayout = relayout;

  /* ───────────────────────── COUNTERS ───────────────────────── */
  function animateCount(el) {
    if (el.dataset.done) return;
    el.dataset.done = '1';
    var target = parseFloat(el.dataset.count || '0');
    var dec = parseInt(el.dataset.decimals || '0', 10);
    var suffix = el.dataset.suffix || '';
    var prefix = el.dataset.prefix || '';
    var dur = 1400, start = performance.now();
    function tick(now) {
      var p = Math.min(1, (now - start) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      var val = target * eased;
      el.textContent = prefix + val.toLocaleString('en-US', {
        minimumFractionDigits: dec, maximumFractionDigits: dec
      }) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  function fillBars() {
    document.querySelectorAll('[data-bar]').forEach(function (b) {
      setTimeout(function () { b.style.width = b.dataset.bar + '%'; }, 120);
    });
    document.querySelectorAll('.hd-spark > i[data-h]').forEach(function (s, i) {
      setTimeout(function () { s.style.height = s.dataset.h + '%'; }, 120 + i * 60);
    });
  }

  /* ───────────────────────── SLIDER ───────────────────────── */
  function initSlider() {
    var slides = Array.prototype.slice.call(document.querySelectorAll('.hd-slide'));
    var dotsWrap = document.getElementById('hdSliderDots');
    if (!slides.length) return;
    var i = 0, timer;
    slides.forEach(function (_, idx) {
      var d = document.createElement('i');
      if (idx === 0) d.className = 'on';
      d.addEventListener('click', function () { go(idx); reset(); });
      dotsWrap && dotsWrap.appendChild(d);
    });
    function go(n) {
      slides[i].classList.remove('is-active');
      dotsWrap && dotsWrap.children[i] && dotsWrap.children[i].classList.remove('on');
      i = (n + slides.length) % slides.length;
      slides[i].classList.add('is-active');
      dotsWrap && dotsWrap.children[i] && dotsWrap.children[i].classList.add('on');
    }
    function reset() { clearInterval(timer); timer = setInterval(function () { go(i + 1); }, 5000); }
    slides[0].classList.add('is-active');
    reset();
  }

  /* ───────────────────────── ROTATOR (tips / facts) ───────────────────────── */
  function initRotator(textId, dotsId, items, interval) {
    var txt = document.getElementById(textId);
    var dots = document.getElementById(dotsId);
    if (!txt || !items.length) return;
    var i = 0;
    if (dots) items.forEach(function (_, idx) {
      var d = document.createElement('i'); if (idx === 0) d.className = 'on'; dots.appendChild(d);
    });
    txt.textContent = items[0];
    setInterval(function () {
      txt.classList.add('swap');
      setTimeout(function () {
        if (dots) dots.children[i] && dots.children[i].classList.remove('on');
        i = (i + 1) % items.length;
        txt.textContent = items[i];
        if (dots) dots.children[i] && dots.children[i].classList.add('on');
        txt.classList.remove('swap');
        relayout();
      }, 400);
    }, interval);
  }

  /* ───────────────────────── CONTENT DATA ───────────────────────── */
  var SCENES = [
    'linear-gradient(135deg,#1b3a6b,#2f7bff)',
    'linear-gradient(135deg,#0a4d68,#1fd0e0)',
    'linear-gradient(135deg,#1d5e46,#19c37d)',
    'linear-gradient(135deg,#3a2a6b,#8b6dff)',
    'linear-gradient(135deg,#5e2440,#ff5d7a)',
    'linear-gradient(135deg,#5e451d,#ffb340)'
  ];
  function scene(i) { return SCENES[i % SCENES.length]; }

  var IMG = '/static/img/hd/';
  var BLOG = [
    { cat: 'AI Detection', title: 'How modern AI text detectors read perplexity and burstiness', sum: 'A practical look at the statistical signals that separate human prose from machine-generated text, and why context windows matter.', read: '6 min read', img: IMG + 'ai-detect.webp' },
    { cat: 'Academic Integrity', title: 'Citing AI assistance: the emerging standards for 2025', sum: 'Universities are converging on disclosure norms. Here is how to document AI use transparently without undermining your work.', read: '4 min read', img: IMG + 'research.webp' },
    { cat: 'Research', title: 'Stylometry 101: writing fingerprints in scholarly work', sum: 'Sentence rhythm, vocabulary richness and function-word frequency reveal authorship. We break down the core metrics.', read: '7 min read', img: IMG + 'university.webp' },
    { cat: 'Plagiarism', title: 'Semantic vs. literal matching: beyond copy-paste detection', sum: 'Paraphrased plagiarism evades string matching. Embedding-based comparison catches meaning, not just words.', read: '5 min read', img: IMG + 'analysis.webp' },
    { cat: 'Image Forensics', title: 'Spotting AI-generated images in academic submissions', sum: 'Diffusion artefacts, frequency signatures and metadata gaps — the multimodal tells of synthetic imagery.', read: '6 min read', img: IMG + 'deepfake.webp' },
    { cat: 'AI Trends', title: 'Human vs. machine: telling academic authorship apart', sum: 'Most modern submissions now contain partial AI assistance. What that means for evaluation and detection.', read: '8 min read', img: IMG + 'human-ai.webp' },
    { cat: 'Misinformation', title: 'AI-generated text and the spread of academic misinformation', sum: 'When synthetic content enters the literature, traceability becomes essential. How detection protects the record.', read: '5 min read', img: IMG + 'misinfo.webp' },
    { cat: 'MarkTrack', title: 'Document traceability: versioning that protects authorship', sum: 'Every edit leaves a trail. How continuous tracking establishes a defensible record of original work.', read: '5 min read', img: IMG + 'research.webp' }
  ];

  var GUIDES = [
    { t: 'Getting started with the Plagiarism Detector', m: '5 min', lvl: 'beg' },
    { t: 'Reading your AI Text Detection report', m: '7 min', lvl: 'int' },
    { t: 'Running a FinderX deep source search', m: '6 min', lvl: 'int' },
    { t: 'Interpreting stylometric similarity scores', m: '10 min', lvl: 'adv' },
    { t: 'Verifying images with AI Image Detect', m: '5 min', lvl: 'beg' },
    { t: 'Organising documents and shared folders', m: '4 min', lvl: 'beg' },
    { t: 'Advanced semantic comparison settings', m: '9 min', lvl: 'adv' },
    { t: 'Exporting and citing your analysis results', m: '6 min', lvl: 'int' }
  ];

  var TIPS = [
    'Use multiple sources to strengthen the originality of your academic work.',
    'Run a preventive check before submitting — catching issues early saves rewrites.',
    'Paraphrase by understanding, not by swapping synonyms. Detectors see meaning.',
    'Always disclose AI assistance; transparency protects your academic credibility.',
    'Keep a version history of your drafts to establish a clear authorship trail.',
    'Quote directly only when the exact wording matters — otherwise, synthesise.'
  ];

  var FACTS = [
    'Over 60% of current academic texts contain partial AI assistance.',
    'Embedding-based detection can flag paraphrased plagiarism that string matching misses.',
    'Stylometric analysis can identify an author from as few as 500 words of text.',
    'Diffusion-generated images leave frequency-domain artefacts invisible to the eye.',
    'The average research paper cites work from more than 30 distinct sources.',
    'Burstiness — variation in sentence complexity — is a key human-writing signal.'
  ];

  function pickRandom(arr, n) {
    var copy = arr.slice(), out = [];
    while (out.length < n && copy.length) out.push(copy.splice(Math.floor(Math.random() * copy.length), 1)[0]);
    return out;
  }

  /* ── BLOG render ── */
  var _blogIdx = Math.floor(Math.random() * BLOG.length);
  function renderBlog() {
    var card = document.getElementById('hdBlogCard');
    if (!card) return;
    var a = BLOG[_blogIdx % BLOG.length];
    var sc = card.querySelector('.scene');
    sc.style.background = "linear-gradient(180deg, rgba(8,12,24,.05), rgba(8,12,24,.45)), url('" + a.img + "') center/cover no-repeat";
    card.querySelector('.cat').textContent = a.cat;
    card.querySelector('h3').textContent = a.title;
    card.querySelector('p').textContent = a.sum;
    card.querySelector('.meta').textContent = a.read;
    _blogIdx++;
    relayout();
  }

  /* ── GUIDES render ── */
  function renderGuides() {
    var list = document.getElementById('hdGuideList');
    if (!list) return;
    var picks = pickRandom(GUIDES, 4);
    list.innerHTML = picks.map(function (g, i) {
      var lvlName = g.lvl === 'beg' ? 'Beginner' : g.lvl === 'int' ? 'Intermediate' : 'Advanced';
      return '<div class="hd-guide" onclick="window.open(\'https://xplagiax.ca/guides\',\'_blank\')">' +
        '<div class="hd-guide__num">0' + (i + 1) + '</div>' +
        '<div class="hd-guide__b"><div class="t">' + g.t + '</div>' +
        '<div class="m"><span class="lvl ' + g.lvl + '">' + lvlName + '</span><span>· ' + g.m + ' read</span></div></div></div>';
    }).join('');
    relayout();
  }

  /* ── ACTIVITY feed (real docs + fallback) ── */
  function timeAgo(iso) {
    if (!iso) return '';
    var d = new Date(iso), s = (Date.now() - d.getTime()) / 1000;
    if (s < 60) return 'just now';
    if (s < 3600) return Math.floor(s / 60) + 'm ago';
    if (s < 86400) return Math.floor(s / 3600) + 'h ago';
    return Math.floor(s / 86400) + 'd ago';
  }
  var FEED_FALLBACK = [
    { c: '#3ee79b', t: 'Welcome to <b>XplagiaX</b> — your workspace is ready', time: 'just now' },
    { c: '#6fb0ff', t: 'Tip: run an originality check before your next submission', time: 'today' },
    { c: '#a98bff', t: 'Explore <b>FinderX</b> for deep source discovery', time: 'today' }
  ];
  function renderFeed() {
    var box = document.getElementById('hdFeed');
    if (!box) return;
    fetch('/x_doc/folders?trash=false')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        var items = [];
        if (data && (data.files || data.folders)) {
          (data.folders || []).slice(0, 2).forEach(function (f) {
            items.push({ c: '#ffc94d', t: 'Folder <b>' + esc(f.name) + '</b> created', time: timeAgo(f.created_at) });
          });
          (data.files || []).slice(0, 4).forEach(function (f) {
            items.push({ c: '#6fb0ff', t: 'Document <b>' + esc(f.original_filename || f.name || 'file') + '</b> added', time: timeAgo(f.created_at) });
          });
        }
        if (!items.length) items = FEED_FALLBACK;
        box.innerHTML = items.slice(0, 6).map(function (it) {
          return '<div class="hd-feed__item"><span class="hd-feed__dot" style="background:' + it.c + ';"></span>' +
            '<div class="hd-feed__t">' + it.t + '</div><div class="hd-feed__time">' + it.time + '</div></div>';
        }).join('');
        relayout();
      })
      .catch(function () {
        box.innerHTML = FEED_FALLBACK.map(function (it) {
          return '<div class="hd-feed__item"><span class="hd-feed__dot" style="background:' + it.c + ';"></span>' +
            '<div class="hd-feed__t">' + it.t + '</div><div class="hd-feed__time">' + it.time + '</div></div>';
        }).join('');
        relayout();
      });
  }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]; }); }

  /* ── real document count for hero + insights ── */
  function wireRealCounts() {
    if (!document.querySelector('[data-live="total"]')) return; // no target on page
    fetch('/x_buck/api/sidebar-counts')
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d) return;
        document.querySelectorAll('[data-live="total"]').forEach(function (el) {
          el.dataset.count = d.total || 0; el.dataset.done = ''; animateCount(el);
        });
      }).catch(function () {});
  }

  /* ───────────────────────── HERO PARTICLES ───────────────────────── */
  function initParticles() {
    var host = document.getElementById('hdParticles');
    if (!host) return;
    for (var i = 0; i < 14; i++) {
      var s = document.createElement('span');
      var size = 2 + Math.random() * 4;
      s.style.width = s.style.height = size + 'px';
      s.style.left = Math.random() * 100 + '%';
      s.style.bottom = '-10px';
      s.style.animationDuration = (5 + Math.random() * 6) + 's';
      s.style.animationDelay = (Math.random() * 6) + 's';
      host.appendChild(s);
    }
  }

  /* ───────────────────────── INIT ───────────────────────── */
  function init() {
    initParticles();
    initSlider();
    renderBlog();
    renderGuides();
    renderFeed();
    fillBars();
    document.querySelectorAll('[data-count]').forEach(animateCount);
    wireRealCounts();

    initRotator('hdTipText', 'hdTipDots', TIPS, 10000);
    initRotator('hdFactText', 'hdFactDots', FACTS, 12000);

    // blog auto-rotate + manual refresh
    var rb = document.getElementById('hdBlogRefresh');
    if (rb) rb.addEventListener('click', renderBlog);
    setInterval(renderBlog, 28000);
    var rg = document.getElementById('hdGuideRefresh');
    if (rg) rg.addEventListener('click', renderGuides);

    // layout passes (fonts shift heights; cards reveal with staggered delays up to ~1.2s)
    layout();
    requestAnimationFrame(layout);
    [250, 700, 1300].forEach(function (ms) { setTimeout(layout, ms); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(layout);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
