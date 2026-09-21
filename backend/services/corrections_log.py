"""
Correction log (append-only CSV) with DCSA field attribution.

Every human correction records *which DCSA-standard field* was involved, so
analytics can answer questions like "which DCSA fields cause the most carrier
disputes?" - a number that is meaningful to carriers, not just to our own UI.

Legacy files written by the older 6-column format are migrated in place on first
use (the DCSA column is back-filled from the mapping catalog).
"""
import csv
import os
from typing import Any, Dict, List, Optional

from backend.services import dcsa_mapping

COLUMNS = [
    "timestamp",
    "email_id",
    "field",
    "dcsa_field",
    "original_value",
    "corrected_value",
    "resolution",
    "reviewer",
    "evidence_summary",
]

LEGACY_COLUMNS = ["timestamp", "email_id", "field", "original_value", "corrected_value", "reviewer"]


def _workspace_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def corrections_path() -> str:
    return os.path.join(_workspace_root(), "data", "corrections.csv")


def _read_rows(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def migrate_if_needed(path: Optional[str] = None) -> bool:
    """Upgrade a legacy corrections.csv to the DCSA-aware schema. Returns True if rewritten."""
    path = path or corrections_path()
    rows = _read_rows(path)
    if not rows and not os.path.exists(path):
        return False

    with open(path, "r", encoding="utf-8", newline="") as fh:
        header = next(csv.reader(fh), [])
    if header == COLUMNS:
        return False

    migrated: List[Dict[str, Any]] = []
    for row in rows:
        field = row.get("field", "")
        migrated.append({
            "timestamp": row.get("timestamp", ""),
            "email_id": row.get("email_id", ""),
            "field": field,
            "dcsa_field": row.get("dcsa_field") or (dcsa_mapping.dcsa_field_name(field) or ""),
            "original_value": row.get("original_value", ""),
            "corrected_value": row.get("corrected_value", ""),
            "resolution": row.get("resolution") or "human_selected",
            "reviewer": row.get("reviewer", ""),
            "evidence_summary": row.get("evidence_summary", ""),
        })

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for row in migrated:
            writer.writerow(row)
    return True


def append_corrections(rows: List[Dict[str, Any]], path: Optional[str] = None) -> int:
    """Append correction rows, filling the DCSA column from the mapping catalog."""
    path = path or corrections_path()
    migrate_if_needed(path)
    is_new = not os.path.exists(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    written = 0
    with open(path, "a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        if is_new:
            writer.writeheader()
        for row in rows:
            field = row.get("field", "")
            writer.writerow({
                "timestamp": row.get("timestamp", ""),
                "email_id": row.get("email_id", ""),
                "field": field,
                "dcsa_field": row.get("dcsa_field") or (dcsa_mapping.dcsa_field_name(field) or ""),
                "original_value": row.get("original_value", ""),
                "corrected_value": row.get("corrected_value", ""),
                "resolution": row.get("resolution", "human_selected"),
                "reviewer": row.get("reviewer", ""),
                "evidence_summary": row.get("evidence_summary", ""),
            })
            written += 1
    return written


def read_corrections(path: Optional[str] = None) -> List[Dict[str, str]]:
    migrate_if_needed(path)
    return _read_rows(path or corrections_path())


def dcsa_field_dispute_counts(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Corrections grouped by DCSA field - the 'which standard fields cause disputes' view."""
    counts: Dict[str, Dict[str, Any]] = {}
    for row in read_corrections(path):
        label = row.get("dcsa_field") or f"(internal only) {row.get('field', '')}".strip()
        entry = counts.setdefault(label, {
            "dcsa_field": row.get("dcsa_field") or None,
            "internal_field": row.get("field", ""),
            "internal_only": not bool(row.get("dcsa_field")),
            "count": 0,
            "last_reviewer": row.get("reviewer", ""),
            "last_timestamp": row.get("timestamp", ""),
        })
        entry["count"] += 1
        if row.get("timestamp", "") >= entry["last_timestamp"]:
            entry["last_timestamp"] = row.get("timestamp", "")
            entry["last_reviewer"] = row.get("reviewer", "")

    ordered = sorted(counts.values(), key=lambda e: (-e["count"], str(e["dcsa_field"])))
    return ordered
