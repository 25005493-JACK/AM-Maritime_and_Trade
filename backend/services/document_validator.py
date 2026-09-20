import os
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

from backend.services.pdf_inspector import classify_pdf

REQUIRED_SI_FIELDS = [
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg"
]

NON_SI_SIGNATURES = [
    (re.compile(r'\b(?:booking\s*confirmation|booking\s*advice|booking\s*note|booking\s*details|booking\s*acknowledgement)\b', re.I), "booking_confirmation"),
    (re.compile(r'\b(?:commercial\s*invoice|proforma\s*invoice|invoice\s*no\.?)\b', re.I), "commercial_invoice"),
    (re.compile(r'\b(?:packing\s*list|packing\s*note|delivery\s*note)\b', re.I), "packing_list"),
    (re.compile(r'\b(?:certificate\s*of\s*origin|co\s*certificate)\b', re.I), "certificate_of_origin"),
    (re.compile(r'\b(?:freight\s*quotation|rate\s*quotation|quotation)\b', re.I), "quotation"),
]

def assess_document_validity(
    extracted_fields: Any,
    doc_type_guess: str = "si",
    raw_text: str = "",
    file_path: Optional[str] = None,
    min_coverage: float = 0.6,
    required_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Layer 2 Check: Assesses whether an attachment qualifies as a valid, comparable SI.
    Decoupled from email intent (what the email text asked for).

    Checks:
    1. Unreadable / Scanned PDF check before attempting field matching.
    2. Non-SI document signature check (e.g. Booking Confirmation, Commercial Invoice, Quote).
    3. Field coverage ratio calculation against required SI fields.

    Returns:
    {
        "doc_type_guess": "si" | "booking_confirmation" | "commercial_invoice" | "packing_list" | "quotation" | "unknown" | "unreadable",
        "coverage_ratio": float,  # 0.0 to 1.0
        "matched_fields": List[str],
        "missing_fields": List[str],
        "is_comparable": bool,
        "min_coverage_threshold": float,
        "reason": str
    }
    """
    req_fields = required_fields or REQUIRED_SI_FIELDS
    total_required = len(req_fields)

    # 1. Check for unreadable or scan-quality issues
    if file_path and os.path.exists(file_path):
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            try:
                pdf_type = classify_pdf(file_path)
                if pdf_type == "scanned":
                    return {
                        "doc_type_guess": "unreadable",
                        "coverage_ratio": 0.0,
                        "matched_fields": [],
                        "missing_fields": req_fields.copy(),
                        "is_comparable": False,
                        "min_coverage_threshold": min_coverage,
                        "reason": "Attachment is a low-quality or scanned image-only PDF without searchable text."
                    }
            except Exception as e:
                return {
                    "doc_type_guess": "unreadable",
                    "coverage_ratio": 0.0,
                    "matched_fields": [],
                    "missing_fields": req_fields.copy(),
                    "is_comparable": False,
                    "min_coverage_threshold": min_coverage,
                    "reason": f"Attachment is corrupted, damaged, or unreadable: {str(e)}"
                }

    # Also check raw_text unreadable markers
    if raw_text:
        raw_lower = raw_text.lower()
        if any(marker in raw_lower for marker in ["[unreadable", "[read_error", "failed to open", "damaged text"]):
            return {
                "doc_type_guess": "unreadable",
                "coverage_ratio": 0.0,
                "matched_fields": [],
                "missing_fields": req_fields.copy(),
                "is_comparable": False,
                "min_coverage_threshold": min_coverage,
                "reason": "Attachment text contains unreadable or damaged markers."
            }

    # 2. Check for explicit Non-SI document headers
    detected_type = (doc_type_guess or "unknown").lower()
    text_to_scan = raw_text[:1000] if raw_text else ""
    if text_to_scan:
        for pat, kind in NON_SI_SIGNATURES:
            if pat.search(text_to_scan):
                detected_type = kind
                break

    # If document type is known non-SI, immediately mark as not comparable
    if detected_type in ("booking_confirmation", "commercial_invoice", "packing_list", "certificate_of_origin", "quotation"):
        readable_kind = detected_type.replace('_', ' ').title()
        return {
            "doc_type_guess": detected_type,
            "coverage_ratio": 0.0,
            "matched_fields": [],
            "missing_fields": req_fields.copy(),
            "is_comparable": False,
            "min_coverage_threshold": min_coverage,
            "reason": f"Attachment is detected as a {readable_kind}, not a Shipping Instruction (SI)."
        }

    # 3. Calculate field coverage ratio
    matched_fields: List[str] = []
    missing_fields: List[str] = []

    # Support dict or ExtractionResult
    fields_dict = extracted_fields
    if hasattr(extracted_fields, "fields"):
        fields_dict = extracted_fields.fields
    elif hasattr(extracted_fields, "to_dict"):
        fields_dict = extracted_fields.to_dict()

    if not isinstance(fields_dict, dict):
        fields_dict = {}

    for f in req_fields:
        val = fields_dict.get(f)
        if val is not None and str(val).strip() != "" and str(val).strip().upper() not in ("N/A", "NONE", "BLANK", "-"):
            matched_fields.append(f)
        else:
            missing_fields.append(f)

    coverage_ratio = round(len(matched_fields) / total_required, 3) if total_required > 0 else 0.0

    # Determine if comparable
    if coverage_ratio >= min_coverage:
        is_comparable = True
        reason = f"Document qualifies as comparable SI with {coverage_ratio:.1%} field coverage ({len(matched_fields)}/{total_required} fields)."
        detected_type = "si"
    else:
        is_comparable = False
        detected_type = detected_type if detected_type not in ("si", "unknown") else "not_a_valid_si"
        reason = f"Attachment coverage ({coverage_ratio:.1%}) is below threshold ({min_coverage:.1%}). Missing fields: {', '.join(missing_fields)}."

    return {
        "doc_type_guess": detected_type,
        "coverage_ratio": coverage_ratio,
        "matched_fields": matched_fields,
        "missing_fields": missing_fields,
        "is_comparable": is_comparable,
        "min_coverage_threshold": min_coverage,
        "reason": reason
    }
