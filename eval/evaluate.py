#!/usr/bin/env python3
"""
evaluate.py — Compares system predictions against independent ground-truth labels.

This script contains NO fixed score components, NO self-referencing metrics.
Every number reported comes from comparing predictions to human labels.

Metrics reported:
  1. Classification macro-F1 (5 categories)
  2. Per-field precision / recall / F1 (7 fields)
  3. Missed discrepancy count (predicted OK, truly MISMATCH)
  4. Incorrect auto-approval count (predicted OK, truly defective)
  5. Human-review rate (fraction of emails routed to NEEDS_REVIEW)
  6. Escalation reason accuracy (for NEEDS_REVIEW: was the reason correct?)
  7. Overall status accuracy

Outputs:
  eval/results.json          — machine-readable results
  eval/results.md            — human-readable markdown table
  stdout                     — summary

Usage:
    python eval/evaluate.py --mode rules_only [--split dev|heldout|all]
    python eval/evaluate.py --mode rules_plus_llm [--split dev|heldout|all]
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "test data"))

LABELS_DIR = ROOT / "eval" / "labels"
EVAL_DIR = ROOT / "eval"

# The 5 classification categories
CATEGORIES = {"BL_COMPARISON", "SI_REQUEST", "INVOICE_QUERY", "GENERAL", "SPAM"}

# The 7 canonical SI-vs-BL comparison fields
FIELDS = [
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg",
]

# Mapping from label column names to canonical field names
FIELD_MATCH_COLS = {
    "shipper_match": "shipper",
    "consignee_match": "consignee",
    "notify_party_match": "notify_party",
    "pol_match": "port_of_loading",
    "pod_match": "port_of_discharge",
    "container_count_match": "container_count",
    "gross_weight_match": "gross_weight_kg",
}


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def safe_bool(val: str) -> Optional[bool]:
    """Parse TRUE/FALSE/NA from label CSV."""
    v = val.strip().upper()
    if v in ("TRUE", "1", "YES", "T"):
        return True
    if v in ("FALSE", "0", "NO", "F"):
        return False
    return None  # NA or empty


def macro_f1(y_true: list, y_pred: list, labels: set) -> Tuple[float, Dict]:
    """Compute macro-F1 across the given label set. Returns (macro_f1, per_class_dict)."""
    per_class = {}
    for label in sorted(labels):
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        per_class[label] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": sum(1 for t in y_true if t == label),
        }
    f1_scores = [v["f1"] for v in per_class.values() if v["support"] > 0]
    return (round(sum(f1_scores) / len(f1_scores), 4) if f1_scores else 0.0), per_class


def binary_prf(y_true: list, y_pred: list) -> Dict:
    """Binary precision/recall/F1 for defect detection at field level."""
    tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
    fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)
    tn = sum(1 for t, p in zip(y_true, y_pred) if not t and not p)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


# ──────────────────────────────────────────────────────────────────────
# Run pipeline on one email
# ──────────────────────────────────────────────────────────────────────

def run_pipeline(email: dict, mode: str) -> dict:
    """
    Run the pipeline on a single email.
    In rules_only: pure rule engine.
    In rules_plus_llm: rules first; LLM assists on low-confidence classifications (<0.90)
    and null/unmapped fields via extract_fields with strict provenance & validation.
    """
    from backend.services.classifier import classifier
    from backend.services.comparator import comparator

    class_res = classifier.classify(email)
    category = class_res["category"]

    if mode == "rules_plus_llm":
        from llm_agent.tasks import classify_email
        llm_class = classify_email(email, category, float(class_res.get("confidence", 1.0)))
        category = llm_class["category"]

    if category != "BL_COMPARISON":
        return {
            "category": category,
            "status": "OK",
            "review_reason": None,
            "has_defect": False,
            "defect_fields": [],
        }

    # For BL_COMPARISON, run comparator
    comp_res = comparator.compare_documents(
        si_text="",
        bl_text="",
        email_metadata=email,
    )

    # In rules_plus_llm mode, if comparator needed review due to missing values or unresolved labels:
    if mode == "rules_plus_llm" and comp_res["status"] == "NEEDS_REVIEW" and comp_res.get("review_reason") in ("missing_value", "term_unresolved"):
        from llm_agent.tasks import extract_fields
        from backend.services.dataset_loader import loader

        bl_text, si_text = "", ""
        for att in email.get("attachments", []):
            path = att.get("path") if isinstance(att, dict) else str(att)
            if "_bl." in path.lower() or "bl" in path.lower():
                bl_text = loader.read_attachment_text(path)
            elif "_si." in path.lower() or "si" in path.lower():
                si_text = loader.read_attachment_text(path)

        bl_ext = comp_res.get("bl_extracted") or {}
        missing = [f for f in comparator.FIELDS if bl_ext.get(f) is None]

        if missing and bl_text:
            doc_key = f"{email.get('email_id', 'unknown')}:BL"
            ext_res = extract_fields(missing, bl_text, doc_key=doc_key, doc_type="BL")
            proposals = ext_res.get("proposals", {})
            if proposals:
                overrides = {
                    "bl_overrides": {k: v["value"] for k, v in proposals.items()}
                }
                # Deterministic re-comparison with the validated proposals
                comp_res = comparator.compare_documents(
                    si_text=si_text,
                    bl_text=bl_text,
                    overrides=overrides,
                    email_metadata=email,
                )

    return {
        "category": category,
        "status": comp_res["status"],
        "review_reason": comp_res.get("review_reason"),
        "has_defect": comp_res.get("has_defect", False),
        "defect_fields": comp_res.get("defect_fields", []),
    }


# ──────────────────────────────────────────────────────────────────────
# Load ground truth
# ──────────────────────────────────────────────────────────────────────

def load_labels(split: str) -> List[dict]:
    """Load ground truth rows for the specified split."""
    if split == "all":
        path = LABELS_DIR / "ground_truth.csv"
    elif split == "dev":
        path = LABELS_DIR / "dev_split.csv"
    elif split == "heldout":
        path = LABELS_DIR / "heldout_split.csv"
    else:
        raise ValueError(f"Unknown split: {split}")

    if not path.exists():
        print(f"ERROR: Label file not found: {path}")
        if split in ("dev", "heldout"):
            print("  Run 'python eval/split.py' first.")
        else:
            print("  Fill in eval/labels/ground_truth.csv first.")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_inbox_email(email_id: str) -> Optional[dict]:
    """Load a single email from the inbox."""
    inbox_dir = ROOT / "test data" / "inbox"
    path = inbox_dir / f"{email_id}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ──────────────────────────────────────────────────────────────────────
# Main evaluation
# ──────────────────────────────────────────────────────────────────────

def evaluate(mode: str, split: str) -> dict:
    """Run evaluation and return results dict."""
    if mode == "rules_plus_llm":
        os.environ["DOCUMATCH_LLM_MODE"] = "assist"
        from llm_agent.client import llm_client
        if not llm_client.is_enabled:
            from eval.eval_transport import create_eval_transport
            llm_client.set_transport(create_eval_transport())
    else:
        os.environ["DOCUMATCH_LLM_MODE"] = "off"
        from llm_agent.client import llm_client
        llm_client.set_transport(None)

    labels = load_labels(split)
    print(f"Loaded {len(labels)} labelled examples from split='{split}' (mode='{mode}')")

    # ── Collect predictions ──
    cat_true = []
    cat_pred = []
    status_true = []
    status_pred = []
    review_reason_true = []
    review_reason_pred = []

    # Per-field defect detection (only for BL_COMPARISON emails)
    field_true = {f: [] for f in FIELDS}  # True: field has defect
    field_pred = {f: [] for f in FIELDS}  # Pred: field flagged as defect

    missed_discrepancies = []  # predicted OK, truly MISMATCH
    incorrect_auto_approvals = []  # predicted OK, truly has_defect
    needs_review_count = 0
    total_bl_comparison = 0
    errors = []

    for row in labels:
        email_id = row["email_id"].strip()
        true_category = row["category"].strip()
        true_status = row["expected_status"].strip()
        true_review_reason = row.get("review_reason", "").strip() or None
        true_defect_str = row.get("defect_fields", "").strip()
        true_defect_fields = set(
            f.strip() for f in true_defect_str.split(",") if f.strip()
        ) if true_defect_str else set()

        # Load email and get prediction
        email = load_inbox_email(email_id)
        if email is None:
            errors.append(f"Email not found: {email_id}")
            continue

        pred = run_pipeline(email, mode)

        # Classification
        cat_true.append(true_category)
        cat_pred.append(pred["category"])

        # Status (for BL_COMPARISON emails only)
        if true_category == "BL_COMPARISON":
            total_bl_comparison += 1
            status_true.append(true_status)
            status_pred.append(pred["status"])

            if pred["status"] == "NEEDS_REVIEW":
                needs_review_count += 1

            # Check missed discrepancy
            if pred["status"] == "OK" and true_status == "MISMATCH":
                missed_discrepancies.append(email_id)

            # Check incorrect auto-approval
            if pred["status"] == "OK" and true_defect_fields:
                incorrect_auto_approvals.append(email_id)

            # Escalation reason accuracy
            if true_status == "NEEDS_REVIEW" and true_review_reason:
                review_reason_true.append(true_review_reason)
                review_reason_pred.append(pred.get("review_reason") or "")

            # Per-field defect detection
            pred_defect_fields = set(pred.get("defect_fields", []))
            for field in FIELDS:
                # Parse field match column
                col_name = [k for k, v in FIELD_MATCH_COLS.items() if v == field][0]
                match_val = safe_bool(row.get(col_name, ""))
                if match_val is None:
                    continue  # Skip NA fields
                # true defect = match_val is False (field does NOT match)
                field_true[field].append(not match_val)
                field_pred[field].append(field in pred_defect_fields)
        else:
            # Non-BL emails: status should be OK, no defects
            status_true.append("OK")
            status_pred.append(pred["status"])

    # ── Compute metrics ──

    # 1. Classification macro-F1
    all_cats = CATEGORIES | set(cat_true) | set(cat_pred)
    classification_macro_f1, classification_per_class = macro_f1(cat_true, cat_pred, all_cats)

    # 2. Per-field precision/recall/F1
    field_metrics = {}
    for field in FIELDS:
        if field_true[field]:
            field_metrics[field] = binary_prf(field_true[field], field_pred[field])
        else:
            field_metrics[field] = {"tp": 0, "fp": 0, "fn": 0, "tn": 0,
                                     "precision": 0.0, "recall": 0.0, "f1": 0.0,
                                     "note": "no_labelled_data"}

    # Aggregate field-level metrics
    all_field_true = []
    all_field_pred = []
    for field in FIELDS:
        all_field_true.extend(field_true[field])
        all_field_pred.extend(field_pred[field])
    aggregate_field = binary_prf(all_field_true, all_field_pred) if all_field_true else {}

    # 3. Status accuracy
    status_accuracy = (
        sum(1 for t, p in zip(status_true, status_pred) if t == p) / len(status_true)
        if status_true
        else 0.0
    )
    status_macro_f1, status_per_class = macro_f1(
        status_true, status_pred, {"OK", "MISMATCH", "NEEDS_REVIEW"}
    )

    # 4. Escalation reason accuracy
    reason_accuracy = (
        sum(1 for t, p in zip(review_reason_true, review_reason_pred) if t == p)
        / len(review_reason_true)
        if review_reason_true
        else 0.0
    )

    # 5. Human review rate
    human_review_rate = needs_review_count / total_bl_comparison if total_bl_comparison > 0 else 0.0

    # ── Assemble results ──
    results = {
        "mode": mode,
        "split": split,
        "total_evaluated": len(labels),
        "errors": errors,
        "classification": {
            "macro_f1": classification_macro_f1,
            "per_class": classification_per_class,
        },
        "status": {
            "accuracy": round(status_accuracy, 4),
            "macro_f1": status_macro_f1,
            "per_class": status_per_class,
            "total_bl_comparison": total_bl_comparison,
        },
        "field_level_defect_detection": {
            "per_field": field_metrics,
            "aggregate": aggregate_field,
        },
        "missed_discrepancies": {
            "count": len(missed_discrepancies),
            "email_ids": missed_discrepancies,
        },
        "incorrect_auto_approvals": {
            "count": len(incorrect_auto_approvals),
            "email_ids": incorrect_auto_approvals,
        },
        "human_review_rate": {
            "needs_review_count": needs_review_count,
            "total_bl_comparison": total_bl_comparison,
            "rate": round(human_review_rate, 4),
        },
        "escalation_reason_accuracy": {
            "accuracy": round(reason_accuracy, 4),
            "total_evaluated": len(review_reason_true),
        },
    }

    return results


# ──────────────────────────────────────────────────────────────────────
# Output formatters
# ──────────────────────────────────────────────────────────────────────

def write_results_json(results: dict, path: Path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    print(f"  -> {path}")


def write_results_md(results: dict, path: Path):
    """Write a human-readable markdown report."""
    lines = []
    lines.append(f"# Evaluation Results")
    lines.append(f"")
    lines.append(f"- **Mode**: `{results['mode']}`")
    lines.append(f"- **Split**: `{results['split']}`")
    lines.append(f"- **Total evaluated**: {results['total_evaluated']}")
    if results["errors"]:
        lines.append(f"- **Errors**: {len(results['errors'])}")
    lines.append("")

    # Classification
    lines.append("## 1. Classification (5-category Macro-F1)")
    lines.append("")
    lines.append(f"**Macro-F1: {results['classification']['macro_f1']:.4f}**")
    lines.append("")
    lines.append("| Category | Precision | Recall | F1 | Support |")
    lines.append("|----------|-----------|--------|-----|---------|")
    for cat, m in sorted(results["classification"]["per_class"].items()):
        lines.append(
            f"| {cat} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} | {m['support']} |"
        )
    lines.append("")

    # Status
    lines.append("## 2. Status Accuracy (OK / MISMATCH / NEEDS_REVIEW)")
    lines.append("")
    lines.append(f"**Accuracy: {results['status']['accuracy']:.4f}** | **Macro-F1: {results['status']['macro_f1']:.4f}**")
    lines.append("")
    lines.append("| Status | Precision | Recall | F1 | Support |")
    lines.append("|--------|-----------|--------|-----|---------|")
    for s, m in sorted(results["status"]["per_class"].items()):
        lines.append(
            f"| {s} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} | {m['support']} |"
        )
    lines.append("")

    # Field-level
    lines.append("## 3. Field-Level Defect Detection")
    lines.append("")
    agg = results["field_level_defect_detection"].get("aggregate", {})
    if agg:
        lines.append(f"**Aggregate — Precision: {agg.get('precision', 0):.4f} | Recall: {agg.get('recall', 0):.4f} | F1: {agg.get('f1', 0):.4f}**")
    lines.append("")
    lines.append("| Field | TP | FP | FN | TN | Precision | Recall | F1 |")
    lines.append("|-------|----|----|----|----|-----------|--------|-----|")
    for field in FIELDS:
        m = results["field_level_defect_detection"]["per_field"][field]
        lines.append(
            f"| {field} | {m['tp']} | {m['fp']} | {m['fn']} | {m['tn']} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} |"
        )
    lines.append("")

    # Critical errors
    lines.append("## 4. Critical Errors")
    lines.append("")
    md = results["missed_discrepancies"]
    lines.append(f"- **Missed discrepancies** (predicted OK, truly MISMATCH): **{md['count']}**")
    if md["email_ids"]:
        lines.append(f"  - IDs: {', '.join(md['email_ids'][:20])}")
    iaa = results["incorrect_auto_approvals"]
    lines.append(f"- **Incorrect auto-approvals** (predicted OK, truly defective): **{iaa['count']}**")
    if iaa["email_ids"]:
        lines.append(f"  - IDs: {', '.join(iaa['email_ids'][:20])}")
    lines.append("")

    # Human review
    lines.append("## 5. Human Review & Escalation")
    lines.append("")
    hr = results["human_review_rate"]
    lines.append(f"- **Human review rate**: {hr['rate']:.2%} ({hr['needs_review_count']}/{hr['total_bl_comparison']} BL comparisons)")
    era = results["escalation_reason_accuracy"]
    lines.append(f"- **Escalation reason accuracy**: {era['accuracy']:.2%} ({era['total_evaluated']} evaluated)")
    lines.append("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"  -> {path}")


def print_summary(results: dict):
    """Print a concise summary to stdout."""
    print()
    print("=" * 70)
    print(f"  EVALUATION RESULTS — mode={results['mode']}, split={results['split']}")
    print("=" * 70)
    print(f"  Classification Macro-F1 :  {results['classification']['macro_f1']:.4f}")
    print(f"  Status Accuracy         :  {results['status']['accuracy']:.4f}")
    print(f"  Status Macro-F1         :  {results['status']['macro_f1']:.4f}")
    agg = results["field_level_defect_detection"].get("aggregate", {})
    if agg:
        print(f"  Field-Level P/R/F1      :  {agg.get('precision',0):.4f} / {agg.get('recall',0):.4f} / {agg.get('f1',0):.4f}")
    print(f"  Missed Discrepancies    :  {results['missed_discrepancies']['count']}")
    print(f"  Incorrect Auto-Approvals:  {results['incorrect_auto_approvals']['count']}")
    hr = results["human_review_rate"]
    print(f"  Human Review Rate       :  {hr['rate']:.2%}")
    era = results["escalation_reason_accuracy"]
    print(f"  Escalation Reason Acc   :  {era['accuracy']:.2%}")
    print("=" * 70)
    if results["errors"]:
        print(f"  WARNING: {len(results['errors'])} errors during evaluation")
    print()


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate DocuMatch pipeline against ground-truth labels."
    )
    parser.add_argument(
        "--mode",
        choices=["rules_only", "rules_plus_llm"],
        default="rules_only",
        help="Pipeline mode to evaluate (default: rules_only)",
    )
    parser.add_argument(
        "--split",
        choices=["dev", "heldout", "all"],
        default="dev",
        help="Which data split to evaluate on (default: dev)",
    )
    args = parser.parse_args()

    results = evaluate(args.mode, args.split)

    # Write outputs
    json_path = EVAL_DIR / "results.json"
    md_path = EVAL_DIR / "results.md"
    write_results_json(results, json_path)
    write_results_md(results, md_path)
    print_summary(results)


if __name__ == "__main__":
    main()
