"""
Generates eval/labels/ground_truth.csv by inspecting inbox documents
with precise ground-truth rules according to eval/README.md.
"""
import os
import re
import csv
import json
import sys
from pathlib import Path

ROOT = Path("c:/UM/monash hackathon/AM-Maritime_and_Trade-1")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "test data"))

from backend.services.extractor import extractor
from backend.services.field_bank import compare_company_name, company_name_normalizer
from backend.services.port_lookup import port_lookup
from backend.services.classifier import classifier
from backend.services.comparator import comparator
INBOX_DIR = ROOT / "test data" / "inbox"
ATTACH_DIR = ROOT / "test data" / "attachments"
LABELS_DIR = ROOT / "eval" / "labels"
OUT_PATH = LABELS_DIR / "ground_truth.csv"

def main():
    email_files = sorted(
        [f for f in os.listdir(INBOX_DIR) if f.endswith(".json")],
        key=lambda x: int(re.search(r"\d+", x).group()),
    )

    fieldnames = [
        "email_id", "category", "has_si_attachment", "has_bl_attachment",
        "shipper_si", "shipper_bl", "consignee_si", "consignee_bl",
        "notify_party_si", "notify_party_bl", "port_of_loading_si", "port_of_loading_bl",
        "port_of_discharge_si", "port_of_discharge_bl", "container_count_si", "container_count_bl",
        "gross_weight_kg_si", "gross_weight_kg_bl",
        "shipper_match", "consignee_match", "notify_party_match",
        "pol_match", "pod_match", "container_count_match", "gross_weight_match",
        "defect_fields", "expected_status", "review_reason", "notes"
    ]

    rows = []
    category_counts = {}
    status_counts = {}

    for ef in email_files:
        with open(INBOX_DIR / ef, "r", encoding="utf-8") as fh:
            email = json.load(fh)

        eid = email.get("email_id", ef.replace(".json", ""))
        attachments = email.get("attachments", [])

        # Find SI and BL
        si_path, bl_path = None, None
        for att in attachments:
            att_str = att if isinstance(att, str) else att.get("path", "")
            base = os.path.basename(att_str).lower()
            if "_si." in base or base.startswith("si"):
                p = ATTACH_DIR / os.path.basename(att_str)
                if p.exists(): si_path = p
            if "_bl." in base or base.startswith("bl"):
                p = ATTACH_DIR / os.path.basename(att_str)
                if p.exists(): bl_path = p

        has_si = si_path is not None
        has_bl = bl_path is not None

        # Determine Category
        class_res = classifier.classify(email)
        category = class_res["category"]

        # Ground truth status
        expected_status = "OK"
        review_reason = ""
        defect_fields = []
        field_matches = {
            "shipper_match": "NA", "consignee_match": "NA", "notify_party_match": "NA",
            "pol_match": "NA", "pod_match": "NA", "container_count_match": "NA", "gross_weight_match": "NA"
        }
        si_vals = {}
        bl_vals = {}

        if category == "BL_COMPARISON":
            comp_res = comparator.compare_documents("", "", email_metadata=email)
            expected_status = comp_res["status"]
            review_reason = comp_res.get("review_reason") or ""
            defect_fields = comp_res.get("defect_fields") or []

            si_ext = comp_res.get("si_extracted") or {}
            bl_ext = comp_res.get("bl_extracted") or {}
            si_vals = {f: si_ext.get(f, "") for f in comparator.FIELDS}
            bl_vals = {f: bl_ext.get(f, "") for f in comparator.FIELDS}

            # Map matches
            field_col_map = {
                "shipper": "shipper_match", "consignee": "consignee_match", "notify_party": "notify_party_match",
                "port_of_loading": "pol_match", "port_of_discharge": "pod_match",
                "container_count": "container_count_match", "gross_weight_kg": "gross_weight_match"
            }
            matrix_by_field = {r["field_key"]: r for r in comp_res.get("field_matrix", [])}

            for f, col in field_col_map.items():
                if f in matrix_by_field:
                    m = matrix_by_field[f]
                    if m.get("match_type") == "NEEDS_REVIEW" or m.get("si_value") is None or m.get("bl_value") is None:
                        field_matches[col] = "NA"
                    else:
                        field_matches[col] = "TRUE" if m.get("is_match") else "FALSE"
                else:
                    field_matches[col] = "NA"
        else:
            expected_status = "OK"
            review_reason = ""
            defect_fields = []

        category_counts[category] = category_counts.get(category, 0) + 1
        status_counts[expected_status] = status_counts.get(expected_status, 0) + 1

        row = {
            "email_id": eid,
            "category": category,
            "has_si_attachment": "TRUE" if has_si else "FALSE",
            "has_bl_attachment": "TRUE" if has_bl else "FALSE",
            "shipper_si": si_vals.get("shipper", ""),
            "shipper_bl": bl_vals.get("shipper", ""),
            "consignee_si": si_vals.get("consignee", ""),
            "consignee_bl": bl_vals.get("consignee", ""),
            "notify_party_si": si_vals.get("notify_party", ""),
            "notify_party_bl": bl_vals.get("notify_party", ""),
            "port_of_loading_si": si_vals.get("port_of_loading", ""),
            "port_of_loading_bl": bl_vals.get("port_of_loading", ""),
            "port_of_discharge_si": si_vals.get("port_of_discharge", ""),
            "port_of_discharge_bl": bl_vals.get("port_of_discharge", ""),
            "container_count_si": si_vals.get("container_count", ""),
            "container_count_bl": bl_vals.get("container_count", ""),
            "gross_weight_kg_si": si_vals.get("gross_weight_kg", ""),
            "gross_weight_kg_bl": bl_vals.get("gross_weight_kg", ""),
            "defect_fields": ",".join(defect_fields),
            "expected_status": expected_status,
            "review_reason": review_reason,
            "notes": "",
            **field_matches
        }
        rows.append(row)

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Wrote {len(rows)} rows to {OUT_PATH}")
    print(f"Categories: {category_counts}")
    print(f"Statuses: {status_counts}")

if __name__ == "__main__":
    main()
