"""
Multi-source field evidence.

Builds the reviewer-facing evidence record for a single field:

    {
      "dcsa_field": "portOfDischarge" | null,
      "value": ...,
      "sources": [ {"document": ..., "value": ..., "char_offset": ..., "exact_text": ...} ],
      "validation": {"source_match": ..., "whitelist": {"status": ..., "table": ...}},
      "agreement": "match" | "conflict"
    }

What this is (and is not): it presents *evidence* - where a value came from, in
which document, at which offset - plus mechanical checks (source span located,
code-list lookup). It is deliberately NOT a certificate: no hash, no signature,
no claim of legal validity. `source_match` only states that the extracted value
could be located in the text that was extracted from.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.services.port_lookup import port_lookup
from backend.services.anchor_triage import _validate_container_number

WHITELIST_TABLES = {
    "port_of_loading": "UN/LOCODE",
    "port_of_discharge": "UN/LOCODE",
    "container_count": "ISO 6346",
}

_CONTAINER_RE = re.compile(r'\b[A-Z]{4}\d{7}\b')


def locate_span(text: str, value: Any, allow_partial: bool = False) -> Optional[Dict[str, Any]]:
    """Locate full normalized ``value`` inside ``text`` and return start_char, end_char, offset, line, and quoted text.

    In strict provenance mode (allow_partial=False, the default), partial matches (e.g. matching
    only the first token or arbitrary prefix) are strictly rejected. The entire normalized value
    must appear in the source text.
    """
    if text is None or value is None:
        return None
    needle = str(value).strip()
    if not needle:
        return None

    collapsed = re.sub(r'\s+', ' ', needle)
    idx = -1
    matched_len = 0
    match_type = "exact"

    # Strategy 1: Exact verbatim match
    idx = text.find(needle)
    if idx >= 0:
        matched_len = len(needle)
        match_type = "exact"
    else:
        # Strategy 2: Case-insensitive verbatim match
        idx = text.upper().find(needle.upper())
        if idx >= 0:
            matched_len = len(needle)
            match_type = "case_insensitive"

    # Strategy 3: Whitespace-collapsed verbatim match
    if idx < 0 and collapsed != needle:
        idx = text.find(collapsed)
        if idx >= 0:
            matched_len = len(collapsed)
            match_type = "whitespace_collapsed"
        else:
            idx = text.upper().find(collapsed.upper())
            if idx >= 0:
                matched_len = len(collapsed)
                match_type = "whitespace_collapsed"

    # Strategy 4: Whitespace-tolerant match (ALL tokens in the value must appear in order)
    if idx < 0 and " " in collapsed:
        tokens = [re.escape(tok) for tok in collapsed.split(" ") if tok]
        if tokens:
            pattern = re.compile(r'\s+'.join(tokens), re.IGNORECASE)
            found = pattern.search(text)
            if found:
                idx = found.start()
                matched_len = found.end() - found.start()
                match_type = "whitespace_tolerant"

    # Strategy 5: Numeric / Digit-tolerant match (all digits must appear in order)
    if idx < 0:
        digits = re.sub(r'[^0-9]', '', needle)
        if len(digits) >= 4:
            pattern = re.compile(r'[^0-9\n]*'.join(re.escape(ch) for ch in digits))
            found = pattern.search(text)
            if found:
                idx = found.start()
                matched_len = found.end() - found.start()
                match_type = "digit_tolerant"

    # Strategy 6: Partial matching ONLY if explicitly permitted
    if idx < 0 and allow_partial:
        tokens = [tok for tok in collapsed.split(' ') if tok]
        # Check prefix matches
        for k in range(len(tokens) - 1, 0, -1):
            cand = " ".join(tokens[:k])
            if len(cand) >= 3:
                pos = text.upper().find(cand.upper())
                if pos >= 0:
                    idx = pos
                    matched_len = len(cand)
                    match_type = "token_prefix" if k > 1 else "line_partial"
                    break
        if idx < 0 and tokens:
            for tok in tokens:
                if len(tok) >= 3:
                    pos = text.upper().find(tok.upper())
                    if pos >= 0:
                        idx = pos
                        matched_len = len(tok)
                        match_type = "line_partial"
                        break

    if idx >= 0:
        line_start = text.rfind('\n', 0, idx) + 1
        line_end = text.find('\n', idx)
        if line_end < 0:
            line_end = len(text)
        return {
            "char_offset": idx,
            "start_char": idx,
            "end_char": idx + matched_len,
            "line_number": text[:idx].count('\n') + 1,
            "exact_text": text[line_start:line_end].strip(),
            "match_type": match_type,
        }
    return None


def _document_name(attachment: Any, fallback: str) -> str:
    if isinstance(attachment, dict):
        return attachment.get("filename") or attachment.get("path") or fallback
    if isinstance(attachment, str) and attachment:
        return attachment.split("/")[-1]
    return fallback


def _build_source(document: str, doc_type: str, raw_text: str, value: Any, allow_partial: bool = False) -> Dict[str, Any]:
    span = locate_span(raw_text, value, allow_partial=allow_partial)
    return {
        "document": document,
        "document_type": doc_type,
        "value": None if value is None else str(value),
        "char_offset": span["char_offset"] if span else None,
        "start_char": span["start_char"] if span else None,
        "end_char": span["end_char"] if span else None,
        "line_number": span["line_number"] if span else None,
        "exact_text": span["exact_text"] if span else None,
        "span_match": span["match_type"] if span else None,
        "found_in_document": bool(span),
    }


def check_whitelist(field_key: str, value: Any, raw_text: str = "") -> Dict[str, Any]:
    """Apply the code-list lookup belonging to this field, if any."""
    table = WHITELIST_TABLES.get(field_key)
    if table is None:
        return {"status": "n/a", "table": None,
                "details": "No code list applies to this field."}

    if table == "UN/LOCODE":
        if value in (None, ""):
            return {"status": "n/a", "table": "UN/LOCODE", "details": "No value to resolve."}
        code = port_lookup.resolve_port_code(str(value))
        return {
            "status": "pass" if code else "fail",
            "table": "UN/LOCODE",
            "resolved_code": code,
            "details": f"Resolved UN/LOCODE {code}." if code
                       else "Value could not be resolved to a UN/LOCODE.",
        }

    # ISO 6346 check digits apply to container *numbers* found in the document;
    # a bare container count has no check digit of its own.
    numbers = sorted(_CONTAINER_RE.findall(str(raw_text).upper()))
    if not numbers:
        return {"status": "n/a", "table": "ISO 6346",
                "details": "No ISO 6346 container numbers present in the document text."}
    invalid = [n for n in numbers if not _validate_container_number(n)]
    return {
        "status": "pass" if not invalid else "fail",
        "table": "ISO 6346",
        "checked": numbers,
        "invalid": invalid,
        "details": f"{len(numbers) - len(invalid)}/{len(numbers)} container numbers pass the ISO 6346 check digit.",
    }


def build_field_evidence(
    field_key: str,
    si_value: Any,
    bl_value: Any,
    si_text: str = "",
    bl_text: str = "",
    si_document: str = "SI",
    bl_document: str = "BL",
    agreement: Optional[str] = None,
    resolved_value: Any = None,
) -> Dict[str, Any]:
    """Build the evidence record for one field across both source documents."""
    from backend.services import dcsa_mapping

    mapping = dcsa_mapping.mapping_for(field_key)

    sources: List[Dict[str, Any]] = [
        _build_source(si_document, "SI", si_text, si_value),
        _build_source(bl_document, "BL", bl_text, bl_value),
    ]

    if agreement is None:
        from backend.services.comparator import comparator
        is_match, _, _, _meta = comparator._compare_single_field(field_key, si_value, bl_value)
        agreement = "match" if is_match else "conflict"

    chosen = bl_value if resolved_value is None else resolved_value
    source_match = "pass" if any(
        s["document_type"] == "BL" and s["found_in_document"] for s in sources
    ) else "fail"

    return {
        "internal_field": field_key,
        "dcsa_field": mapping.get("dcsa_field"),
        "dcsa_object": mapping.get("dcsa_object"),
        "internal_only": bool(mapping.get("internal_only")),
        "value": None if chosen is None else str(chosen),
        "sources": sources,
        "validation": {
            "source_match": source_match,
            "whitelist": check_whitelist(field_key, chosen, bl_text or si_text),
        },
        "agreement": agreement,
    }


def attachment_names(email: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Best-effort SI/BL document names for an email record."""
    names = {"si": "SI", "bl": "BL"}
    if not email:
        return names
    for att in email.get("attachments", []) or []:
        path = att.get("path") if isinstance(att, dict) else str(att)
        doc_type = (att.get("doc_type") if isinstance(att, dict) else "") or ""
        lower = str(path).lower()
        if doc_type == "SI" or "_si." in lower:
            names["si"] = _document_name(att, "SI")
        elif doc_type == "BL" or "_bl." in lower:
            names["bl"] = _document_name(att, "BL")
    return names
