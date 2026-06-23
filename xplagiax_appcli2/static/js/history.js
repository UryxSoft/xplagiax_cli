'use strict';

let avSessions = [];
let avRiskFilter = 'all';
let avSearchQ = '';
let avDonutChart, avLineChart, avBarChart;

document.addEventListener('DOMContentLoaded', () => {
  loadAnalytics('30');

  document.querySelectorAll('.av-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.av-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const range = btn.dataset.range;
      if (range === 'custom') {
        document.getElementById('avCustomRange').classList.add('visible');
      } else {
        document.getElementById('avCustomRange').classList.remove('visible');
        loadAnalytics(range);
      }
    });
  });

  document.getElementById('avApplyCustom').addEventListener('click', () => {
    const from = document.getElementById('avDateFrom').value;
    const to   = document.getElementById('avDateTo').value;
    if (from && to) loadAnalytics('custom', from, to);
  });

  document.getElementById('avTblFilter').addEventListener('input', e => {
    avSearchQ = e.target.value.toLowerCase();
    renderTable();
  });

  document.querySelectorAll('.av-risk-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.av-risk-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      avRiskFilter = btn.dataset.risk;
      renderTable();
    });
  });
});

async function loadAnalytics(range, dateFrom, dateTo) {
  let url = `/api/history/analytics?range=${range}`;
  if (range === 'custom' && dateFrom && dateTo) {
    url += `&date_from=${dateFrom}&date_to=${dateTo}`;
  }
  try {
    const res  = await fetch(url);
    const data = await res.json();
    if (!data.success) return;
    const d = data.data;
    avSessions = d.sessions || [];
    renderKPIs(d.kpis);
    renderDonut(d.kpis);
    renderLine(d.timeseries);
    renderBar(d.sessions);
    renderAlerts(d.alerts);
    renderTable();
  } catch (e) {
    console.error('loadAnalytics error', e);
  }
}

function renderKPIs(k) {
  function setKpi(valueId, val, barId, barPct, trendId, trendVal, isBad) {
    const vEl = document.getElementById(valueId);
    if (vEl) vEl.textContent = val;
    const bEl = document.getElementById(barId);
    if (bEl) bEl.style.width = Math.min(barPct, 100) + '%';
    const tEl = document.getElementById(trendId);
    if (!tEl) return;
    const delta = trendVal;
    const up = delta >= 0;
    tEl.textContent = (up ? '↑ ' : '↓ ') + Math.abs(delta);
    tEl.className = 'av-kpi-trend ' + (up ? 'av-trend-up' : 'av-trend-down') + (isBad === true && up ? ' av-trend-bad' : isBad === false && !up ? ' av-trend-bad' : '');
  }

  setKpi('avKpiSessionsValue', k.total_analyses, 'avKpiSessionsBar', k.total_analyses * 2, 'avKpiSessionsTrend', 0, null);
  setKpi('avKpiAiValue', k.avg_ai_pct.toFixed(1) + '%', 'avKpiAiBar', k.avg_ai_pct, 'avKpiAiTrend', k.avg_ai_trend, true);
  setKpi('avKpiRiskValue', k.high_risk, 'avKpiRiskBar', k.total_analyses ? (k.high_risk / k.total_analyses * 100) : 0, 'avKpiRiskTrend', 0, true);
  setKpi('avKpiImagesValue', k.total_images, 'avKpiImagesBar', Math.min(k.total_images * 4, 100), 'avKpiImagesTrend', 0, true);
  setKpi('avKpiApprovedValue', k.approved, 'avKpiApprovedBar', k.total_analyses ? (k.approved / k.total_analyses * 100) : 0, 'avKpiApprovedTrend', 0, false);

  const iEl = document.getElementById('avKpiIntegrityValue');
  if (iEl) iEl.innerHTML = k.integrity_score.toFixed(0) + '<span class="av-kpi-unit">/100</span>';
  const ibEl = document.getElementById('avKpiIntegrityBar');
  if (ibEl) ibEl.style.width = k.integrity_score + '%';
  const itEl = document.getElementById('avKpiIntegrityTrend');
  if (itEl) {
    const t = k.integrity_trend;
    itEl.textContent = (t >= 0 ? '↑ ' : '↓ ') + Math.abs(t) + 'pts';
    itEl.className = 'av-kpi-trend ' + (t >= 0 ? 'av-trend-up' : 'av-trend-down av-trend-bad');
  }

  const donutBadge = document.getElementById('avDonutBadge');
  if (donutBadge) {
    const hi = k.high_risk, total = k.total_analyses || 1;
    const pct = hi / total * 100;
    if (pct >= 35) { donutBadge.textContent = 'High Risk'; donutBadge.className = 'av-card-badge av-badge-amber'; }
    else if (pct >= 15) { donutBadge.textContent = 'Medium Risk'; donutBadge.className = 'av-card-badge av-badge-amber'; }
    else { donutBadge.textContent = 'Low Risk'; donutBadge.className = 'av-card-badge av-badge-green'; }
  }

  const barBadge = document.getElementById('avBarBadge');
  if (barBadge) barBadge.textContent = k.total_analyses + ' analyses';

  const it = k.integrity_trend;
  const tb = document.getElementById('avTrendBadge');
  if (tb) {
    if (it > 0) { tb.className = 'av-trend-badge trend-up'; document.getElementById('avTrendIcon').textContent = '↑'; document.getElementById('avTrendLabel').textContent = 'Growing'; }
    else if (it < 0) { tb.className = 'av-trend-badge trend-down'; document.getElementById('avTrendIcon').textContent = '↓'; document.getElementById('avTrendLabel').textContent = 'Declining'; }
    else { tb.className = 'av-trend-badge trend-flat'; document.getElementById('avTrendIcon').textContent = '→'; document.getElementById('avTrendLabel').textContent = 'Stable'; }
  }
  const dp = document.getElementById('avDeltaVal');
  if (dp) dp.textContent = (it >= 0 ? '+' : '') + it.toFixed(1) + ' pts';
}

function renderDonut(k) {
  const el = document.getElementById('avDonutChart');
  if (!el) return;
  const opts = {
    chart: { type: 'donut', height: 200, background: 'transparent', sparkline: { enabled: false } },
    theme: { mode: 'dark' },
    series: [k.high_risk, k.revision, k.approved],
    labels: ['High Risk', 'Review', 'Approved'],
    colors: ['#f87171', '#fbbf24', '#34d399'],
    legend: { show: false },
    dataLabels: { enabled: false },
    stroke: { width: 2, colors: ['rgba(255,255,255,.04)'] },
    plotOptions: { pie: { donut: { size: '68%', labels: {
      show: true,
      total: { show: true, label: 'Total', color: 'rgba(255,255,255,.5)', fontSize: '11px',
        formatter: w => w.globals.seriesTotals.reduce((a, b) => a + b, 0)
      }
    } } } },
    tooltip: { theme: 'dark', style: { fontFamily: 'inherit' } }
  };
  if (avDonutChart) { avDonutChart.updateOptions(opts); }
  else { avDonutChart = new ApexCharts(el, opts); avDonutChart.render(); }

  const leg = document.getElementById('avDonutLegend');
  if (leg) {
    const total = (k.high_risk + k.revision + k.approved) || 1;
    leg.innerHTML = `
      <div class="av-legend-item"><span class="av-leg-dot" style="background:#f87171"></span><span>High Risk <strong>${k.high_risk}</strong></span></div>
      <div class="av-legend-item"><span class="av-leg-dot" style="background:#fbbf24"></span><span>Review <strong>${k.revision}</strong></span></div>
      <div class="av-legend-item"><span class="av-leg-dot" style="background:#34d399"></span><span>Approved <strong>${k.approved}</strong></span></div>
    `;
  }
}

function renderLine(ts) {
  const el = document.getElementById('avLineChart');
  if (!el || !ts) return;
  const dates  = ts.map(p => p.date);
  const integ  = ts.map(p => parseFloat(p.integrity.toFixed(1)));
  const aiPct  = ts.map(p => parseFloat(p.ai_pct.toFixed(1)));
  const opts = {
    chart: { type: 'line', height: 220, background: 'transparent', toolbar: { show: false }, animations: { enabled: true, easing: 'easeinout', speed: 500 } },
    theme: { mode: 'dark' },
    series: [
      { name: 'Integrity', data: integ, color: '#34d399' },
      { name: '% AI Detected', data: aiPct, color: '#f87171' }
    ],
    xaxis: { categories: dates, labels: { style: { colors: 'rgba(255,255,255,.4)', fontSize: '10px', fontFamily: 'inherit' }, rotate: -30 }, axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { min: 0, max: 100, labels: { style: { colors: 'rgba(255,255,255,.4)', fontSize: '10px', fontFamily: 'inherit' }, formatter: v => v + '%' } },
    grid: { borderColor: 'rgba(255,255,255,.06)', strokeDashArray: 3 },
    stroke: { curve: 'smooth', width: 2 },
    markers: { size: ts.length <= 15 ? 3 : 0, strokeWidth: 0 },
    legend: { show: false },
    tooltip: { theme: 'dark', style: { fontFamily: 'inherit' }, y: { formatter: v => v + '%' } },
    annotations: {
      yaxis: [
        { y: 80, borderColor: '#34d399', borderWidth: 1, strokeDashArray: 4, label: { text: '', style: { background: 'transparent' } } },
        { y: 60, borderColor: '#fbbf24', borderWidth: 1, strokeDashArray: 4, label: { text: '', style: { background: 'transparent' } } }
      ]
    }
  };
  if (avLineChart) { avLineChart.updateOptions(opts); }
  else { avLineChart = new ApexCharts(el, opts); avLineChart.render(); }
}

function renderBar(sessions) {
  const el = document.getElementById('avBarChart');
  if (!el || !sessions) return;
  const slice = sessions.slice(0, 20);
  const cats   = slice.map(s => truncate(s.title, 20));
  const aiData = slice.map(s => parseFloat(s.ai_pct.toFixed(1)));
  const colors = aiData.map(v => v >= 35 ? '#f87171' : v >= 15 ? '#fbbf24' : '#34d399');
  const opts = {
    chart: { type: 'bar', height: 220, background: 'transparent', toolbar: { show: false } },
    theme: { mode: 'dark' },
    series: [{ name: 'AI %', data: aiData }],
    colors: ['#60a5fa'],
    xaxis: { categories: cats, labels: { style: { colors: 'rgba(255,255,255,.4)', fontSize: '9px', fontFamily: 'inherit' }, rotate: -35 }, axisBorder: { show: false }, axisTicks: { show: false } },
    yaxis: { min: 0, max: 100, labels: { style: { colors: 'rgba(255,255,255,.4)', fontSize: '10px', fontFamily: 'inherit' }, formatter: v => v + '%' } },
    grid: { borderColor: 'rgba(255,255,255,.06)', strokeDashArray: 3 },
    plotOptions: { bar: { borderRadius: 4, columnWidth: '60%', distributed: true } },
    legend: { show: false },
    tooltip: { theme: 'dark', style: { fontFamily: 'inherit' }, y: { formatter: v => v + '%' } },
    fill: { colors: colors }
  };
  if (avBarChart) { avBarChart.updateOptions(opts); }
  else { avBarChart = new ApexCharts(el, opts); avBarChart.render(); }
}

function renderAlerts(alerts) {
  const wrap = document.getElementById('avAlerts');
  if (!wrap) return;
  if (!alerts || alerts.length === 0) {
    wrap.innerHTML = '<div class="av-empty">No alerts for the selected period.</div>';
    return;
  }
  wrap.innerHTML = alerts.map(a => {
    const cls  = a.risk === 'crit' ? 'av-alert-crit' : 'av-alert-warn';
    const rCls = a.risk === 'crit' ? 'av-risk-crit' : 'av-risk-warn';
    const rLbl = a.risk === 'crit' ? 'CRITICAL' : 'MEDIUM';
    const reason = a.ai_pct >= 35
      ? `${a.ai_pct.toFixed(1)}% of the content was identified as AI-generated. Exceeds the critical threshold (35%).`
      : `${a.images} unreferenced image(s) detected in this document.`;
    return `
    <div class="av-alert ${cls}">
      <div class="av-alert-left">
        <div class="av-alert-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        </div>
        <div>
          <div class="av-alert-title">${escHtml(a.title)}</div>
          <div class="av-alert-desc">${reason}</div>
          <div class="av-alert-actions">
            <span class="av-alert-action-btn" onclick="avViewAnalysis('${a.analysis_id}')">View analysis →</span>
          </div>
        </div>
      </div>
      <div class="av-alert-meta">
        <span class="av-risk-badge ${rCls}">${rLbl}</span>
        <span class="av-alert-time">${a.date}</span>
      </div>
    </div>`;
  }).join('');
}

function renderTable() {
  const tbody = document.getElementById('avTableBody');
  if (!tbody) return;
  let rows = avSessions.filter(s => {
    const q = avSearchQ;
    const matchText = !q || s.title.toLowerCase().includes(q) || s.date.includes(q);
    const matchRisk = avRiskFilter === 'all' || s.risk === avRiskFilter;
    return matchText && matchRisk;
  });
  if (rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="av-empty">No results found.</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(s => {
    const pctCls  = s.risk === 'crit' ? 'av-pct-crit' : s.risk === 'warn' ? 'av-pct-warn' : 'av-pct-ok';
    const ringCls = s.risk === 'crit' ? 'av-score-crit' : s.risk === 'warn' ? 'av-score-warn' : 'av-score-ok';
    const rBadge  = s.risk === 'crit' ? 'av-risk-crit' : s.risk === 'warn' ? 'av-risk-warn' : 'av-risk-ok';
    const rLabel  = s.risk === 'crit' ? 'CRITICAL' : s.risk === 'warn' ? 'MEDIUM' : 'LOW';
    const sid     = 'row-' + s.analysis_id.replace(/-/g,'');
    return `
    <tr id="tr-${sid}">
      <td>
        <div class="av-expand-btn" id="btn-${sid}" onclick="avToggleRow('${sid}',this)">
          <svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
      </td>
      <td>${escHtml(truncate(s.title, 40))}</td>
      <td>${s.date}</td>
      <td><div class="av-pct-bar"><span class="av-pct-pill ${pctCls}">${s.ai_pct.toFixed(1)}%</span></div></td>
      <td>${s.images}</td>
      <td><div class="av-score-ring ${ringCls}">${s.integrity}</div></td>
      <td><span class="av-risk-badge ${rBadge}">${rLabel}</span></td>
      <td><span class="av-alert-action-btn" onclick="avViewAnalysis('${s.analysis_id}')">View</span></td>
    </tr>
    <tr class="av-row-expanded av-row-hidden" id="exp-${sid}">
      <td colspan="8">
        <div class="av-expanded-content">
          <div>
            <div class="av-exp-block-title">Document details</div>
            <div class="av-snippet">Pages: ${s.pages || '—'} · Paragraphs: ${s.paragraphs || '—'}</div>
          </div>
          <div>
            <div class="av-exp-block-title">Model confidence</div>
            <div class="av-snippet">${s.confidence ? (s.confidence * 100).toFixed(0) + '%' : '—'}</div>
          </div>
          <div>
            <div class="av-exp-block-title">Images detected</div>
            <div class="av-snippet">${s.images} unreferenced image(s)</div>
          </div>
          <div class="av-exp-actions">
            <div class="av-exp-action av-action-primary" onclick="avViewAnalysis('${s.analysis_id}')">
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              View full analysis
            </div>
          </div>
        </div>
      </td>
    </tr>`;
  }).join('');
}

function avToggleRow(sid, btn) {
  const expRow = document.getElementById('exp-' + sid);
  if (!expRow) return;
  const isOpen = !expRow.classList.contains('av-row-hidden');
  expRow.classList.toggle('av-row-hidden', isOpen);
  btn.classList.toggle('open', !isOpen);
}

function avViewAnalysis(analysisId) {
  window.location.href = '/documents';
}

function avExport(type) {
  showToast(type === 'pdf' ? 'Exporting PDF…' : 'Exporting CSV…');
}

function avFilterLine() {}

function showToast(msg) {
  const existing = document.querySelector('.av-toast');
  if (existing) existing.remove();
  const t = document.createElement('div');
  t.className = 'av-toast';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2800);
}

function truncate(str, n) {
  if (!str) return '';
  return str.length > n ? str.slice(0, n) + '…' : str;
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
