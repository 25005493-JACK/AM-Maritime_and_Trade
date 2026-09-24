#!/usr/bin/env python3
"""
generate_labelling_template.py
------------------------------
Creates eval/labels/labelling_template.csv with one row per email.

Columns:
  email_id            — e.g. "email_001"
  category            — human must fill: BL_COMPARISON | SI_REQUEST | INVOICE_QUERY | GENERAL | SPAM
  has_si_attachment    — auto-populated: TRUE/FALSE (whether SI file exists)
  has_bl_attachment    — auto-populated: TRUE/FALSE (whether BL file exists)
  shipper_si          — auto-populated: extracted SI shipper (for reference)
  shipper_bl          — auto-populated: extracted BL shipper (for reference)
  consignee_si        — auto-populated
  consignee_bl        — auto-populated
  notify_party_si     — auto-populated
  notify_party_bl     — auto-populated
  port_of_loading_si  — auto-populated
  port_of_loading_bl  — auto-populated
  port_of_discharge_si — auto-populated
  port_of_discharge_bl — auto-populated
  container_count_si  — auto-populated
  container_count_bl  — auto-populated
  gross_weight_kg_si  — auto-populated
  gross_weight_kg_bl  — auto-populated
  shipper_match       — human must fill: TRUE/FALSE/NA (NA if not BL_COMPARISON)
  consignee_match     — human must fill
  notify_party_match  — human must fill
  pol_match           — human must fill
  pod_match           — human must fill
  container_count_match — human must fill
  gross_weight_match  — human must fill
  defect_fields       — human must fill: comma-separated list of mismatched fields, or empty
  expected_status     — human must fill: OK | MISMATCH | NEEDS_REVIEW
  review_reason       — human must fill if NEEDS_REVIEW: missing_attachment | corrupted_file |
                         wrong_doc_type | scanned_not_processed | missing_value | term_unresolved | other
  notes               — optional freeform notes

IMPORTANT: Auto-populated reference fields are filled from the raw attachment
text where available (NOT from system predictions). They are only visual aids;
the human annotator should verify them against the original documents.

Usage:
    python eval/generate_labelling_template.py
"""

import csv
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX_DIR = ROOT / "test data" / "inbox"
ATTACH_DIR = ROOT / "test data" / "attachments"
LABELS_DIR = ROOT / "eval" / "labels"


# ──────────────────────────────────────────────────────────────────────
# Lightweight field extraction from raw text (no system imports)
# ──────────────────────────────────────────────────────────────────────

FIELD_PATTERNS = {
    "shipper": re.compile(
        r"(?:shipper|shipper/exporter|exporter)\s*(?:\(.*?\))?\s*:\s*(.+)",
        re.I,
    ),
    "consignee": re.compile(
        r"(?:consignee|to the order of)\s*(?:\(.*?\))?\s*:\s*(.+)",
        re.I,
    ),
    "notify_party": re.compile(
        r"(?:notify\s*(?:party)?)\s*:\s*(.+)",
        re.I,
    ),
    "port_of_loading": re.compile(
        r"(?:port of loading|pol|loading port)\s*(?:\(.*?\))?\s*:\s*(.+)",
        re.I,
    ),
    "port_of_discharge": re.compile(
        r"(?:port of discharge|pod|discharge port|destination port)\s*:\s*(.+)",
        re.I,
    ),
    "container_count": re.compile(
        r"(?:container\s*(?:count|qty)?|total containers|no\.?\s*of containers\s*(?:or packages)?)\s*:\s*(.+)",
        re.I,
    ),
    "gross_weight_kg": re.compile(
        r"(?:gross\s*w(?:eigh)?t|gross\s*wt)\s*(?:\(.*?\))?\s*:\s*(.+)",
        re.I,
    ),
}


def extract_fields_from_text(text: str) -> dict:
    """Very simple regex extraction — used only for the labelling template reference columns."""
    fields = {}
    for field_name, pattern in FIELD_PATTERNS.items():
        m = pattern.search(text)
        fields[field_name] = m.group(1).strip() if m else ""
    return fields


def read_text_file(path: Path) -> str:
    """Read a text-based attachment; skip binary/non-text formats."""
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    if suffix in (".txt", ".csv"):
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""
    # For xlsx, docx, pdf — we can't easily extract here without heavy deps.
    # Leave blank; the human annotator should open the original file.
    return ""


def main():
    LABELS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = LABELS_DIR / "labelling_template.csv"

    # Collect all email IDs
    email_files = sorted(
        [f for f in os.listdir(INBOX_DIR) if f.endswith(".json")],
        key=lambda x: int(re.search(r"\d+", x).group()),
    )

    fieldnames = [
        "email_id",
        "category",
        "has_si_attachment",
        "has_bl_attachment",
        "shipper_si",
        "shipper_bl",
        "consignee_si",
        "consignee_bl",
        "notify_party_si",
        "notify_party_bl",
        "port_of_loading_si",
        "port_of_loading_bl",
        "port_of_discharge_si",
        "port_of_discharge_bl",
        "container_count_si",
        "container_count_bl",
        "gross_weight_kg_si",
        "gross_weight_kg_bl",
        "shipper_match",
        "consignee_match",
        "notify_party_match",
        "pol_match",
        "pod_match",
        "container_count_match",
        "gross_weight_match",
        "defect_fields",
        "expected_status",
        "review_reason",
        "notes",
    ]

    rows = []
    for ef in email_files:
        with open(INBOX_DIR / ef, "r", encoding="utf-8") as fh:
            email = json.load(fh)

        eid = email.get("email_id", ef.replace(".json", ""))
        attachments = email.get("attachments", [])

        # Check for SI/BL attachments
        si_path = None
        bl_path = None
        for att in attachments:
            att_str = att if isinstance(att, str) else att.get("path", "")
            att_basename = os.path.basename(att_str).lower()
            if "_si." in att_basename or att_basename.startswith("si"):
                si_path = ATTACH_DIR / os.path.basename(att_str)
            if "_bl." in att_basename or att_basename.startswith("bl"):
                bl_path = ATTACH_DIR / os.path.basename(att_str)

        has_si = si_path is not None and si_path.exists()
        has_bl = bl_path is not None and bl_path.exists()

        # Extract reference fields from text attachments
        si_fields = extract_fields_from_text(read_text_file(si_path)) if has_si and si_path else {}
        bl_fields = extract_fields_from_text(read_text_file(bl_path)) if has_bl and bl_path else {}

        row = {
            "email_id": eid,
            "category": "",  # human fills
            "has_si_attachment": "TRUE" if has_si else "FALSE",
            "has_bl_attachment": "TRUE" if has_bl else "FALSE",
            "shipper_si": si_fields.get("shipper", ""),
            "shipper_bl": bl_fields.get("shipper", ""),
            "consignee_si": si_fields.get("consignee", ""),
            "consignee_bl": bl_fields.get("consignee", ""),
            "notify_party_si": si_fields.get("notify_party", ""),
            "notify_party_bl": bl_fields.get("notify_party", ""),
            "port_of_loading_si": si_fields.get("port_of_loading", ""),
            "port_of_loading_bl": bl_fields.get("port_of_loading", ""),
            "port_of_discharge_si": si_fields.get("port_of_discharge", ""),
            "port_of_discharge_bl": bl_fields.get("port_of_discharge", ""),
            "container_count_si": si_fields.get("container_count", ""),
            "container_count_bl": bl_fields.get("container_count", ""),
            "gross_weight_kg_si": si_fields.get("gross_weight_kg", ""),
            "gross_weight_kg_bl": bl_fields.get("gross_weight_kg", ""),
            "shipper_match": "",  # human fills
            "consignee_match": "",
            "notify_party_match": "",
            "pol_match": "",
            "pod_match": "",
            "container_count_match": "",
            "gross_weight_match": "",
            "defect_fields": "",
            "expected_status": "",
            "review_reason": "",
            "notes": "",
        }
        rows.append(row)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Wrote labelling template with {len(rows)} rows to:")
    print(f"    {out_path}")
    print()
    print("NEXT STEPS:")
    print("  1. Open the CSV in Excel/Google Sheets")
    print("  2. Fill in ALL blank columns (category, field matches, expected_status, etc.)")
    print("  3. Save as eval/labels/ground_truth.csv")
    print("  4. Run:  python eval/split.py")
    print("  5. Run:  python eval/evaluate.py --mode rules_only")
    print()
    print("RULES:")
    print("  - For non-BL_COMPARISON emails, set expected_status=OK and all match fields to NA")
    print("  - For BL_COMPARISON emails, compare SI vs BL fields manually")
    print("  - defect_fields is a comma-separated list: e.g. 'consignee,notify_party'")
    print("  - Do NOT use an LLM to fill labels. Do NOT guess. If unsure, set expected_status=NEEDS_REVIEW")


if __name__ == "__main__":
    main()
