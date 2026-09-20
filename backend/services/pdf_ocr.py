"""PyMuPDF text extraction with OCR fallback and a measured OCR benchmark.

Searchable PDF text is the reference for the benchmark. Image-only pages do not
have a reference transcript, so their OCR accuracy is deliberately unreported.
"""

from __future__ import annotations

import re
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import pymupdf


TESSDATA_DIR = Path(__file__).resolve().parents[1] / "tessdata"
OCR_LANGUAGE = "eng"
OCR_DPI = 200
MIN_TEXT_CHARS = 25
_OCR_LOCK = threading.Lock()


def _tessdata_path() -> str | None:
    """Prefer the bundled language model so local Windows runs need no installer."""
    return str(TESSDATA_DIR) if (TESSDATA_DIR / "eng.traineddata").is_file() else None


def _has_searchable_text(text: str) -> bool:
    return len(re.sub(r"\W", "", text, flags=re.UNICODE)) >= MIN_TEXT_CHARS


def _ocr_page(page: pymupdf.Page) -> str:
    # MuPDF/Leptonica OCR is not safe when concurrent FastAPI requests use it.
    with _OCR_LOCK:
        text_page = page.get_textpage_ocr(
            language=OCR_LANGUAGE,
            dpi=OCR_DPI,
            full=True,
            tessdata=_tessdata_path(),
        )
        return page.get_text(textpage=text_page, sort=True).strip()


def _file_key(path: str | Path) -> tuple[str, int, int]:
    resolved = Path(path).resolve()
    stat = resolved.stat()
    return str(resolved), stat.st_mtime_ns, stat.st_size


@lru_cache(maxsize=256)
def _extract_cached(path: str, mtime_ns: int, size: int) -> Dict[str, Any]:
    del mtime_ns, size  # Cache keys invalidate results when a PDF changes.
    pages = []
    try:
        with pymupdf.open(path) as document:
            for number, page in enumerate(document, start=1):
                native_text = page.get_text(sort=True).strip()
                if _has_searchable_text(native_text):
                    pages.append({
                        "page": number,
                        "method": "text_layer",
                        "text": native_text,
                        "error": None,
                    })
                    continue

                try:
                    ocr_text = _ocr_page(page)
                    pages.append({
                        "page": number,
                        "method": "ocr",
                        "text": ocr_text,
                        "error": None if ocr_text else "OCR found no readable text on this page.",
                    })
                except Exception as exc:
                    pages.append({
                        "page": number,
                        "method": "ocr",
                        "text": "",
                        "error": f"OCR could not read this page: {exc}",
                    })
    except Exception as exc:
        return {
            "status": "unreadable",
            "error": "PDF could not be opened. The file may be missing or damaged.",
            "page_count": 0,
            "text_page_count": 0,
            "ocr_page_count": 0,
            "text": "",
            "pages": [],
        }

    errors = [page["error"] for page in pages if page["error"]]
    text = "\n\n".join(page["text"] for page in pages if page["text"])
    return {
        "status": "ready" if text and not errors else "needs_review",
        "error": "; ".join(errors) if errors else None,
        "page_count": len(pages),
        "text_page_count": sum(page["method"] == "text_layer" for page in pages),
        "ocr_page_count": sum(page["method"] == "ocr" for page in pages),
        "text": text,
        "pages": pages,
    }


def extract_pdf(path: str | Path) -> Dict[str, Any]:
    """Read searchable pages directly and OCR image-only pages once per file."""
    try:
        return _extract_cached(*_file_key(path))
    except OSError as exc:
        return {
            "status": "unreadable",
            "error": "PDF could not be opened. The file may be missing or damaged.",
            "page_count": 0,
            "text_page_count": 0,
            "ocr_page_count": 0,
            "text": "",
            "pages": [],
        }


def _normalise_for_comparison(text: str) -> str:
    # Ignore case and whitespace layout; retain characters and punctuation.
    return " ".join(text.casefold().split())


def _edit_distance(reference: str, candidate: str) -> int:
    """Character edit distance using two rows of memory."""
    if len(reference) < len(candidate):
        reference, candidate = candidate, reference
    previous = list(range(len(candidate) + 1))
    for row, char_a in enumerate(reference, start=1):
        current = [row]
        for col, char_b in enumerate(candidate, start=1):
            current.append(min(
                current[-1] + 1,
                previous[col] + 1,
                previous[col - 1] + (char_a != char_b),
            ))
        previous = current
    return previous[-1]


@lru_cache(maxsize=256)
def _benchmark_cached(path: str, mtime_ns: int, size: int) -> Dict[str, Any]:
    del mtime_ns, size
    reference_chars = 0
    edit_count = 0
    benchmark_pages = 0
    errors = []
    try:
        with pymupdf.open(path) as document:
            for number, page in enumerate(document, start=1):
                reference = _normalise_for_comparison(page.get_text(sort=True))
                if not _has_searchable_text(reference):
                    continue
                try:
                    candidate = _normalise_for_comparison(_ocr_page(page))
                    edit_count += _edit_distance(reference, candidate)
                    reference_chars += len(reference)
                    benchmark_pages += 1
                except Exception as exc:
                    errors.append(f"Page {number}: {exc}")
    except Exception as exc:
        errors.append(str(exc))

    accuracy = None
    if reference_chars:
        accuracy = round(max(0.0, 1.0 - edit_count / reference_chars) * 100, 1)
    return {
        "accuracy_pct": accuracy,
        "reference_chars": reference_chars,
        "edit_count": edit_count,
        "benchmark_pages": benchmark_pages,
        "error": "; ".join(errors) if errors else None,
    }


def benchmark_pdf(path: str | Path) -> Dict[str, Any]:
    """Compare OCR with the PDF's own searchable text, when one exists."""
    try:
        return _benchmark_cached(*_file_key(path))
    except OSError as exc:
        return {
            "accuracy_pct": None,
            "reference_chars": 0,
            "edit_count": 0,
            "benchmark_pages": 0,
            "error": str(exc),
        }
