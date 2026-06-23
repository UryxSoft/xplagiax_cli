"""
OCR utility for scanned PDFs.
Optimized for speed and low resource usage in a multi-worker Flask context.
"""
import os
import fitz
import logging
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


def ocr_pdf_to_searchable(
    input_path: str,
    output_path: Optional[str] = None,
    jobs: int = 2,
    page_timeout: int = 30,
) -> Optional[str]:
    """
    Runs OCR on a scanned PDF and returns the path to a searchable version.

    Key optimizations vs the original OcrDocument class:
    - No pandas: removes 20 MB import overhead
    - No class: plain function with zero state management cost
    - optimize=0: skips post-OCR PDF compression (~30% faster)
    - output_type='pdf': skips PDF/A conformance validation step
    - jobs=2: caps tesseract CPU threads (avoids saturation in Gunicorn multi-worker)
    - use_threads=True: threading instead of subprocesses (lower memory overhead)
    - tesseract_timeout: per-page timeout prevents hung pages from blocking forever
    - progress_bar=False: no stdout pollution in a web context
    - skip_text=True: only OCRs pages that have no text layer (hybrid-doc safe)
    - Does NOT modify or delete the original file

    Args:
        input_path:   Absolute path to the scanned PDF
        output_path:  Where to write the searchable PDF. Uses a tempfile if None.
        jobs:         Max parallel tesseract workers. Keep ≤2 in multi-worker deploys.
        page_timeout: Seconds before tesseract gives up on a single page.

    Returns:
        Path to the OCR'd PDF, or None if OCR failed.
    """
    try:
        import ocrmypdf
    except ImportError:
        logger.error("ocrmypdf not installed: pip install ocrmypdf")
        return None

    owns_output = output_path is None
    if owns_output:
        fd, output_path = tempfile.mkstemp(suffix='_ocr.pdf')
        os.close(fd)

    try:
        ocrmypdf.ocr(
            input_path,
            output_path,
            output_type='pdf',           # Plain PDF — skips PDF/A conformance step
            skip_text=True,              # Don't re-OCR pages that already have text
            deskew=False,                # Faster; enable for physically-skewed scans
            optimize=0,                  # Skip lossless optimization (~30% time saved)
            jobs=jobs,                   # Cap tesseract thread count
            use_threads=True,            # Threads vs processes: lower memory overhead
            tesseract_timeout=page_timeout,
            progress_bar=False,          # No stdout noise in web context
        )

        with fitz.open(output_path) as check:
            if len(check) == 0:
                logger.error("OCR produced an empty PDF")
                return None

        logger.info(f"OCR completed → {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"OCR failed for {os.path.basename(input_path)}: {e}")
        if owns_output and os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except OSError:
                pass
        return None
