"""Read-only inventory and accuracy metrics for PDF attachments in the inbox."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from backend.services.extractor import extractor
from backend.services.pdf_ocr import benchmark_pdf, extract_pdf


SHIPMENT_FIELDS = (
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg",
)


def build_ocr_dashboard(loader: Any) -> Dict[str, Any]:
    documents = []
    total_reference_chars = 0
    total_edits = 0
    benchmark_pages = 0
    benchmark_errors = []

    for email in loader.load_inbox():
        for attachment in email.get("attachments", []):
            path = attachment.get("path", "") if isinstance(attachment, dict) else str(attachment)
            if Path(path).suffix.lower() != ".pdf":
                continue

            filename = attachment.get("filename") if isinstance(attachment, dict) else None
            filename = filename or Path(path).name
            doc_type = attachment.get("doc_type", "OTHER") if isinstance(attachment, dict) else "OTHER"
            full_path = loader.resolve_attachment_path(path)
            result = extract_pdf(full_path)
            benchmark = benchmark_pdf(full_path) if result["text_page_count"] else None

            if benchmark:
                total_reference_chars += benchmark["reference_chars"]
                total_edits += benchmark["edit_count"]
                benchmark_pages += benchmark["benchmark_pages"]
                if benchmark["error"]:
                    benchmark_errors.append(f"{filename}: {benchmark['error']}")

            fields_found = []
            if result["text"]:
                extracted = extractor.extract_fields(result["text"], doc_type_hint=doc_type)
                fields_found = [field for field in SHIPMENT_FIELDS if extracted.get(field) is not None]

            status = result["status"]
            if result["ocr_page_count"] and len(fields_found) < len(SHIPMENT_FIELDS):
                status = "needs_review"

            match = re.search(r"(\d+)$", email["id"])
            documents.append({
                "email_id": email["id"],
                "email_number": int(match.group(1)) if match else None,
                "subject": email.get("subject", ""),
                "filename": filename,
                "document_type": doc_type,
                "status": status,
                "method": "OCR" if result["ocr_page_count"] else (
                    "Text layer" if result["text_page_count"] else "Unreadable"
                ),
                "page_count": result["page_count"],
                "ocr_page_count": result["ocr_page_count"],
                "text_page_count": result["text_page_count"],
                "character_count": len(result["text"]),
                "field_count": len(fields_found),
                "fields_found": fields_found,
                "benchmark_accuracy_pct": benchmark["accuracy_pct"] if benchmark else None,
                "benchmark_pages": benchmark["benchmark_pages"] if benchmark else 0,
                "error": result["error"],
                "text": result["text"],
            })

    documents.sort(key=lambda doc: (doc["email_number"] or 0, doc["document_type"] != "SI"))
    ocr_documents = [doc for doc in documents if doc["ocr_page_count"]]
    accuracy = None
    if total_reference_chars:
        accuracy = round(max(0.0, 1.0 - total_edits / total_reference_chars) * 100, 1)

    return {
        "summary": {
            "total_pdfs": len(documents),
            "searchable_pdfs": sum(doc["method"] == "Text layer" for doc in documents),
            "ocr_pdfs": len(ocr_documents),
            "needs_review": sum(doc["status"] != "ready" for doc in documents),
            "ocr_accuracy_pct": accuracy,
            "benchmark_pages": benchmark_pages,
            "reference_characters": total_reference_chars,
            "scan_pages_without_reference": sum(doc["ocr_page_count"] for doc in documents),
            "ocr_field_coverage_pct": round(
                sum(doc["field_count"] for doc in ocr_documents) / (7 * len(ocr_documents)) * 100,
                1,
            ) if ocr_documents else None,
            "benchmark_warning": benchmark_errors[0] if benchmark_errors else None,
        },
        "documents": documents,
    }
