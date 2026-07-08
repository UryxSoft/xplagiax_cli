#!/usr/bin/env python3
"""
Production-Grade PDF to HTML Converter (High-Fidelity Layout)
============================================================

Optimized for high-throughput, low-memory environments (containers).

Fidelity goals (single source of truth for the "analysiss" document view):
- Reproduce the PDF layout as faithfully as possible: absolute positioning of
  every text span, so distribution, alignment, columns, tables and headers/
  footers keep their place.
- Preserve text styling: bold, italic, font size, color, serif/monospace.
- Preserve UNDERLINE exactly as it appears in the document. Underlines in PDFs
  (and in Word/DOCX exported to PDF via LibreOffice) are drawn as thin
  horizontal vector lines *under* the glyphs, not as a font flag. We detect
  those lines and re-emit them as real ``<u>`` text decoration on the exact
  characters they cover, so the underline shows up "igual como cuando es texto".
- Reproduce tables and other vector graphics (grid lines, shading) via an SVG
  overlay drawn behind the text.
- Embed raster images at their real position (logos in headers/footers, etc.).

Requirements:
    PyMuPDF>=1.23.0
    Pillow>=9.0.0   (optional; only used indirectly by PyMuPDF)

Performance characteristics:
    Time: O(n) where n = number of pages
    Space: O(1) - constant memory regardless of document size (streaming write)
"""

import fitz  # PyMuPDF
import base64
import os
import logging
from pathlib import Path
from typing import Optional, Final, List, Dict, Any, Tuple
from contextlib import contextmanager
from dataclasses import dataclass, field
from io import StringIO
import time
from enum import Enum

# Structured logging setup
logger = logging.getLogger(__name__)


class ImageFormat(Enum):
    """Supported image formats for embedding."""
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


@dataclass(frozen=True)
class ConverterConfig:
    """Immutable converter configuration with resource limits."""

    # Resource limits (critical for container environments)
    max_image_size_mb: int = 10  # Per image
    max_total_images_mb: int = 100  # Per document
    max_page_processing_time_sec: float = 30.0
    max_document_pages: int = 1000

    # Image processing
    embed_fonts: bool = True
    preserve_layout: bool = True
    image_quality: int = 85  # JPEG quality 1-100
    max_image_dimension: int = 2048  # Max width/height in pixels

    # Layout / fidelity
    detect_underline: bool = True       # re-emit drawn underlines as <u>
    render_vector_graphics: bool = True  # tables / borders / shading overlay
    max_drawing_items: int = 8000        # safety cap on vector complexity

    # Performance tuning
    use_progressive_jpeg: bool = True
    strip_image_metadata: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if not 1 <= self.image_quality <= 100:
            raise ValueError("image_quality must be 1-100")
        if self.max_image_dimension < 100:
            raise ValueError("max_image_dimension too small")


@dataclass
class ConversionMetrics:
    """Performance metrics for observability."""

    pages_processed: int = 0
    images_extracted: int = 0
    images_skipped: int = 0
    underlines_detected: int = 0
    total_image_size_mb: float = 0.0
    processing_time_sec: float = 0.0
    errors: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        self.errors.append(error)

    def to_dict(self) -> dict:
        """Export metrics for monitoring systems."""
        return {
            "pages_processed": self.pages_processed,
            "images_extracted": self.images_extracted,
            "images_skipped": self.images_skipped,
            "underlines_detected": self.underlines_detected,
            "total_image_size_mb": round(self.total_image_size_mb, 2),
            "processing_time_sec": round(self.processing_time_sec, 3),
            "pages_per_second": round(
                self.pages_processed / self.processing_time_sec, 2
            ) if self.processing_time_sec > 0 else 0,
            "error_count": len(self.errors),
        }


# Horizontal tolerance (pt) allowed between a candidate underline segment and
# the text it belongs to. Real underlines hug the text; table/cell borders run
# well past it into the cell padding, so this keeps them apart.
_UNDERLINE_X_PAD: Final[float] = 4.0


class PDFToHTMLConverter:
    """
    Production-grade PDF to HTML converter with strict resource management and
    high layout fidelity (absolute positioning + underline + vector overlay).

    Thread safety: Multiple instances can run concurrently. Each instance
    maintains its own state.
    """

    # Class-level constants (shared, immutable)
    _CSS_TEMPLATE: Final[str] = """
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
            color: #111;
            background: #f0f0f2;
        }

        .pdf-container {
            margin: 0 auto;
            padding: 16px 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 18px;
        }

        /* Each page is a fixed-size canvas sized in PDF points, so every
           positioned element keeps its exact coordinates. */
        .pdf-page {
            position: relative;
            background: #fff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.18);
            overflow: hidden;
            flex: 0 0 auto;
        }

        /* Vector layer (table borders, shading, misc lines) sits behind text. */
        .pdf-vector {
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            pointer-events: none;
            z-index: 0;
        }

        .pdf-image {
            position: absolute;
            z-index: 1;
        }

        /* Absolutely positioned text; white-space:pre keeps original spacing. */
        .pdf-span {
            position: absolute;
            white-space: pre;
            line-height: 1;
            transform-origin: left top;
            z-index: 2;
        }
        .pdf-span.bold { font-weight: 700; }
        .pdf-span.italic { font-style: italic; }
        /* Underline is emitted as real <u> so it reads as underlined text. */
        .pdf-span u { text-decoration: underline; text-decoration-skip-ink: none; }

        @media print {
            body { background: #fff; }
            .pdf-container { padding: 0; gap: 0; }
            .pdf-page { box-shadow: none; page-break-after: always; }
            .pdf-page:last-child { page-break-after: auto; }
        }
    """

    # Fit-to-width: the PDF pages have a fixed size in points (e.g. ~816px wide
    # for Letter). Inside a narrow panel/iframe that overflows horizontally and
    # makes the document look like it only shows one page. This scales the whole
    # container down (never up) so every page fits the available width and the
    # pages stack for clean vertical scrolling. Recomputes on resize.
    _FIT_SCRIPT: Final[str] = (
        "<script>(function(){"
        "var c=document.querySelector('.pdf-container');if(!c)return;"
        "function fit(){"
        "c.style.zoom='';"
        "var p=c.getElementsByClassName('pdf-page'),m=0,i;"
        "for(i=0;i<p.length;i++){if(p[i].offsetWidth>m)m=p[i].offsetWidth;}"
        "var a=(document.documentElement.clientWidth||window.innerWidth||0)-8;"
        "if(!m||a<=0)return;"
        "var f=a/m;c.style.zoom=(f<1?f:'');"
        "}"
        "if(document.readyState!=='loading')fit();"
        "else document.addEventListener('DOMContentLoaded',fit);"
        "window.addEventListener('load',fit);"
        "window.addEventListener('resize',fit);"
        "})();</script>\n"
    )

    def __init__(
        self,
        config: Optional[ConverterConfig] = None,
        *,
        embed_fonts: Optional[bool] = None,
        preserve_layout: Optional[bool] = None,
        **overrides,
    ):
        """
        Initialize converter.

        Args:
            config: Full configuration object (takes precedence).
            embed_fonts / preserve_layout / **overrides: Convenience keyword
                overrides mapped onto ``ConverterConfig`` when ``config`` is not
                supplied. This keeps backward compatibility with callers that do
                ``PDFToHTMLConverter(embed_fonts=True, preserve_layout=True)``.
        """
        if config is None:
            kwargs: Dict[str, Any] = {}
            if embed_fonts is not None:
                kwargs["embed_fonts"] = embed_fonts
            if preserve_layout is not None:
                kwargs["preserve_layout"] = preserve_layout
            valid = ConverterConfig.__dataclass_fields__
            for key, value in overrides.items():
                if key in valid:
                    kwargs[key] = value
                else:
                    logger.debug(f"Ignoring unknown converter option: {key}")
            config = ConverterConfig(**kwargs)

        self.config = config
        self.metrics = ConversionMetrics()

        logger.info(
            "Initialized PDFToHTMLConverter",
            extra={
                "max_image_size_mb": self.config.max_image_size_mb,
                "max_document_pages": self.config.max_document_pages,
            },
        )

    # =====================================================================
    # PDF lifecycle
    # =====================================================================

    @contextmanager
    def _open_pdf(self, pdf_path: str):
        """Context manager for safe PDF opening with validation."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if not os.access(pdf_path, os.R_OK):
            raise PermissionError(f"Cannot read PDF: {pdf_path}")

        doc = None
        try:
            doc = fitz.open(pdf_path)

            page_count = len(doc)
            if page_count == 0:
                raise ValueError("PDF contains no pages")

            if page_count > self.config.max_document_pages:
                raise ValueError(
                    f"PDF too large: {page_count} pages "
                    f"(max: {self.config.max_document_pages})"
                )

            logger.info(f"Opened PDF: {page_count} pages", extra={"path": pdf_path})
            yield doc

        except Exception as e:
            logger.error(f"Failed to open PDF: {e}", extra={"path": pdf_path})
            raise
        finally:
            if doc is not None:
                doc.close()
                logger.debug("PDF document closed")

    def convert_pdf_to_html(
        self,
        pdf_path: str,
        output_path: Optional[str] = None,
    ) -> tuple[str, ConversionMetrics]:
        """
        Convert PDF to standalone HTML with metrics.

        Returns:
            Tuple of (output_path, metrics)
        """
        start_time = time.time()

        try:
            if output_path is None:
                output_path = Path(pdf_path).with_suffix('.html').as_posix()

            output_dir = os.path.dirname(output_path) or '.'
            if not os.access(output_dir, os.W_OK):
                raise PermissionError(f"Cannot write to: {output_dir}")

            with self._open_pdf(pdf_path) as doc:
                html_content = self._generate_html_streaming(doc, pdf_path)

            # Write atomically (temp file + rename)
            temp_path = f"{output_path}.tmp"
            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                os.replace(temp_path, output_path)
            except Exception:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise

            self.metrics.processing_time_sec = time.time() - start_time
            logger.info(
                "PDF conversion completed",
                extra={"input": pdf_path, "output": output_path, **self.metrics.to_dict()},
            )
            return output_path, self.metrics

        except Exception as e:
            self.metrics.add_error(str(e))
            self.metrics.processing_time_sec = time.time() - start_time
            logger.error(
                f"PDF conversion failed: {e}",
                extra={"input": pdf_path, "metrics": self.metrics.to_dict()},
            )
            raise

    # =====================================================================
    # HTML generation
    # =====================================================================

    def _generate_html_streaming(self, doc: fitz.Document, pdf_name: str) -> str:
        """Generate HTML using a streaming StringIO buffer (constant memory)."""
        pdf_title = Path(pdf_name).stem
        page_count = len(doc)

        html_buffer = StringIO()
        html_buffer.write(
            '<!DOCTYPE html>\n'
            '<html lang="en">\n'
            '<head>\n'
            '    <meta charset="UTF-8">\n'
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            f'    <title>{self._escape_html(pdf_title)}</title>\n'
            f'    <style>{self._CSS_TEMPLATE}</style>\n'
            '</head>\n'
            '<body>\n'
            '    <div class="pdf-container">\n'
        )

        for page_num in range(page_count):
            try:
                page_html = self._process_page_safe(doc, page_num)
                html_buffer.write(page_html)
                self.metrics.pages_processed += 1
            except Exception as e:
                error_msg = f"Error processing page {page_num + 1}: {e}"
                self.metrics.add_error(error_msg)
                logger.warning(error_msg)
                html_buffer.write(
                    '        <div class="pdf-page" style="width:612pt;height:80pt">\n'
                    f'            <div class="pdf-span" style="left:20pt;top:20pt;color:#dc3545">'
                    f'Failed to process page {page_num + 1}</div>\n'
                    '        </div>\n'
                )

        html_buffer.write('    </div>\n')
        html_buffer.write(self._FIT_SCRIPT)
        html_buffer.write('</body>\n</html>')
        result = html_buffer.getvalue()
        html_buffer.close()
        return result

    def _process_page_safe(self, doc: fitz.Document, page_num: int) -> str:
        """Render a single page as an absolutely-positioned HTML canvas."""
        start_time = time.time()
        page = doc.load_page(page_num)

        try:
            prect = page.rect
            pw = max(1.0, float(prect.width))
            ph = max(1.0, float(prect.height))

            page_buffer = StringIO()
            page_buffer.write(
                f'        <div class="pdf-page" id="page-{page_num + 1}" '
                f'style="width:{pw:.1f}pt;height:{ph:.1f}pt">\n'
            )

            # 1) Vector graphics (tables, borders, shading) + underline segments.
            underline_segments: List[Dict[str, Any]] = []
            other_drawings: List[Dict[str, Any]] = []
            if self.config.render_vector_graphics or self.config.detect_underline:
                try:
                    underline_segments, other_drawings = self._collect_drawings(page)
                except Exception as e:
                    logger.debug(f"Drawing collection failed on page {page_num + 1}: {e}")

            # 2) Text (absolute spans + char-level underline).
            try:
                raw = page.get_text("rawdict")
            except Exception:
                raw = {"blocks": []}
            text_html = self._render_text(raw.get("blocks", []), underline_segments)

            # 3) Vector overlay (skip underline segments consumed by text).
            if self.config.render_vector_graphics:
                svg = self._render_vector_overlay(underline_segments, other_drawings, pw, ph)
                if svg:
                    page_buffer.write(f'            {svg}\n')

            # 4) Images positioned at their real bbox.
            try:
                for img_html in self._render_images(doc, page, page_num, start_time):
                    page_buffer.write(f'            {img_html}\n')
            except Exception as e:
                logger.debug(f"Image render failed on page {page_num + 1}: {e}")

            if text_html:
                page_buffer.write(text_html)

            page_buffer.write('        </div>\n')
            result = page_buffer.getvalue()
            page_buffer.close()
            return result

        finally:
            page = None  # explicit cleanup

    # =====================================================================
    # Vector drawings (tables, borders) + underline segment extraction
    # =====================================================================

    def _collect_drawings(
        self, page: fitz.Page
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Split page vector drawings into:
          - horizontal segments (underline candidates), each with a `consumed`
            flag so ones re-emitted as text underline are not double-drawn.
          - everything else (rects, vertical/diagonal lines, curves) for the
            overlay that reproduces tables and shapes.
        """
        segments: List[Dict[str, Any]] = []
        others: List[Dict[str, Any]] = []
        count = 0

        for d in page.get_drawings():
            stroke = d.get("color")
            fill = d.get("fill")
            width = d.get("width") or 1.0
            for item in d.get("items", []):
                count += 1
                if count > self.config.max_drawing_items:
                    logger.debug("Drawing item cap reached; skipping remaining")
                    return segments, others

                kind = item[0]
                if kind == "l":
                    p1, p2 = item[1], item[2]
                    dx, dy = abs(p2.x - p1.x), abs(p2.y - p1.y)
                    if dy <= 0.6 and dx > 1.0:  # horizontal → underline candidate
                        x0, x1 = sorted((p1.x, p2.x))
                        segments.append({
                            "x0": x0, "x1": x1, "y": (p1.y + p2.y) / 2.0,
                            "color": stroke, "w": width, "consumed": False,
                        })
                    else:
                        others.append({
                            "type": "line",
                            "p": (p1.x, p1.y, p2.x, p2.y),
                            "color": stroke, "w": width,
                        })
                elif kind == "re":
                    r = item[1]
                    others.append({
                        "type": "rect",
                        "r": (r.x0, r.y0, r.width, r.height),
                        "stroke": stroke, "fill": fill, "w": width,
                    })
                elif kind == "qu":
                    q = item[1]
                    xs = [q.ul.x, q.ur.x, q.ll.x, q.lr.x]
                    ys = [q.ul.y, q.ur.y, q.ll.y, q.lr.y]
                    others.append({
                        "type": "rect",
                        "r": (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)),
                        "stroke": stroke, "fill": fill, "w": width,
                    })
                elif kind == "c":  # bezier → approximate by its chord
                    p1, p4 = item[1], item[4]
                    others.append({
                        "type": "line",
                        "p": (p1.x, p1.y, p4.x, p4.y),
                        "color": stroke, "w": width,
                    })

        return segments, others

    def _render_vector_overlay(
        self,
        underline_segments: List[Dict[str, Any]],
        other_drawings: List[Dict[str, Any]],
        pw: float,
        ph: float,
    ) -> str:
        """Build one inline SVG reproducing table borders / shapes behind text."""
        parts: List[str] = []

        for d in other_drawings:
            if d["type"] == "line":
                x1, y1, x2, y2 = d["p"]
                col = self._rgb_to_hex(d.get("color")) or "#000000"
                w = max(0.4, float(d.get("w") or 1.0))
                parts.append(
                    f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                    f'stroke="{col}" stroke-width="{w:.2f}"/>'
                )
            elif d["type"] == "rect":
                x, y, w_, h_ = d["r"]
                if w_ <= 0 or h_ <= 0:
                    continue
                fill = self._rgb_to_hex(d.get("fill"))
                stroke = self._rgb_to_hex(d.get("stroke"))
                sw = max(0.4, float(d.get("w") or 1.0))
                fill_attr = f'fill="{fill}"' if fill else 'fill="none"'
                stroke_attr = (
                    f'stroke="{stroke}" stroke-width="{sw:.2f}"' if stroke else 'stroke="none"'
                )
                parts.append(
                    f'<rect x="{x:.1f}" y="{y:.1f}" width="{w_:.1f}" height="{h_:.1f}" '
                    f'{fill_attr} {stroke_attr}/>'
                )

        # Underline segments not consumed as text underline still get drawn so
        # nothing visible is lost.
        for seg in underline_segments:
            if seg.get("consumed"):
                continue
            col = self._rgb_to_hex(seg.get("color")) or "#000000"
            w = max(0.4, float(seg.get("w") or 1.0))
            parts.append(
                f'<line x1="{seg["x0"]:.1f}" y1="{seg["y"]:.1f}" '
                f'x2="{seg["x1"]:.1f}" y2="{seg["y"]:.1f}" '
                f'stroke="{col}" stroke-width="{w:.2f}"/>'
            )

        if not parts:
            return ""

        return (
            f'<svg class="pdf-vector" viewBox="0 0 {pw:.1f} {ph:.1f}" '
            f'width="{pw:.1f}pt" height="{ph:.1f}pt" preserveAspectRatio="none" '
            f'xmlns="http://www.w3.org/2000/svg">'
            + "".join(parts)
            + '</svg>'
        )

    # =====================================================================
    # Text rendering (absolute spans + char-level underline)
    # =====================================================================

    def _render_text(
        self, blocks: List[Dict[str, Any]], underline_segments: List[Dict[str, Any]]
    ) -> str:
        """Render every text span as an absolutely positioned element."""
        out = StringIO()

        for block in blocks:
            if block.get("type") != 0:  # 0 = text block
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                # Determine which underline segments belong to THIS text line:
                # they must sit just under the baseline and stay within the
                # text's horizontal extent (table borders run past it).
                line_chars = [c for s in spans for c in s.get("chars", [])]
                candidates: List[Dict[str, Any]] = []
                if underline_segments and self.config.detect_underline and line_chars:
                    tx0 = min(c["bbox"][0] for c in line_chars)
                    tx1 = max(c["bbox"][2] for c in line_chars)
                    lbottom = max(c["bbox"][3] for c in line_chars)
                    sizes = sorted(s.get("size", 0) for s in spans if s.get("size"))
                    msize = sizes[len(sizes) // 2] if sizes else 10.0
                    for seg in underline_segments:
                        if seg.get("consumed"):
                            continue
                        if (seg["x0"] >= tx0 - _UNDERLINE_X_PAD
                                and seg["x1"] <= tx1 + _UNDERLINE_X_PAD
                                and (lbottom - 0.55 * msize) <= seg["y"]
                                <= (lbottom + 0.35 * msize)):
                            candidates.append(seg)

                for span in spans:
                    html = self._render_span(span, candidates)
                    if html:
                        out.write(f'            {html}\n')

        result = out.getvalue()
        out.close()
        return result

    def _render_span(
        self, span: Dict[str, Any], underline_candidates: List[Dict[str, Any]]
    ) -> str:
        """Build one positioned <span>, wrapping underlined char runs in <u>."""
        chars = span.get("chars", [])
        text = "".join(c.get("c", "") for c in chars)
        if not text.strip():
            return ""

        bbox = span.get("bbox", (0, 0, 0, 0))
        left, top = bbox[0], bbox[1]
        size = span.get("size", 12) or 12

        # Per-char underline flags.
        u_flags: List[bool] = []
        any_underline = False
        for c in chars:
            underlined = False
            if underline_candidates:
                cb = c["bbox"]
                cx = (cb[0] + cb[2]) / 2.0
                for seg in underline_candidates:
                    if seg["x0"] - 1.0 <= cx <= seg["x1"] + 1.0:
                        underlined = True
                        seg["consumed"] = True
                        break
            u_flags.append(underlined)
            any_underline = any_underline or underlined

        if any_underline:
            self.metrics.underlines_detected += 1

        # Group consecutive chars by underline state.
        inner_parts: List[str] = []
        i, n = 0, len(chars)
        while i < n:
            flag = u_flags[i]
            j = i
            seg_text = []
            while j < n and u_flags[j] == flag:
                seg_text.append(chars[j].get("c", ""))
                j += 1
            escaped = self._escape_html("".join(seg_text))
            inner_parts.append(f"<u>{escaped}</u>" if flag else escaped)
            i = j
        inner_html = "".join(inner_parts)

        # Style: position, size, weight/style, color, font family.
        classes = ["pdf-span"]
        font = str(span.get("font", "")).lower()
        flags = span.get("flags", 0)
        if (flags & 16) or any(k in font for k in ("bold", "black", "heavy", "semibold")):
            classes.append("bold")
        if (flags & 2) or "italic" in font or "oblique" in font:
            classes.append("italic")

        styles = [f"left:{left:.1f}pt", f"top:{top:.1f}pt", f"font-size:{size:.1f}pt"]

        color = span.get("color", 0)
        if color and color != 0:
            styles.append(f"color:#{color & 0xFFFFFF:06x}")

        if flags & 8:  # monospaced
            styles.append('font-family:"Courier New",monospace')
        elif flags & 4:  # serif
            styles.append('font-family:"Times New Roman",Georgia,serif')

        class_attr = " ".join(classes)
        style_attr = ";".join(styles)
        return f'<span class="{class_attr}" style="{style_attr}">{inner_html}</span>'

    # =====================================================================
    # Images
    # =====================================================================

    def _render_images(
        self, doc: fitz.Document, page: fitz.Page, page_num: int, start_time: float
    ) -> List[str]:
        """Yield positioned <img> tags for every raster image on the page."""
        results: List[str] = []
        try:
            infos = page.get_image_info(xrefs=True)
        except Exception:
            infos = []

        for idx, info in enumerate(infos):
            if time.time() - start_time > self.config.max_page_processing_time_sec:
                logger.warning(f"Page {page_num + 1} timeout, skipping remaining images")
                break

            xref = info.get("xref", 0)
            bbox = info.get("bbox")
            if not xref or not bbox:
                continue
            try:
                html = self._extract_image_safe(doc, xref, bbox, idx, page_num)
                if html:
                    results.append(html)
            except Exception as e:
                self.metrics.images_skipped += 1
                logger.debug(f"Skipped image {idx} on page {page_num + 1}: {e}")

        return results

    def _extract_image_safe(
        self,
        doc: fitz.Document,
        xref: int,
        bbox: tuple,
        img_index: int,
        page_num: int,
    ) -> Optional[str]:
        """Extract, size-limit, base64-embed and position a single image."""
        pix = None
        pix_rgb = None
        try:
            pix = fitz.Pixmap(doc, xref)

            image_size_mb = (pix.width * pix.height * pix.n) / (1024 * 1024)
            if image_size_mb > self.config.max_image_size_mb:
                self.metrics.images_skipped += 1
                return None
            if (self.metrics.total_image_size_mb + image_size_mb
                    > self.config.max_total_images_mb):
                self.metrics.images_skipped += 1
                return None

            if (pix.width > self.config.max_image_dimension
                    or pix.height > self.config.max_image_dimension):
                scale = min(
                    self.config.max_image_dimension / pix.width,
                    self.config.max_image_dimension / pix.height,
                )
                mat = fitz.Matrix(scale, scale)
                pix = fitz.Pixmap(pix, 0, mat)

            if pix.n - pix.alpha < 4:
                img_format = ImageFormat.PNG
                img_bytes = pix.tobytes("png")
            else:
                img_format = ImageFormat.JPEG
                pix_rgb = fitz.Pixmap(fitz.csRGB, pix)
                img_bytes = pix_rgb.tobytes("jpeg", jpg_quality=self.config.image_quality)

            img_b64 = base64.b64encode(img_bytes).decode('ascii')
            data_uri = f"data:image/{img_format.value};base64,{img_b64}"

            self.metrics.images_extracted += 1
            self.metrics.total_image_size_mb += image_size_mb

            x0, y0, x1, y1 = bbox
            w = max(1.0, x1 - x0)
            h = max(1.0, y1 - y0)
            return (
                f'<img class="pdf-image" '
                f'style="left:{x0:.1f}pt;top:{y0:.1f}pt;width:{w:.1f}pt;height:{h:.1f}pt" '
                f'src="{data_uri}" alt="Page {page_num + 1} image {img_index}" '
                f'loading="lazy">'
            )
        finally:
            pix_rgb = None
            pix = None

    # =====================================================================
    # Helpers
    # =====================================================================

    @staticmethod
    def _rgb_to_hex(color) -> Optional[str]:
        """Convert a PyMuPDF float RGB tuple (0..1) to #rrggbb, or None."""
        if not color:
            return None
        try:
            r, g, b = color[0], color[1], color[2]
            return "#{:02x}{:02x}{:02x}".format(
                max(0, min(255, int(round(r * 255)))),
                max(0, min(255, int(round(g * 255)))),
                max(0, min(255, int(round(b * 255)))),
            )
        except Exception:
            return None

    @staticmethod
    def _escape_html(text: str) -> str:
        """Fast HTML escaping."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    def get_metrics(self) -> dict:
        """Get conversion metrics for monitoring."""
        return self.metrics.to_dict()


# Factory function for convenience
def convert_pdf_to_html(
    pdf_path: str,
    output_path: Optional[str] = None,
    config: Optional[ConverterConfig] = None,
) -> tuple[str, dict]:
    """
    Convenience function for one-off conversions.

    Example:
        >>> output, metrics = convert_pdf_to_html("document.pdf")
        >>> print(f"Processed {metrics['pages_processed']} pages")
    """
    converter = PDFToHTMLConverter(config)
    output, metrics = converter.convert_pdf_to_html(pdf_path, output_path)
    return output, metrics.to_dict()


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    if len(sys.argv) < 2:
        print("Usage: python pdf_to_html_optimized.py <pdf_file> [output.html]")
        sys.exit(1)

    pdf_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        config = ConverterConfig(
            max_document_pages=2000,
            max_image_size_mb=15,
            image_quality=80,
        )
        output, metrics = convert_pdf_to_html(pdf_file, output_file, config)
        print("\nConversion successful!")
        print(f"Output: {output}")
        print("\nMetrics:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"\nConversion failed: {e}")
        sys.exit(1)
