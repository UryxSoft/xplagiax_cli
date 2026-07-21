"""
Enterprise Academic Integrity Report (PDF) — generador ReportLab/Platypus.

Reemplaza el resumen de 3 números de `_share_pdf_bytes` por un reporte
institucional multi-sección que consume TODO lo que AnalysisHistory ya
persiste (entry.ai / entry.source / entry.citation) y que hasta ahora el PDF
ignoraba: segmentos de IA, fuentes de FinderX, validación de citas.

Reglas de coherencia con la app (no negociables):
  - El % de "Plagiarism" se gatea por segmentos CONFIRMADOS (decision
    plagiarism/paraphrase), igual que el verdict del tab FinderX y el chip
    del topbar — un score crudo alto con 0 segmentos confirmados se reporta
    como similitud temática, nunca como plagio.
  - Umbrales de riesgo idénticos al frontend: >=50 HIGH, >=25 MEDIUM.
  - Paleta = _XPA_BRAND (analysis_smartinput.css): rojo IA, ámbar similitud,
    azul citas, verde humano, morado original. (El mapeo de colores de la
    app manda sobre cualquier otra convención.)

El "verification code" del pie es un checksum SHA-256 del payload del
análisis (id, scores, fecha) — sirve para comparar el PDF contra la vista
online (misma pantalla pública del QR muestra el mismo código). NO es una
firma criptográfica.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
from datetime import datetime

# Provider name -> static/img/imgsource/<slug>.png slug. Mirrors
# analysis_smartinput.html's _providerLogoHtml (JS) exactly — keep both in
# sync if either changes. A mismatch just means a missing icon (both the
# HTML <img onerror> and the PDF's try/except degrade gracefully), never a
# broken report.
_PROVIDER_LOGO_ALIASES = {
    'archive': 'internetarchive', 'wayback': 'internetarchive',
    'pubmedcentral': 'pmc', 'scholar': 'googlescholar',
    'bielefeld': 'base', 'thelens': 'lens', 'faoagris': 'agris',
    'crossrefapi': 'crossref', 'crossreftdm': 'crossref', 'crossmark': 'crossref',
    'datacitecommons': 'datacite', 'ada': 'nasaads', 'adsabs': 'nasaads',
    'nasaadsabs': 'nasaads', 'inspire': 'inspirehep',
}


def _provider_logo_slug(provider):
    p = str(provider or '').lower().strip()
    if not p or p == 'searxng':  # meta-search aggregator, no logo of its own
        return None
    p = re.sub(r'_[a-z]{2,3}$', '', p)   # language suffix: "wikipedia_en" -> "wikipedia"
    p = re.sub(r'[^a-z0-9]', '', p)      # "semantic_scholar" -> "semanticscholar"
    return _PROVIDER_LOGO_ALIASES.get(p, p) or None


BRAND = {
    'primary': '#064CDB', 'ink': '#0f172a', 'muted': '#64748b',
    'ai': '#ef4444', 'plag': '#f59e0b', 'cit': '#064CDB',
    'ok': '#10b981', 'orig': '#a78bfa', 'bg': '#f8fafc',
    'line': '#e2e8f0', 'body': '#334155',
    'danger': '#dc2626', 'warn': '#d97706', 'success': '#059669',
}

_RISK = {
    'LOW':    {'color': BRAND['ok'],   'glyph': '●', 'label': 'Low Risk'},
    'MEDIUM': {'color': BRAND['plag'], 'glyph': '▲', 'label': 'Medium Risk'},
    'HIGH':   {'color': BRAND['ai'],   'glyph': '■', 'label': 'High Risk'},
}


# ── Extracción defensiva de los JSON persistidos ─────────────────────────────

def _num(v, default=0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def extract_report_data(entry):
    """Normaliza entry.ai / entry.source / entry.citation al dict que consumen
    el PDF y la vista pública (una sola fuente de verdad para ambos)."""
    ai = entry.ai if isinstance(entry.ai, dict) else None
    src = entry.source if isinstance(entry.source, dict) else None
    cit = entry.citation if isinstance(entry.citation, dict) else None

    ai_pct = int(_num(entry.ai_pct, _num((ai or {}).get('ai_score')))) if (entry.ai_pct is not None or ai) else None
    human_pct = None
    if ai_pct is not None:
        human_pct = int(_num((ai or {}).get('human_score'), 100 - ai_pct))

    scores = (src or {}).get('scores') or {}
    overall = int(_num(entry.overall, _num(scores.get('overall')))) if (entry.overall is not None or src) else None
    exact = int(_num(scores.get('exact'))) if src else None
    semantic = int(_num(scores.get('semantic'))) if src else None

    segs = (src or {}).get('segment_matches') or []
    summary = (src or {}).get('segment_summary') or {}
    flagged_segs = [s for s in segs if str(s.get('decision', '')).lower() in ('plagiarism', 'paraphrase')]
    flagged_n = int(_num(summary.get('segments_flagged'), len(flagged_segs)))
    analyzed_n = int(_num(summary.get('segments_analyzed'), len(segs)))
    has_flag = flagged_n > 0
    # Mismo gating que el frontend: sin segmento confirmado no hay "plagio".
    plag_pct = overall if (has_flag and overall is not None) else (0 if src else None)

    original_n = None
    if src and analyzed_n:
        if summary.get('segments_original') is not None:
            original_n = int(_num(summary.get('segments_original')))
        else:
            original_n = len([s for s in segs if str(s.get('decision', '')).lower() == 'original']) or (analyzed_n - flagged_n)
    original_pct = int(round(original_n / analyzed_n * 100)) if (original_n is not None and analyzed_n) else (
        max(0, 100 - (overall or 0)) if src else None)

    matches = list((src or {}).get('academic_matches') or [])
    # Shallow copy (not mutation) — these dicts are the same objects cached
    # inside entry.source's JSON; adding logo_slug in place would risk
    # SQLAlchemy flagging the JSON column dirty on a read-only route.
    def _with_logo(m):
        return dict(m, logo_slug=_provider_logo_slug(m.get('provider') or m.get('source')))
    web = [_with_logo(m) for m in matches if str(m.get('source_type', '')).lower() == 'internet']
    academic = [_with_logo(m) for m in matches if str(m.get('source_type', '')).lower() != 'internet']

    cit_score = int(_num(entry.cit_score, _num((cit or {}).get('citation_quality_score')))) if (entry.cit_score is not None or cit) else None
    citations_found = int(_num((cit or {}).get('citations_found'))) if cit else None
    references_found = int(_num((cit or {}).get('references_found'))) if cit else None
    orphan_cit = int(_num((cit or {}).get('orphan_citations'))) if cit else None
    orphan_ref = int(_num((cit or {}).get('orphan_references'))) if cit else None
    cit_risk = str((cit or {}).get('overall_risk_level') or 'low').lower() if cit else None

    # Riesgo combinado — misma fórmula que el Overview de la app.
    plag_risk = max(overall or 0, exact or 0) if has_flag else 0
    risk_pct = max(ai_pct or 0, plag_risk)
    risk = 'HIGH' if risk_pct >= 50 else 'MEDIUM' if risk_pct >= 25 else 'LOW'
    integrity_score = max(0, 100 - risk_pct)

    text = (entry.text or '').strip()
    word_count = int(_num((ai or {}).get('word_count'), len(text.split())))
    language = str((src or {}).get('language') or '').upper() or None
    meta = (src or {}).get('metadata') or {}

    created = entry.created_at or datetime.utcnow()
    checksum = hashlib.sha256(json.dumps(
        [entry.history_id, entry.title, ai_pct, overall, cit_score,
         created.strftime('%Y-%m-%dT%H:%M:%S')],
        sort_keys=True, default=str).encode()).hexdigest()

    return {
        'title': entry.title or 'Untitled analysis',
        'history_id': entry.history_id,
        'created': created,
        'text': text,
        'word_count': word_count,
        'language': language,
        'ai': ai, 'src': src, 'cit': cit,
        'ai_pct': ai_pct, 'human_pct': human_pct,
        'overall': overall, 'exact': exact, 'semantic': semantic,
        'plag_pct': plag_pct, 'has_flag': has_flag,
        'flagged_n': flagged_n, 'analyzed_n': analyzed_n,
        'original_pct': original_pct,
        'flagged_segs': flagged_segs, 'segs': segs,
        'academic': academic, 'web': web,
        'cit_score': cit_score, 'cit_risk': cit_risk,
        'citations_found': citations_found, 'references_found': references_found,
        'orphan_cit': orphan_cit, 'orphan_ref': orphan_ref,
        'risk': risk, 'risk_pct': risk_pct, 'integrity_score': integrity_score,
        'chunks': int(_num(meta.get('chunks_analyzed'))) or None,
        'checksum': checksum,
    }


def risk_explanation(d):
    """Frase corta bajo el Risk Level — redactada según los datos reales."""
    parts = []
    if d['risk'] == 'LOW':
        parts.append('The document presents a LOW academic integrity risk.')
    elif d['risk'] == 'MEDIUM':
        parts.append('The document presents a MEDIUM academic integrity risk and should be reviewed.')
    else:
        parts.append('The document presents a HIGH academic integrity risk and requires manual review.')
    if d['has_flag']:
        parts.append(f"{d['flagged_n']} of {d['analyzed_n']} analyzed segments match known sources.")
    elif d['src']:
        if (d['exact'] or 0) >= 50 or (d['overall'] or 0) >= 50:
            parts.append('High raw similarity was detected, but no full segment was confirmed as a copy '
                         '(short or localized matches only).')
        else:
            parts.append('No copied passages were confirmed against external sources.')
    if d['ai_pct'] is not None:
        if d['ai_pct'] >= 50:
            parts.append(f"AI-characteristic patterns dominate the text ({d['ai_pct']}%).")
        elif d['ai_pct'] >= 25:
            parts.append(f"AI-characteristic patterns appear in parts of the text ({d['ai_pct']}%).")
    return ' '.join(parts)


def risk_factors(d):
    """Bullets del Academic Risk Assessment, derivados de los datos."""
    out = []
    if d['ai_pct'] is not None and d['ai_pct'] >= 50:
        out.append(('High AI concentration', f"{d['ai_pct']}% of the content shows AI-characteristic patterns.", 'bad'))
    elif d['ai_pct'] is not None and d['ai_pct'] >= 25:
        out.append(('Moderate AI presence', f"{d['ai_pct']}% of the content shows AI-characteristic patterns.", 'warn'))
    elif d['ai_pct'] is not None:
        out.append(('Predominantly human-written', f"Only {d['ai_pct']}% shows AI-characteristic patterns.", 'good'))
    if d['has_flag']:
        out.append(('Confirmed source matches', f"{d['flagged_n']} segment(s) were flagged as plagiarism or paraphrase.", 'bad'))
    elif d['src'] and ((d['exact'] or 0) >= 50):
        out.append(('Localized literal overlap',
                    f"A {d['exact']}% exact score indicates short word-for-word matches, "
                    'but no full segment was confirmed as copied.', 'warn'))
    elif d['src']:
        out.append(('No confirmed plagiarism', 'No segment matched an external source closely enough to be flagged.', 'good'))
    if d['orphan_cit']:
        out.append(('Orphan citations', f"{d['orphan_cit']} in-text citation(s) have no matching bibliography entry.", 'warn'))
    if d['orphan_ref']:
        out.append(('Uncited references', f"{d['orphan_ref']} bibliography entrie(s) are never cited in the text.", 'warn'))
    if d['cit'] and not d['citations_found'] and not d['references_found']:
        out.append(('No citations detected', 'The document contains no detectable citations or bibliography.', 'warn'))
    elif d['cit_score'] is not None and d['cit_score'] >= 80:
        out.append(('Good citation quality', f"Citation quality scored {d['cit_score']}/100.", 'good'))
    return out


def recommendations(d):
    out = []
    if d['ai_pct'] is not None and d['ai_pct'] >= 25:
        out.append('Review the sections flagged with AI-characteristic patterns and verify authorship.')
    if d['has_flag']:
        out.append('Rewrite or properly cite the flagged passages that match external sources.')
    if d['src'] and not d['has_flag'] and (d['exact'] or 0) >= 50:
        out.append('Check the listed candidate sources: short literal overlaps were found even though '
                   'no full segment was confirmed as copied.')
    if d['orphan_cit']:
        out.append('Add the missing bibliography entries for in-text citations that currently have none.')
    if d['orphan_ref']:
        out.append('Remove or cite the bibliography entries that never appear in the text.')
    if d['cit'] and not d['citations_found']:
        out.append('Increase citation coverage: no in-text citations were detected.')
    if not out:
        out.append('No corrective action is required. The document may be archived as reviewed.')
    return out


def interpretation(d):
    """Párrafo de lectura experta, generado por reglas (sin inventar datos)."""
    s = []
    if d['risk'] == 'LOW':
        s.append('The document demonstrates an acceptable level of academic integrity.')
    elif d['risk'] == 'MEDIUM':
        s.append('The document shows integrity indicators that warrant closer inspection.')
    else:
        s.append('The document shows strong indicators of compromised academic integrity.')
    if d['src']:
        if d['has_flag']:
            s.append(f"FinderX confirmed {d['flagged_n']} segment(s) matching external sources; "
                     'these passages are listed in the Findings section with their matched source.')
        else:
            s.append('Similarities detected by the source search correspond to thematic or vocabulary '
                     'overlap rather than confirmed copying.')
    if d['ai_pct'] is not None:
        if d['ai_pct'] >= 50:
            s.append(f"AI detection attributes {d['ai_pct']}% of the content to machine-generated patterns.")
        elif d['ai_pct'] >= 25:
            s.append(f"AI-generated content appears limited to isolated sections ({d['ai_pct']}%) and does not "
                     'dominate the document.')
        else:
            s.append('AI-generated content is minimal and does not significantly affect the originality assessment.')
    if d['cit_score'] is not None:
        if d['cit_score'] >= 80:
            s.append(f"Citation quality is solid ({d['cit_score']}/100).")
        elif d['cit_score'] >= 50:
            s.append(f"Citation quality is acceptable ({d['cit_score']}/100) with room for improvement.")
        else:
            s.append(f"Citation quality is weak ({d['cit_score']}/100); referencing should be reviewed.")
    s.append('These results are decision-support indicators for human review, not a definitive '
             'determination of academic misconduct.')
    return ' '.join(s)


# ── Construcción del PDF ─────────────────────────────────────────────────────

def build_report_pdf(entry, sender_email, public_url=None):
    """Genera el PDF enterprise. Devuelve bytes. `public_url` (vista online
    del QR) es opcional — sin ella se omiten QR y botón de verificación."""
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (Paragraph, Spacer, Table, TableStyle,
                                    HRFlowable, Image, KeepTogether)
    from reportlab.graphics.shapes import Drawing, Rect, String, Wedge, Circle
    import os
    from flask import current_app

    def _logo_flowable(slug, size=3.4 * mm):
        """Provider icon for the Sources table — None if unresolvable, so the
        caller can fall back to plain text (same graceful degradation as the
        HTML <img onerror>)."""
        if not slug:
            return None
        try:
            path = os.path.join(current_app.static_folder, 'img', 'imgsource', f'{slug}.png')
            if not os.path.isfile(path):
                return None
            return Image(path, width=size, height=size)
        except Exception:
            return None

    d = extract_report_data(entry)
    B = BRAND
    C = HexColor

    ss = getSampleStyleSheet()

    def st(name, **kw):
        base = kw.pop('parent', ss['Normal'])
        return ParagraphStyle(name, parent=base, **kw)

    s_h1 = st('rh1', fontSize=19, leading=24, textColor=C(B['ink']), fontName='Helvetica-Bold', spaceAfter=2)
    s_h2 = st('rh2', fontSize=12.5, leading=16, textColor=C(B['ink']), fontName='Helvetica-Bold',
              spaceBefore=14, spaceAfter=6)
    s_sub = st('rsub', fontSize=9, leading=13, textColor=C(B['muted']))
    s_lbl = st('rlbl', fontSize=7.2, leading=9, textColor=C(B['muted']))
    s_body = st('rbody', fontSize=9.3, leading=13.5, textColor=C(B['body']))
    s_small = st('rsmall', fontSize=8.2, leading=11.5, textColor=C(B['body']))
    s_kpi_v = st('rkpiv', fontSize=10, leading=22, alignment=TA_CENTER)
    s_kpi_l = st('rkpil', fontSize=7, leading=9, textColor=C(B['muted']), alignment=TA_CENTER)

    def esc(t):
        return str(t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def pct(v):
        return '—' if v is None else f'{int(v)}%'

    story = []
    bookmarks = []

    def section(title_text, anchor):
        bookmarks.append((anchor, title_text))
        return Paragraph(f'<a name="{anchor}"/>{esc(title_text)}', s_h2)

    # ── Portada ──────────────────────────────────────────────────────────────
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f'<font color="{B["primary"]}"><b>&#215;</b></font>plagia'
        f'<font color="{B["primary"]}"><b>&#215;</b></font>'
        f'<font color="{B["muted"]}" size="8">&nbsp;&nbsp;AI TestPro · FinderX</font>', s_h1))
    story.append(Paragraph('ACADEMIC INTEGRITY REPORT',
                           st('rcov', fontSize=8.5, leading=11, textColor=C(B['primary']),
                              fontName='Helvetica-Bold', spaceBefore=2)))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width='100%', color=C(B['primary']), thickness=2))
    story.append(Spacer(1, 12))
    story.append(Paragraph(esc(d['title']), st('rtitle', fontSize=14, leading=18,
                                               textColor=C(B['ink']), fontName='Helvetica-Bold')))
    story.append(Spacer(1, 10))

    meta_rows = [
        ('Shared by', sender_email or '—'),
        ('Date (UTC)', d['created'].strftime('%B %d, %Y')),
        ('Time (UTC)', d['created'].strftime('%H:%M')),
        ('Words analyzed', f"{d['word_count']:,}"),
        ('Language', d['language'] or '—'),
        ('Analysis ID', d['history_id']),
        ('Report status', 'Verified Report'),
    ]
    meta_tbl = Table(
        [[Paragraph(f'<font color="{B["muted"]}" size="7">{esc(k).upper()}</font><br/>'
                    f'<font color="{B["ink"]}" size="9"><b>{esc(v)}</b></font>', s_small)
          for k, v in meta_rows[i:i + 2]] + ([''] if len(meta_rows[i:i + 2]) == 1 else [])
         for i in range(0, len(meta_rows), 2)],
        colWidths=[88 * mm, 88 * mm])
    meta_tbl.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, C(B['line'])),
    ]))

    if public_url:
        try:
            import qrcode
            qr_img = qrcode.make(public_url, box_size=4, border=1)
            qb = io.BytesIO()
            qr_img.save(qb, format='PNG')
            qb.seek(0)
            qr_cell = [Image(qb, width=27 * mm, height=27 * mm),
                       Paragraph('<b>Scan to verify</b><br/>Opens the live interactive report',
                                 st('rqr', fontSize=6.8, leading=8.5, textColor=C(B['muted']),
                                    alignment=TA_CENTER, spaceBefore=3))]
        except Exception:
            qr_cell = ['']
        cover = Table([[meta_tbl, qr_cell]], colWidths=[138 * mm, 38 * mm])
        cover.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                   ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
        story.append(cover)
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f'Online verification: <font color="{B["primary"]}"><u>'
            f'<link href="{esc(public_url)}">{esc(public_url)}</link></u></font>', s_small))
    else:
        story.append(meta_tbl)

    # ── Resumen ejecutivo ────────────────────────────────────────────────────
    story.append(section('Executive Summary', 'exec'))
    rk = _RISK[d['risk']]

    ring = Drawing(44 * mm, 44 * mm)
    cx = cy = 22 * mm
    r_out, r_in = 20 * mm, 14.2 * mm
    ring.add(Wedge(cx, cy, r_out, 0, 359.99, radius1=r_in, fillColor=C('#eef2f7'), strokeColor=None))
    sweep = max(2.0, 359.99 * d['integrity_score'] / 100.0)
    ring.add(Wedge(cx, cy, r_out, 90 - sweep, 90, radius1=r_in,
                   fillColor=C(rk['color']), strokeColor=None))
    ring.add(String(cx, cy + 1, str(d['integrity_score']), fontSize=17,
                    fillColor=C(B['ink']), fontName='Helvetica-Bold', textAnchor='middle'))
    ring.add(String(cx, cy - 4 * mm, '/ 100', fontSize=6.5,
                    fillColor=C(B['muted']), textAnchor='middle'))

    exec_right = [
        Paragraph(f'<font color="{B["muted"]}" size="7">ACADEMIC INTEGRITY INDEX</font>', s_small),
        Paragraph(f'<font color="{rk["color"]}" size="13"><b>{rk["glyph"]}&nbsp;&nbsp;{rk["label"]}</b></font>',
                  st('rrisk', spaceBefore=2, spaceAfter=5)),
        Paragraph(esc(risk_explanation(d)), s_body),
    ]
    exec_tbl = Table([[ring, exec_right]], colWidths=[50 * mm, 126 * mm])
    exec_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), C(B['bg'])),
        ('BOX', (0, 0), (-1, -1), 0.75, C(B['line'])),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(exec_tbl)

    # ── KPIs ─────────────────────────────────────────────────────────────────
    story.append(section('Key Indicators', 'kpi'))
    kpis = []
    if d['ai_pct'] is not None:
        kpis.append(('AI GENERATED', pct(d['ai_pct']), B['ai'], 'Probability of AI-generated text'))
    if d['plag_pct'] is not None:
        kpis.append(('PLAGIARISM', pct(d['plag_pct']), B['plag'],
                     'Confirmed matches to external sources'))
    if d['cit_score'] is not None:
        kpis.append(('CITATIONS', f"{d['cit_score']}/100", B['cit'], 'Citation & referencing quality'))
    if d['references_found'] is not None:
        kpis.append(('REFERENCES', str(d['references_found']), B['cit'], 'Bibliographic entries identified'))
    if d['original_pct'] is not None:
        kpis.append(('ORIGINAL', pct(d['original_pct']), B['orig'], 'Content with no confirmed match'))
    if d['human_pct'] is not None:
        kpis.append(('HUMAN WRITTEN', pct(d['human_pct']), B['ok'], 'Naturally written content'))
    if kpis:
        row_v = [Paragraph(f'<font color="{c}" size="16"><b>{esc(v)}</b></font>', s_kpi_v)
                 for (_, v, c, _h) in kpis]
        row_l = [Paragraph(f'<b>{esc(k)}</b><br/>{esc(h)}', s_kpi_l) for (k, _, _c, h) in kpis]
        w = 176 * mm / len(kpis)
        kpi_tbl = Table([row_v, row_l], colWidths=[w] * len(kpis))
        kpi_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), C(B['bg'])),
            ('BOX', (0, 0), (-1, -1), 0.75, C(B['line'])),
            ('LINEBEFORE', (1, 0), (-1, -1), 0.75, C(B['line'])),
            ('TOPPADDING', (0, 0), (-1, 0), 8), ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(kpi_tbl)

    # ── Distribución ─────────────────────────────────────────────────────────
    dist = []
    if d['ai_pct'] is not None:
        dist.append(('AI', d['ai_pct'], B['ai']))
    if d['plag_pct'] is not None:
        dist.append(('Plagiarism', d['plag_pct'], B['plag']))
    if d['cit_score'] is not None:
        dist.append(('Citations', d['cit_score'], B['cit']))
    if d['human_pct'] is not None:
        dist.append(('Human', d['human_pct'], B['ok']))
    if d['original_pct'] is not None:
        dist.append(('Original', d['original_pct'], B['orig']))
    if dist:
        story.append(section('Document Distribution', 'dist'))
        bar_w, bar_h = 176 * mm, 7 * mm
        total = sum(max(v, 0.5) for _, v, _c in dist)
        dr = Drawing(bar_w, bar_h + 14)
        x = 0.0
        for name, v, color in dist:
            w = bar_w * max(v, 0.5) / total
            dr.add(Rect(x, 12, max(w - 1, 1), bar_h, fillColor=C(color), strokeColor=None))
            x += w
        lx = 0.0
        for name, v, color in dist:
            dr.add(Rect(lx, 2, 5, 5, fillColor=C(color), strokeColor=None))
            dr.add(String(lx + 8, 3, f'{name} {int(v)}%', fontSize=6.5, fillColor=C(B['body'])))
            lx += 34 * mm
        story.append(dr)
        story.append(Paragraph(
            'Fixed category order (AI · Plagiarism · Citations · Human · Original); '
            'plagiarism is shown only when at least one segment was confirmed against a source.',
            s_lbl))

    # ── Risk assessment ──────────────────────────────────────────────────────
    factors = risk_factors(d)
    if factors:
        story.append(section('Academic Risk Assessment', 'risk'))
        fc = {'bad': B['danger'], 'warn': B['warn'], 'good': B['success']}
        rows = [[Paragraph(f'<font color="{fc[kind]}"><b>{ "■" if kind == "bad" else "▲" if kind == "warn" else "●" }</b></font>', s_body),
                 Paragraph(f'<b>{esc(t)}</b> — {esc(x)}', s_body)]
                for (t, x, kind) in factors]
        ftbl = Table(rows, colWidths=[8 * mm, 168 * mm])
        ftbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(ftbl)

    # ── Fuentes ──────────────────────────────────────────────────────────────
    sources = (d['academic'][:8] + d['web'][:4])
    if sources:
        story.append(section('Detected Sources', 'sources'))
        story.append(Paragraph(
            'Candidate sources sharing topic or vocabulary with the document. Only passages listed under '
            '<b>Findings</b> indicate a confirmed literal match.', s_small))
        story.append(Spacer(1, 4))
        head = [Paragraph(f'<b>{h}</b>', s_lbl) for h in ('#', 'SOURCE', 'PROVIDER', 'YEAR', 'TYPE')]
        rows = [head]
        for i, m in enumerate(sources, 1):
            title = str(m.get('title') or m.get('url') or 'Untitled source')[:110]
            provider = str(m.get('provider') or m.get('source') or '—')
            year = str(m.get('year') or '—')
            kind = 'Web' if str(m.get('source_type', '')).lower() == 'internet' else 'Academic'
            url = m.get('url') or (('https://doi.org/' + str(m['doi'])) if m.get('doi') else None)
            tcell = (f'<link href="{esc(url)}"><font color="{B["primary"]}">{esc(title)}</font></link>'
                     if url else esc(title))
            logo = _logo_flowable(m.get('logo_slug'))
            provider_cell = (
                Table([[logo, Paragraph(esc(provider), s_small)]], colWidths=[4.4 * mm, 21.6 * mm],
                      style=TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                        ('RIGHTPADDING', (0, 0), (0, -1), 2)]))
                if logo else Paragraph(esc(provider), s_small)
            )
            rows.append([Paragraph(str(i), s_small), Paragraph(tcell, s_small),
                         provider_cell, Paragraph(esc(year), s_small),
                         Paragraph(kind, s_small)])
        stbl = Table(rows, colWidths=[8 * mm, 108 * mm, 26 * mm, 14 * mm, 20 * mm], repeatRows=1)
        stbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), C(B['bg'])),
            ('LINEBELOW', (0, 0), (-1, 0), 0.75, C(B['line'])),
            ('LINEBELOW', (0, 1), (-1, -1), 0.4, C('#eef2f7')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(stbl)

    # ── Hallazgos ────────────────────────────────────────────────────────────
    if d['segs'] or (d['ai'] and (d['ai'].get('blocks'))):
        story.append(section('Findings', 'findings'))

        counts = []
        ai_blocks = [b for b in ((d['ai'] or {}).get('blocks') or []) if str(b.get('type')) == 'ai']
        if d['ai']:
            counts.append(f'{len(ai_blocks)} AI-flagged section(s)')
        if d['src']:
            counts.append(f"{d['flagged_n']} plagiarism/paraphrase segment(s)")
            counts.append(f"{max(0, d['analyzed_n'] - d['flagged_n'])} cleared segment(s)")
        if counts:
            story.append(Paragraph(' · '.join(counts), s_small))
            story.append(Spacer(1, 4))

        def seg_card(idx, kind, color, conf_label, body_text, meta_line):
            head = Table([[
                Paragraph(f'<font color="{color}"><b>#{idx} · {esc(kind)}</b></font>', s_small),
                Paragraph(f'<font color="{B["muted"]}">{esc(conf_label)}</font>',
                          st('rsegc', parent=s_small, alignment=2)),
            ]], colWidths=[120 * mm, 56 * mm])
            head.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0),
                                      ('BOTTOMPADDING', (0, 0), (-1, -1), 1)]))
            inner = [head, Paragraph(f'"{esc(body_text)}"', s_small)]
            if meta_line:
                inner.append(Paragraph(f'<font color="{B["muted"]}" size="7">{esc(meta_line)}</font>',
                                       st('rsegm', parent=s_lbl, spaceBefore=2)))
            card = Table([[inner]], colWidths=[176 * mm])
            card.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.6, C(B['line'])),
                ('LINEBEFORE', (0, 0), (0, -1), 2.2, C(color)),
                ('BACKGROUND', (0, 0), (-1, -1), C('#fdfdfe')),
                ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 9), ('RIGHTPADDING', (0, 0), (-1, -1), 9),
            ]))
            return KeepTogether([card, Spacer(1, 5)])

        n = 0
        for s in d['flagged_segs'][:10]:
            n += 1
            src_m = s.get('matched_source') or {}
            meta = ' · '.join(x for x in (
                f"chars {s.get('char_start', '?')}–{s.get('char_end', '?')}" if s.get('char_start') is not None else '',
                f"matched: {str(src_m.get('title') or '')[:80]}" if src_m.get('title') else '',
                str(s.get('reason') or '')[:120]) if x)
            story.append(seg_card(
                n, str(s.get('decision', 'match')).upper(), B['plag'],
                f"match {int(_num(s.get('match_score')))}%",
                str(s.get('text_full') or '')[:340], meta))
        for b in ai_blocks[:8]:
            n += 1
            story.append(seg_card(
                n, 'AI PATTERN', B['ai'],
                f"confidence {int(_num(b.get('confidence')))}%",
                str(b.get('text') or '')[:340],
                ' · '.join(str(p) for p in (b.get('patterns') or [])[:3])))
        cleared = [s for s in d['segs'] if s not in d['flagged_segs']]
        for s in cleared[:3]:
            n += 1
            story.append(seg_card(
                n, 'ORIGINAL', B['success'],
                f"match {int(_num(s.get('match_score')))}%",
                str(s.get('text_full') or '')[:220],
                str(s.get('reason') or 'No confirmed match.')[:140]))
        if len(cleared) > 3:
            story.append(Paragraph(f'+ {len(cleared) - 3} additional cleared segment(s) omitted for brevity — '
                                   'the full list is available in the online report.', s_lbl))

    # ── Citas ────────────────────────────────────────────────────────────────
    if d['cit']:
        story.append(section('Citations, References & Bibliography', 'citations'))
        crow = [
            ('QUALITY', f"{d['cit_score']}/100" if d['cit_score'] is not None else '—', B['cit']),
            ('CITATIONS', str(d['citations_found'] if d['citations_found'] is not None else '—'), B['ink']),
            ('REFERENCES', str(d['references_found'] if d['references_found'] is not None else '—'), B['ink']),
            ('ORPHAN CITES', str(d['orphan_cit'] if d['orphan_cit'] is not None else '—'),
             B['warn'] if d['orphan_cit'] else B['success']),
            ('ORPHAN REFS', str(d['orphan_ref'] if d['orphan_ref'] is not None else '—'),
             B['warn'] if d['orphan_ref'] else B['success']),
            ('RISK', (d['cit_risk'] or '—').capitalize(),
             B['danger'] if d['cit_risk'] in ('high', 'critical') else B['success']),
        ]
        ctbl = Table([
            [Paragraph(f'<font color="{c}" size="13"><b>{esc(v)}</b></font>', s_kpi_v) for (_, v, c) in crow],
            [Paragraph(f'<b>{k}</b>', s_kpi_l) for (k, _, _c) in crow],
        ], colWidths=[176 * mm / len(crow)] * len(crow))
        ctbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), C(B['bg'])),
            ('BOX', (0, 0), (-1, -1), 0.75, C(B['line'])),
            ('LINEBEFORE', (1, 0), (-1, -1), 0.75, C(B['line'])),
            ('TOPPADDING', (0, 0), (-1, 0), 7), ('BOTTOMPADDING', (0, 1), (-1, 1), 7),
        ]))
        story.append(ctbl)

    # ── Métricas avanzadas ───────────────────────────────────────────────────
    story.append(section('Advanced Metrics', 'metrics'))
    adv = [('Words analyzed', f"{d['word_count']:,}")]
    if d['analyzed_n']:
        adv += [('Segments analyzed', str(d['analyzed_n'])),
                ('Segments flagged', str(d['flagged_n'])),
                ('Segments cleared', str(max(0, d['analyzed_n'] - d['flagged_n'])))]
    if d['exact'] is not None:
        adv.append(('Exact (literal) similarity', pct(d['exact'])))
    if d['semantic'] is not None:
        adv.append(('Semantic similarity', pct(d['semantic'])))
    if d['academic'] or d['web']:
        adv.append(('Candidate sources', f"{len(d['academic'])} academic · {len(d['web'])} web"))
    if d['chunks']:
        adv.append(('Chunks processed', str(d['chunks'])))
    if d['language']:
        adv.append(('Detected language', d['language']))
    mrows = [[Paragraph(esc(k), s_small),
              Paragraph(f'<b>{esc(v)}</b>', st('rmv', parent=s_small, alignment=2))]
             for k, v in adv]
    mtbl = Table(mrows, colWidths=[120 * mm, 56 * mm])
    mtbl.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -2), 0.4, C('#eef2f7')),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(mtbl)

    # ── Interpretación + recomendaciones + metodología ───────────────────────
    story.append(section('Expert Interpretation', 'interp'))
    interp = Table([[Paragraph(esc(interpretation(d)), s_body)]], colWidths=[176 * mm])
    interp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C(B['bg'])),
        ('LINEBEFORE', (0, 0), (0, -1), 2.2, C(B['primary'])),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10), ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(interp)

    story.append(section('Recommendations', 'recs'))
    for r in recommendations(d):
        story.append(Paragraph(f'<font color="{B["primary"]}">→</font>&nbsp;&nbsp;{esc(r)}',
                               st('rrec', parent=s_body, spaceAfter=3)))

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        '<b>Methodology notice.</b> AI-detection, source-similarity and citation scores are produced by '
        'automated statistical analysis. They are support indicators intended to guide human review and '
        'must not be used, in isolation, as a definitive determination of academic misconduct.',
        st('rmeth', parent=s_lbl, leading=10)))

    # ── Doc + pie por página ─────────────────────────────────────────────────
    buf = io.BytesIO()
    created_s = d['created'].strftime('%Y-%m-%d %H:%M UTC')
    footer_left = f"XplagiaX · Report {d['history_id'][:8]} · Verification {d['checksum'][:16]}"
    footer_right = f'Generated {created_s} · Confidential'

    from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame

    class _Doc(BaseDocTemplate):
        def afterFlowable(self, flowable):
            if isinstance(flowable, Paragraph) and flowable.style.name == 'rh2':
                txt = flowable.getPlainText()
                key = 'sec-%d' % self.canv.getPageNumber() + txt[:12]
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(txt, key, level=0, closed=False)

    def _page(canv, doc_):
        canv.saveState()
        canv.setFont('Helvetica', 6.6)
        canv.setFillColor(C(B['muted']))
        canv.drawString(18 * mm, 10 * mm, footer_left)
        canv.drawRightString(198 * mm, 10 * mm, f'{footer_right} · Page {canv.getPageNumber()}')
        canv.setStrokeColor(C(B['line']))
        canv.setLineWidth(0.5)
        canv.line(18 * mm, 13 * mm, 198 * mm, 13 * mm)
        canv.restoreState()

    doc = _Doc(buf, pagesize=LETTER, title=f"XplagiaX Academic Integrity Report — {d['title'][:80]}",
               author='XplagiaX', leftMargin=18 * mm, rightMargin=18 * mm,
               topMargin=15 * mm, bottomMargin=18 * mm)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='main')
    doc.addPageTemplates([PageTemplate(id='page', frames=[frame], onPage=_page)])
    doc.build(story)
    return buf.getvalue()
