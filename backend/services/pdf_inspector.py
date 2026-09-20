import os
from typing import Optional

def classify_pdf(path: str) -> str:
    """
    Classifies a PDF attachment:
    - Returns 'text_based' if digital text can be extracted.
    - Returns 'scanned' if the document is an image-only scan without a selectable text layer.
    - Raises an Exception if the PDF is invalid, corrupted, or cannot be opened.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF file not found: {path}")

    if os.path.getsize(path) == 0:
        raise ValueError(f"PDF file is empty: {path}")

    # Use PyMuPDF (fitz) or pdfplumber to inspect pages
    try:
        import fitz
        doc = fitz.open(path)
        if len(doc) == 0:
            doc.close()
            raise ValueError("PDF has 0 pages")

        total_text = ""
        total_images = 0
        for page in doc:
            total_text += page.get_text() or ""
            total_images += len(page.get_images() or [])
        doc.close()

        # If minimal or no extractable text exists
        if len(total_text.strip()) < 20:
            return "scanned"
        return "text_based"
    except Exception as e:
        # Fallback inspection with pdfplumber if fitz is unavailable
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                if len(pdf.pages) == 0:
                    raise ValueError("PDF has 0 pages")
                total_text = ""
                for p in pdf.pages:
                    txt = p.extract_text() or ""
                    total_text += txt
                if len(total_text.strip()) < 20:
                    return "scanned"
                return "text_based"
        except Exception:
            # Re-raise the exception to indicate corrupted / invalid PDF
            raise e
