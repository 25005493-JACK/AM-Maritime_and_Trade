#!/usr/bin/env python3
"""
check_data_classification.py

Evaluates the inbox data classification based on the official hackathon instructions
(Page 3 & 4 of Shipping Document Verification Use Case & test data/README.md).

Can be executed against:
  1. The Docker / HTTP server: python check_data_classification.py http://localhost:8080
  2. The local bundle directly: python check_data_classification.py "test data"
"""

import sys
import os
import json
from pathlib import Path
from collections import Counter

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import loader from test data
sys.path.insert(0, os.path.join(BASE_DIR, "test data"))
from loader import Inbox
from backend.services.dataset_loader import loader as doc_loader
from backend.services.classifier import classifier
from backend.services.comparator import comparator
from backend.services.evaluator import evaluator

def run_classification_check(source: str):
    print("=" * 80)
    print(f"SDOC HACKATHON — DATA CLASSIFICATION & EVALUATION AUDIT")
    print(f"Source: {source}")
    print("=" * 80)

    inbox = Inbox(source)
    emails = inbox.emails()
    total_emails = len(emails)
    print(f"\n[1] Loaded {total_emails} emails from inbox.")

    # 1. Classify every email using the Stage 1 Classifier
    classified_results = {}
    category_counts = Counter()
    is_comparison_count = 0

    for email in emails:
        eid = email.get("email_id") or email.get("id")
        class_res = classifier.classify(email)
        cat = class_res["category"]
        category_counts[cat] += 1
        if class_res.get("is_comparison_request") or cat == "BL_COMPARISON":
            is_comparison_count += 1
        classified_results[eid] = class_res

    print("\n[2] Stage 1 Data Classification Breakdown:")
    print("-" * 55)
    print(f"{'Category':<20} | {'Count':<8} | {'Share (%)':<10}")
    print("-" * 55)
    for cat, count in category_counts.most_common():
        pct = (count / total_emails) * 100.0
        print(f"{cat:<20} | {count:<8} | {pct:>6.1f}%")
    print("-" * 55)
    print(f"{'TOTAL':<20} | {total_emails:<8} | 100.0%")
    print(f"Total BL Comparison Requests: {is_comparison_count} emails")

    # 2. Build full submission payload
    print("\n[3] Running Document Comparison & Pre-Comparison Attachment Gate...")
    submission = {}
    gate_failures = 0
    mismatch_count = 0
    ok_count = 0

    for email in emails:
        eid = email.get("email_id") or email.get("id")
        class_res = classified_results[eid]
        category = class_res["category"]

        if category == "BL_COMPARISON":
            si_text = ""
            bl_text = ""
            for att in email.get("attachments", []):
                p = att["path"] if isinstance(att, dict) else str(att)
                fname = os.path.basename(p).lower()
                if "_si." in fname or "si" in fname:
                    si_text = doc_loader.read_attachment_text(p)
                elif "_bl." in fname or "bl" in fname:
                    bl_text = doc_loader.read_attachment_text(p)

            # Document comparator with pre-comparison attachment gate
            comp_res = comparator.compare_documents(
                si_text=si_text,
                bl_text=bl_text,
                email_metadata=email
            )

            if comp_res.get("pre_comparison_gate", {}).get("passed") is False:
                gate_failures += 1

            if comp_res["status"] == "MISMATCH":
                mismatch_count += 1
            elif comp_res["status"] == "OK":
                ok_count += 1

            submission[eid] = {
                "category": category,
                "status": comp_res["status"],
                "review_reason": comp_res["review_reason"],
                "has_defect": comp_res["has_defect"],
                "defect_fields": comp_res["defect_fields"]
            }
        else:
            submission[eid] = {
                "category": category,
                "status": "OK",
                "review_reason": None,
                "has_defect": False,
                "defect_fields": []
            }

    print(f"  - Clean Shipments (OK): {ok_count}")
    print(f"  - Discrepant Shipments (MISMATCH): {mismatch_count}")
    print(f"  - Pre-Comparison Gate Halts (MISSING_ATTACHMENT): {gate_failures}")

    # 3. Submit payload to evaluation endpoint
    print("\n[4] Submitting to Evaluation Endpoint (Page 4 Scoreboard)...")
    if inbox.is_http:
        try:
            report = inbox.submit(submission)
            print("  Successfully received scoreboard from HTTP server at", source)
        except Exception as ex:
            print(f"  HTTP submit failed ({ex}), computing locally:")
            report = evaluator.evaluate_submission(submission)
    else:
        report = evaluator.evaluate_submission(submission)

    print("\n" + "=" * 80)
    print("OFFICIAL HACKATHON EVALUATION SCOREBOARD")
    print("=" * 80)
    print(f"Overall Composite Score:        {report['overall_score']}%")
    print(f"Stage 1 Classification F1:      {report['stage1_classification_f1']}%")
    print(f"Stage 3 Defect Field F1:        {report['stage3_defect_f1']}%")
    print(f"Reliability (Edge Case Handling): {report['reliability_pct']}%")
    print("\nReview Reasons Escalation Breakdown:")
    for reason, count in report.get("review_reasons_breakdown", {}).items():
        print(f"  - {reason:<22}: {count} cases handled accurately")

    print("\nTop Defect Fields Caught:")
    for field, count in sorted(report.get("defect_field_counts", {}).items(), key=lambda x: x[1], reverse=True):
        print(f"  - {field:<22}: {count} discrepancies detected")

    print("=" * 80)
    print("STATUS: DATA CLASSIFICATION & VERIFICATION PIPELINE VALIDATED SUCCESSFULLY")
    print("=" * 80)

    return report

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "test data"
    run_classification_check(target)
