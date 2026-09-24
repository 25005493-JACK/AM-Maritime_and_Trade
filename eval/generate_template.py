#!/usr/bin/env python3
"""
generate_template.py — Generates a blank ground-truth labelling template CSV
for the 520 inbox emails in DocuMatch.

Per hackathon instructions:
Do not label with an LLM. This template is filled by a human annotator or populated
with official organizer ground truth labels.
"""
import os
import csv
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.services.dataset_loader import loader

COLUMNS = [
    "email_id",
    "category",                  # BL_COMPARISON | SI_REQUEST | INVOICE_QUERY | GENERAL | SPAM
    "si_shipper",
    "bl_shipper",
    "si_consignee",
    "bl_consignee",
    "si_notify_party",
    "bl_notify_party",
    "si_port_of_loading",
    "bl_port_of_loading",
    "si_port_of_discharge",
    "bl_port_of_discharge",
    "si_container_count",
    "bl_container_count",
    "si_gross_weight_kg",
    "bl_gross_weight_kg",
    "defect_fields",             # comma-separated list of mismatched fields, e.g. "consignee,notify_party" or empty
    "expected_outcome",          # OK | MISMATCH | NEEDS_REVIEW
    "review_reason"              # wrong_doc_type | missing_attachment | unreadable | missing_value | empty
]

def generate_template(output_path: str = None) -> str:
    if output_path is None:
        eval_labels_dir = ROOT_DIR / "eval" / "labels"
        eval_labels_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(eval_labels_dir / "template_labels.csv")

    emails = loader.load_inbox()
    print(f"Loaded {len(emails)} emails from dataset.")

    rows = []
    for email in emails:
        eid = email.get("id") or email.get("email_id")
        row = {col: "" for col in COLUMNS}
        row["email_id"] = eid
        rows.append(row)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated labelling template with {len(rows)} rows at: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_template()
