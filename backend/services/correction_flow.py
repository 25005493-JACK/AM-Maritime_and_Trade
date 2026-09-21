"""
Propose-and-confirm correction flow.

Replaces any "auto-correct to the SI value" behaviour:

  * When SI and BL disagree the system NEVER picks a winner. It builds a
    *proposal* per conflicting field containing both candidate values with their
    source evidence (document, offset, exact quoted text).
  * Only an explicit human decision ("si", "bl" or "custom" + value, with a
    reviewer name) produces a resolved value.
  * Resolved values are written into a ``resolved_bl`` record whose structure
    follows the DCSA Bill of Lading field mapping, so the result is consumable by
    any DCSA-aware system and not only by our own UI.

The record carries a plain ``notice`` stating what it is (reviewer-confirmed field
values in DCSA naming) and what it is not (no legal validity, no signature, no
certificate) - we do not overstate what the pipeline proves.
"""
import json
import os
import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.services import dcsa_mapping, field_evidence
from backend.services.comparator import comparator
from backend.services.corrections_log import append_corrections

RESOLUTION_CHOICES = ("si", "bl", "custom")

NOTICE = (
    "Reviewer-confirmed field values expressed with DCSA Bill of Lading field names. "
    "This is a document-mapping record, not a certificate: it carries no cryptographic "
    "hash or signature, asserts no legal validity, and only records which source documents "
    "the reviewer accepted for each field."
)


class HumanDecisionRequired(ValueError):
    """Raised when a caller tries to resolve a conflict without a human decision."""


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _extracted(verification: Optional[Dict[str, Any]], side: str) -> Dict[str, Any]:
    if not verification:
        return {}
    data = verification.get(f"{side}_extracted") or {}
    return data if isinstance(data, dict) else {}


def _document_names(email: Optional[Dict[str, Any]]) -> Dict[str, str]:
    return field_evidence.attachment_names(email)


def build_conflict_proposals(
    email_id: str,
    verification: Optional[Dict[str, Any]] = None,
    si_text: str = "",
    bl_text: str = "",
    email: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Side-by-side proposals for conflicting fields. Nothing is auto-resolved."""
    names = _document_names(email)
    si_extracted = _extracted(verification, "si")
    bl_extracted = _extracted(verification, "bl")
    matrix = (verification or {}).get("field_matrix") or []

    proposals: List[Dict[str, Any]] = []
    matched: List[str] = []

    for row in matrix:
        field_key = row.get("field_key")
        if not field_key:
            continue
        si_value = row.get("si_value")
        bl_value = row.get("bl_value")
        is_conflict = not row.get("is_match")
        evidence = field_evidence.build_field_evidence(
            field_key, si_value, bl_value, si_text, bl_text,
            names["si"], names["bl"],
            agreement="conflict" if is_conflict else "match",
        )
        if not is_conflict:
            matched.append(field_key)
            continue

        mapping = dcsa_mapping.mapping_for(field_key)
        proposals.append({
            "field_key": field_key,
            "field_name": row.get("field_name"),
            "dcsa_field": mapping.get("dcsa_field"),
            "dcsa_object": mapping.get("dcsa_object"),
            "internal_only": bool(mapping.get("internal_only")),
            "dcsa_definition": mapping.get("definition"),
            "agreement": "conflict",
            "reason": row.get("diff_summary") or row.get("reason") or "Values differ",
            "si_candidate": evidence["sources"][0],
            "bl_candidate": evidence["sources"][1],
            "options": list(RESOLUTION_CHOICES),
            "requires_human_decision": True,
            "auto_resolved": False,
            "decision": None,
        })

    return {
        "email_id": email_id,
        "requires_human_decision": bool(proposals),
        "auto_resolution": "disabled",
        "policy": (
            "SI and draft BL are treated as equal-weight sources. A value is only "
            "accepted into the resolved record when a reviewer explicitly chooses it."
        ),
        "standard": {
            "name": dcsa_mapping.DCSA_STANDARD,
            "information_model": dcsa_mapping.DCSA_INFORMATION_MODEL,
            "sources": dcsa_mapping.DCSA_SOURCES,
        },
        "matched_fields": matched,
        "proposals": proposals,
    }


def _validate_decisions(decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every decision must be an explicit, human-made choice."""
    if not decisions:
        raise HumanDecisionRequired(
            "A human decision is required: this pipeline never resolves SI/BL conflicts on its own."
        )
    validated: List[Dict[str, Any]] = []
    for decision in decisions:
        if not isinstance(decision, dict) or not decision.get("field_key"):
            raise HumanDecisionRequired("Each decision must name the field_key it resolves.")
        field_key = decision["field_key"]
        choice = str(decision.get("choice") or "").lower()
        if choice not in RESOLUTION_CHOICES:
            raise HumanDecisionRequired(
                f"Decision for '{field_key}' must be one of {list(RESOLUTION_CHOICES)} "
                f"(received {decision.get('choice')!r}); auto-resolution is not supported."
            )
        if choice == "custom" and decision.get("value") in (None, ""):
            raise HumanDecisionRequired(
                f"A custom decision for '{field_key}' must supply the explicit corrected value."
            )
        validated.append({
            "field_key": field_key,
            "choice": choice,
            "value": decision.get("value"),
            "note": decision.get("note", ""),
        })
    return validated


def flatten_dcsa_paths(node: Any, prefix: str = "") -> Dict[str, Any]:
    """Flatten a DCSA document into {json.path: value} pairs (for audit/export)."""
    flat: Dict[str, Any] = {}
    if isinstance(node, dict):
        for key, value in node.items():
            flat.update(flatten_dcsa_paths(value, f"{prefix}.{key}" if prefix else key))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            flat.update(flatten_dcsa_paths(value, f"{prefix}[{idx}]"))
    else:
        flat[prefix] = node
    return flat


def build_resolved_record(
    email_id: str,
    resolved_values: Dict[str, Any],
    decisions: List[Dict[str, Any]],
    reviewer: str,
    timestamp: str,
    pending_fields: List[str],
    evidence_map: Optional[Dict[str, Dict[str, Any]]] = None,
    email: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble the resolved record structured by DCSA field names."""
    port_codes: Dict[str, str] = {}
    for field_key in ("port_of_loading", "port_of_discharge"):
        value = resolved_values.get(field_key)
        if value:
            check = field_evidence.check_whitelist(field_key, value)
            if check.get("resolved_code"):
                port_codes[field_key] = check["resolved_code"]

    dcsa_doc = dcsa_mapping.to_dcsa_document(resolved_values, port_codes)

    return {
        "record_type": "resolved_transport_document",
        "email_id": email_id,
        "shipment_id": (email or {}).get("shipment_id") or (email or {}).get("id") or email_id,
        "generated_at": timestamp,
        "reviewer": reviewer,
        "standard": {
            "name": dcsa_mapping.DCSA_STANDARD,
            "information_model": dcsa_mapping.DCSA_INFORMATION_MODEL,
            "sources": dcsa_mapping.DCSA_SOURCES,
        },
        "field_mapping": {
            field: dcsa_mapping.dcsa_field_name(field) for field in sorted(resolved_values)
        },
        "transportDocument": dcsa_doc["transportDocument"],
        "internal_only_fields": {
            field: str(value) for field, value in resolved_values.items()
            if dcsa_mapping.is_internal_only(field)
        },
        "field_evidence": evidence_map or {},
        "review_decisions": decisions,
        "pending_decisions": pending_fields,
        "notice": NOTICE,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Human resolution
# ─────────────────────────────────────────────────────────────────────────────

def apply_human_resolution(
    email_id: str,
    decisions: List[Dict[str, Any]],
    reviewer_name: str,
    verification: Optional[Dict[str, Any]] = None,
    si_text: str = "",
    bl_text: str = "",
    email: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
    persist: bool = True,
    log: bool = True,
) -> Dict[str, Any]:
    """Apply reviewer decisions to produce a DCSA-mapped resolved record.

    Raises :class:`HumanDecisionRequired` if no reviewer is supplied or if any
    field is left to be resolved automatically.
    """
    reviewer = (reviewer_name or "").strip()
    if not reviewer:
        raise HumanDecisionRequired("A reviewer name is required to record a decision.")

    validated = _validate_decisions(decisions)
    ts = timestamp or _now()
    names = _document_names(email)
    si_extracted = _extracted(verification, "si")
    bl_extracted = _extracted(verification, "bl")
    matrix = {row.get("field_key"): row for row in (verification or {}).get("field_matrix") or []}
    conflicts = {key for key, row in matrix.items() if not row.get("is_match")}

    # Fields where the two documents already agree: carried over as-is.
    resolved_values: Dict[str, Any] = {}
    for field_key in matrix:
        if field_key in conflicts:
            continue
        value = bl_extracted.get(field_key, si_extracted.get(field_key))
        if value not in (None, ""):
            resolved_values[field_key] = value

    decisions_out: List[Dict[str, Any]] = []
    evidence_map: Dict[str, Dict[str, Any]] = {}
    correction_rows: List[Dict[str, Any]] = []
    decided: set = set()

    for decision in validated:
        field_key = decision["field_key"]
        si_value = si_extracted.get(field_key)
        bl_value = bl_extracted.get(field_key)

        if decision["choice"] == "si":
            value, origin = si_value, names["si"]
        elif decision["choice"] == "bl":
            value, origin = bl_value, names["bl"]
        else:
            value, origin = decision["value"], "reviewer override"

        if value is None or str(value).strip() == "":
            raise HumanDecisionRequired(
                f"Field '{field_key}' cannot be resolved to an empty value."
            )

        resolved_values[field_key] = value
        decided.add(field_key)

        evidence = field_evidence.build_field_evidence(
            field_key, si_value, bl_value, si_text, bl_text,
            names["si"], names["bl"], agreement="conflict", resolved_value=value,
        )
        evidence_map[field_key] = evidence
        mapping = dcsa_mapping.mapping_for(field_key)

        decisions_out.append({
            "field_key": field_key,
            "dcsa_field": mapping.get("dcsa_field"),
            "internal_only": bool(mapping.get("internal_only")),
            "chosen": decision["choice"],
            "origin": origin,
            "value": str(value),
            "rejected_values": {"si": si_value, "bl": bl_value},
            "reviewer": reviewer,
            "timestamp": ts,
            "note": decision.get("note", ""),
            "evidence": evidence["sources"],
        })
        correction_rows.append({
            "timestamp": ts,
            "email_id": email_id,
            "field": field_key,
            "dcsa_field": mapping.get("dcsa_field") or "",
            "original_value": bl_value if bl_value not in (None, "") else si_value,
            "corrected_value": value,
            "resolution": f"human_selected:{decision['choice']}",
            "reviewer": reviewer,
            "evidence_summary": " | ".join(
                f"{s['document']}@{s['char_offset']}: {s['exact_text']}"
                for s in evidence["sources"] if s.get("exact_text")
            ),
        })

    pending = sorted(conflicts - decided)
    record = build_resolved_record(
        email_id, resolved_values, decisions_out, reviewer, ts, pending, evidence_map, email
    )

    if persist:
        write_resolved_record(email_id, record)
    logged = append_corrections(correction_rows) if (log and correction_rows) else 0

    return {
        "email_id": email_id,
        "reviewer": reviewer,
        "timestamp": ts,
        "auto_resolution": "disabled",
        "resolved_bl": record,
        "dcsa_export": flatten_dcsa_paths(record.get("transportDocument", {})),
        "corrections_logged": logged,
        "pending_decisions": pending,
        "resolved_field_count": len(resolved_values),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Persistence / export
# ─────────────────────────────────────────────────────────────────────────────

def resolved_dir() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "resolved",
    )


def resolved_record_path(email_id: str) -> str:
    return os.path.join(resolved_dir(), f"{email_id}.dcsa.json")


def write_resolved_record(email_id: str, record: Dict[str, Any]) -> str:
    os.makedirs(resolved_dir(), exist_ok=True)
    path = resolved_record_path(email_id)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
    return path


def load_resolved_record(email_id: str) -> Optional[Dict[str, Any]]:
    path = resolved_record_path(email_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def export_dcsa_json(record: Dict[str, Any]) -> str:
    return json.dumps(record, indent=2, ensure_ascii=False)
