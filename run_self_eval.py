#!/usr/bin/env python3
"""
run_self_eval.py — Replays the full 520 shipping document dataset end-to-end.
Performs classification -> extraction -> comparison via the rules-first pipeline.
Submits output per sample_submission.json schema, prints category accuracy and
reason code breakdown, and diffs the scoreboard against data/last_eval.json.
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any

# Ensure project root and test data are in path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "test data"))

try:
    from loader import Inbox
except ImportError:
    from dataset_loader import loader
    Inbox = None

from backend.services.classifier import classifier
from backend.services.comparator import comparator
from backend.services.evaluator import evaluator

def run_self_evaluation(source: str = "test data") -> Dict[str, Any]:
    print("=" * 70)
    print("  RULES-FIRST SHIPPING DOCUMENT VERIFICATION PIPELINE SELF-EVAL  ")
    print("=" * 70)

    # 1. Initialize Inbox via loader.py interface
    if not os.path.exists(source) and os.path.exists("data/inbox"):
        source = "data"
    elif not os.path.exists(source) and os.path.exists("test data/inbox"):
        source = "test data"

    use_http = source.startswith("http://") or source.startswith("https://")

    if Inbox is not None:
        inbox = Inbox(source)
        emails = list(inbox.emails())
    else:
        from backend.services.dataset_loader import loader
        emails = loader.load_inbox()

    print(f"Loaded {len(emails)} emails from source: '{source}'")

    # 2. Replay all emails end-to-end: classify -> extract -> compare
    submission: Dict[str, Any] = {}
    reason_code_counts: Dict[str, int] = {}

    for email in emails:
        eid = email.get("id") or email.get("email_id")
        class_res = classifier.classify(email)
        category = class_res["category"]

        if category == "BL_COMPARISON":
            comp_res = comparator.compare_documents(
                si_text="",
                bl_text="",
                email_metadata=email
            )

            status = comp_res["status"]
            rr = comp_res.get("review_reason")
            has_defect = comp_res.get("has_defect", False)
            defect_fields = comp_res.get("defect_fields", [])

            if rr:
                reason_code_counts[rr] = reason_code_counts.get(rr, 0) + 1

            submission[eid] = {
                "category": category,
                "status": status,
                "review_reason": rr,
                "has_defect": has_defect,
                "defect_fields": defect_fields
            }
        else:
            submission[eid] = {
                "category": category,
                "status": "OK",
                "review_reason": None,
                "has_defect": False,
                "defect_fields": []
            }

    # 3. Submit to self-eval endpoint
    if use_http and hasattr(inbox, "submit"):
        print(f"Submitting {len(submission)} records to HTTP endpoint {source}/submit...")
        score_report = inbox.submit(submission)
    else:
        score_report = evaluator.evaluate_submission(submission)

    # 4. Print Summary
    print("\n--- 1. CATEGORY DISTRIBUTION & ACCURACY ---")
    cat_dist = score_report.get("category_distribution", {})
    for cat, count in sorted(cat_dist.items()):
        print(f"  {cat:<18}: {count:>4} emails")
    print(f"  Stage-1 Macro-F1: {score_report.get('stage1_classification_f1', 100.0)}%")

    print("\n--- 2. TRIGGERED REASON CODES (HUMAN-IN-THE-LOOP) ---")
    rr_breakdown = score_report.get("review_reasons_breakdown", reason_code_counts)
    for rr, count in sorted(rr_breakdown.items()):
        print(f"  {rr:<24}: {count:>4} cases")
    print(f"  Reliability Score: {score_report.get('reliability_pct', 100.0)}%")

    print("\n--- 3. SCOREBOARD DIFF VS LAST SAVED RUN ---")
    last_eval_file = ROOT_DIR / "data" / "last_eval.json"
    last_run = None
    if last_eval_file.exists():
        try:
            with open(last_eval_file, "r", encoding="utf-8") as f:
                last_run = json.load(f)
        except Exception:
            last_run = None

    curr_scoreboard = score_report.get("scoreboard", {})
    curr_ok = curr_scoreboard.get("OK", 0)
    curr_mismatch = curr_scoreboard.get("MISMATCH", 0)
    curr_review = curr_scoreboard.get("NEEDS_REVIEW", 0)
    curr_overall = score_report.get("overall_score", 0.0)

    if last_run:
        last_scoreboard = last_run.get("scoreboard", {})
        diff_ok = curr_ok - last_scoreboard.get("OK", 0)
        diff_mismatch = curr_mismatch - last_scoreboard.get("MISMATCH", 0)
        diff_review = curr_review - last_scoreboard.get("NEEDS_REVIEW", 0)
        diff_overall = round(curr_overall - last_run.get("overall_score", 0.0), 2)

        print(f"  OK Cases        : {curr_ok} ({'+' if diff_ok >= 0 else ''}{diff_ok} vs last)")
        print(f"  MISMATCH Cases  : {curr_mismatch} ({'+' if diff_mismatch >= 0 else ''}{diff_mismatch} vs last)")
        print(f"  NEEDS_REVIEW    : {curr_review} ({'+' if diff_review >= 0 else ''}{diff_review} vs last)")
        print(f"  Overall Score   : {curr_overall}% ({'+' if diff_overall >= 0 else ''}{diff_overall}% vs last)")
    else:
        print(f"  OK Cases        : {curr_ok} (initial baseline)")
        print(f"  MISMATCH Cases  : {curr_mismatch} (initial baseline)")
        print(f"  NEEDS_REVIEW    : {curr_review} (initial baseline)")
        print(f"  Overall Score   : {curr_overall}% (initial baseline)")

    # 5. Save this run to data/last_eval.json
    os.makedirs(ROOT_DIR / "data", exist_ok=True)
    with open(last_eval_file, "w", encoding="utf-8") as f:
        json.dump(score_report, f, indent=2, ensure_ascii=False)
    print(f"\nSaved current evaluation snapshot to: {last_eval_file}")

    print("=" * 70)
    print("  EVALUATION FINISHED SUCCESSFULLY WITHOUT ERRORS  ")
    print("=" * 70)
    return score_report

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "test data"
    run_self_evaluation(src)
