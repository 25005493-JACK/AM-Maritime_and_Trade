#!/usr/bin/env python3
"""
evaluate_memory.py — Phase 5: Prove Correction Memory & Bayesian Trust Routing.

Workflow:
1. Split by carrier/sender_domain.
2. Apply reviewer corrections from dev documents into reflection memory and trust posteriors.
3. Evaluate on unseen held-out documents from the same carriers.
4. Compare Memory OFF vs Memory ON:
   - Memory OFF: Baseline prompts without reflections; uniform/bypassed trust gating.
   - Memory ON: Relevant reflections injected into prompts; Bayesian Thompson Sampling trust gating.
5. Output detailed metrics comparison table (Overall and Per-Carrier).
"""
import os
import sys
import csv
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "test data"))

from backend.services.reflection import (
    extract_domain,
    generate_reflection,
    retrieve_reflections,
)
from backend.services.routing_policy import (
    get_policy,
    sample_trust,
    update_routing_policy,
    DEFAULT_ROUTING_THRESHOLD,
)
from backend.services.classifier import classifier
from backend.services.comparator import comparator
from backend.services.dataset_loader import loader
from eval.evaluate import macro_f1, binary_prf, safe_bool, FIELDS, FIELD_MATCH_COLS, CATEGORIES
from eval.eval_transport import create_eval_transport
from llm_agent.client import llm_client


def train_memory_from_dev(dev_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Applies reviewer corrections from dev documents into:
    1. Reflexion episodic memory (agent_reflections).
    2. Thompson Sampling Beta-Bernoulli trust posteriors (routing_policy).
    """
    print(f"\n[Phase 5] Training memory from {len(dev_rows)} dev split documents...")
    corrections_applied = 0
    clean_matches_recorded = 0
    domain_stats = defaultdict(lambda: {"defects": 0, "clean": 0, "fields_corrected": []})

    for row in dev_rows:
        eid = row["email_id"].strip()
        expected_status = row["expected_status"].strip()
        category = row["category"].strip()
        defect_str = row.get("defect_fields", "").strip()
        defect_fields = [f.strip() for f in defect_str.split(",") if f.strip()]

        email_path = ROOT / "test data" / "inbox" / f"{eid}.json"
        if not email_path.exists():
            continue
        with open(email_path, "r", encoding="utf-8") as fh:
            email = json.load(fh)

        sender = email.get("sender") or email.get("from") or ""
        domain = extract_domain(sender)
        if not domain or domain == "unknown":
            continue

        if category == "BL_COMPARISON":
            if expected_status == "MISMATCH" or defect_fields:
                # Reviewer corrected defective fields
                for field in defect_fields:
                    true_val = row.get(f"{field}_si") or row.get(f"{field}_bl") or "verified_value"
                    err_val = row.get(f"{field}_bl") if true_val == row.get(f"{field}_si") else row.get(f"{field}_si")

                    # 1. Generate Reflection
                    generate_reflection({
                        "field": field,
                        "original_ai_value": str(err_val or "erroneous_draft_value"),
                        "corrected_value": str(true_val),
                        "sender": sender,
                        "doc_type": "BL",
                        "email_id": eid,
                        "context": f"Dev reviewer correction on {eid} for carrier {domain}.",
                    })
                    corrections_applied += 1
                    domain_stats[domain]["fields_corrected"].append(field)

                    # 2. Update Bayesian trust posterior (failure/defect decreases trust)
                    update_routing_policy(domain, field_name=field, ai_was_correct=False)

                # Overall domain update
                update_routing_policy(domain, field_name=None, ai_was_correct=False)
                domain_stats[domain]["defects"] += 1

            elif expected_status == "OK":
                # Clean match verified
                update_routing_policy(domain, field_name=None, ai_was_correct=True)
                clean_matches_recorded += 1
                domain_stats[domain]["clean"] += 1

    print(f"  -> Generated {corrections_applied} episodic reflections from dev reviewer corrections.")
    print(f"  -> Updated trust posteriors for {len(domain_stats)} carrier domains ({clean_matches_recorded} clean, {sum(d['defects'] for d in domain_stats.values())} defective).")

    return {
        "corrections_applied": corrections_applied,
        "clean_matches_recorded": clean_matches_recorded,
        "domain_stats": dict(domain_stats),
    }


def run_pipeline_with_memory(
    email: dict,
    mode: str = "rules_plus_llm",
    memory_enabled: bool = True,
) -> dict:
    """
    Runs verification pipeline on a single email.
    When memory_enabled=True:
      - Uses Bayesian trust posterior to gate low-trust carriers directly to human review.
      - Injects relevant reflections into Phase 4 prompts for unmapped fields.
    When memory_enabled=False:
      - Bypasses trust gating.
      - Uses baseline prompts without reflection memory.
    """
    sender = email.get("sender") or email.get("from") or ""
    domain = extract_domain(sender)

    class_res = classifier.classify(email)
    category = class_res["category"]

    if mode == "rules_plus_llm":
        from llm_agent.tasks import classify_email
        llm_class = classify_email(
            email, category, float(class_res.get("confidence", 1.0)),
            sender_domain=domain, memory_enabled=memory_enabled
        )
        category = llm_class["category"]

    if category != "BL_COMPARISON":
        return {
            "category": category,
            "status": "OK",
            "review_reason": None,
            "has_defect": False,
            "defect_fields": [],
            "gated_by_policy": False,
        }

    # For BL_COMPARISON, run comparator
    comp_res = comparator.compare_documents(
        si_text="",
        bl_text="",
        email_metadata=email,
    )

    gated_by_policy = False
    # If comparator needed review due to missing values or unresolved labels:
    if comp_res["status"] == "NEEDS_REVIEW" and comp_res.get("review_reason") in ("missing_value", "term_unresolved"):
        from llm_agent.tasks import extract_fields

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
            ext_res = extract_fields(
                missing, bl_text, doc_key=doc_key, doc_type="BL",
                sender_domain=domain, memory_enabled=memory_enabled
            )

            if ext_res.get("routed_to_human_by_policy"):
                gated_by_policy = True
                # Safely maintain NEEDS_REVIEW with audit tag
                return {
                    "category": category,
                    "status": "NEEDS_REVIEW",
                    "review_reason": "gated_by_policy",
                    "has_defect": comp_res.get("has_defect", False),
                    "defect_fields": comp_res.get("defect_fields", []),
                    "gated_by_policy": True,
                    "policy_routing": ext_res.get("policy_routing"),
                }

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
        "gated_by_policy": gated_by_policy,
    }


def evaluate_split_with_memory(
    heldout_rows: List[Dict[str, Any]],
    memory_enabled: bool,
) -> Dict[str, Any]:
    """Runs evaluation across held-out rows with Memory ON or OFF."""
    cat_true, cat_pred = [], []
    status_true, status_pred = [], []
    review_reason_true, review_reason_pred = [], []

    field_true = {f: [] for f in FIELDS}
    field_pred = {f: [] for f in FIELDS}

    missed_discrepancies = []
    incorrect_auto_approvals = []
    needs_review_count = 0
    total_bl_comparison = 0
    gated_count = 0

    per_carrier = defaultdict(lambda: {
        "total": 0, "ok": 0, "mismatch": 0, "needs_review": 0,
        "missed": 0, "gated": 0, "accuracy_hits": 0
    })

    for row in heldout_rows:
        eid = row["email_id"].strip()
        true_category = row["category"].strip()
        true_status = row["expected_status"].strip()
        true_review_reason = row.get("review_reason", "").strip() or None
        true_defect_str = row.get("defect_fields", "").strip()
        true_defect_fields = set(f.strip() for f in true_defect_str.split(",") if f.strip())

        email_path = ROOT / "test data" / "inbox" / f"{eid}.json"
        if not email_path.exists():
            continue
        with open(email_path, "r", encoding="utf-8") as fh:
            email = json.load(fh)

        domain = extract_domain(email.get("sender") or email.get("from") or "")

        pred = run_pipeline_with_memory(email, mode="rules_plus_llm", memory_enabled=memory_enabled)

        carrier_entry = per_carrier[domain]
        carrier_entry["total"] += 1
        if pred["status"] == true_status:
            carrier_entry["accuracy_hits"] += 1
        if pred.get("gated_by_policy"):
            carrier_entry["gated"] += 1
            gated_count += 1

        cat_true.append(true_category)
        cat_pred.append(pred["category"])

        if true_category == "BL_COMPARISON":
            total_bl_comparison += 1
            status_true.append(true_status)
            status_pred.append(pred["status"])

            if pred["status"] == "NEEDS_REVIEW":
                needs_review_count += 1
            if pred["status"] == "OK" and true_status == "MISMATCH":
                missed_discrepancies.append(eid)
                carrier_entry["missed"] += 1
            if pred["status"] == "OK" and true_defect_fields:
                incorrect_auto_approvals.append(eid)

            if true_status == "NEEDS_REVIEW" and true_review_reason:
                review_reason_true.append(true_review_reason)
                review_reason_pred.append(pred.get("review_reason") or "")

            pred_defect_fields = set(pred.get("defect_fields", []))
            for f in FIELDS:
                col_name = [k for k, v in FIELD_MATCH_COLS.items() if v == f][0]
                match_val = safe_bool(row.get(col_name, ""))
                if match_val is None:
                    continue
                field_true[f].append(not match_val)
                field_pred[f].append(f in pred_defect_fields)
        else:
            status_true.append("OK")
            status_pred.append(pred["status"])

    # Compute metrics
    classification_macro_f1, _ = macro_f1(cat_true, cat_pred, CATEGORIES | set(cat_true))

    field_metrics = {}
    all_field_true, all_field_pred = [], []
    for f in FIELDS:
        if field_true[f]:
            field_metrics[f] = binary_prf(field_true[f], field_pred[f])
            all_field_true.extend(field_true[f])
            all_field_pred.extend(field_pred[f])
        else:
            field_metrics[f] = {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    agg_field = binary_prf(all_field_true, all_field_pred) if all_field_true else {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    status_acc = sum(1 for t, p in zip(status_true, status_pred) if t == p) / max(len(status_true), 1)
    status_f1, _ = macro_f1(status_true, status_pred, {"OK", "MISMATCH", "NEEDS_REVIEW"})

    human_review_rate = (needs_review_count / total_bl_comparison) if total_bl_comparison > 0 else 0.0

    return {
        "memory_enabled": memory_enabled,
        "total_evaluated": len(heldout_rows),
        "total_bl_comparison": total_bl_comparison,
        "classification_macro_f1": round(classification_macro_f1, 4),
        "status_accuracy": round(status_acc, 4),
        "status_macro_f1": round(status_f1, 4),
        "field_precision": agg_field.get("precision", 0.0),
        "field_recall": agg_field.get("recall", 0.0),
        "field_f1": agg_field.get("f1", 0.0),
        "missed_discrepancies": len(missed_discrepancies),
        "incorrect_auto_approvals": len(incorrect_auto_approvals),
        "human_review_rate": round(human_review_rate, 4),
        "gated_by_policy_count": gated_count,
        "per_carrier": dict(per_carrier),
    }


def main():
    print("=" * 75)
    print("  PHASE 5: PROVE CORRECTION MEMORY & BAYESIAN TRUST ROUTING  ")
    print("=" * 75)

    os.environ["DOCUMATCH_LLM_MODE"] = "assist"
    if not llm_client.is_enabled:
        llm_client.set_transport(create_eval_transport())

    dev_path = ROOT / "eval" / "labels" / "dev_split.csv"
    heldout_path = ROOT / "eval" / "labels" / "heldout_split.csv"

    if not dev_path.exists() or not heldout_path.exists():
        print("ERROR: Split files not found. Run python eval/split.py first.")
        sys.exit(1)

    with open(dev_path, "r", encoding="utf-8") as fh:
        dev_rows = list(csv.DictReader(fh))
    with open(heldout_path, "r", encoding="utf-8") as fh:
        heldout_rows = list(csv.DictReader(fh))

    # 1. Train memory from dev split
    train_summary = train_memory_from_dev(dev_rows)

    # 2. Evaluate with Memory OFF
    print("\n[Phase 5] Evaluating held-out split with MEMORY = OFF...")
    results_off = evaluate_split_with_memory(heldout_rows, memory_enabled=False)

    # 3. Evaluate with Memory ON
    print("[Phase 5] Evaluating held-out split with MEMORY = ON...")
    results_on = evaluate_split_with_memory(heldout_rows, memory_enabled=True)

    # 4. Compare & Print Results
    print("\n" + "=" * 75)
    print("  PHASE 5 BENCHMARK COMPARISON: MEMORY OFF vs MEMORY ON (Held-out Split)")
    print("=" * 75)
    print(f"{'Metric':<30} | {'Memory OFF':<18} | {'Memory ON':<18} | {'Delta':<10}")
    print("-" * 75)

    metrics_to_show = [
        ("Classification Macro-F1", "classification_macro_f1", "{:.4f}"),
        ("Status Accuracy", "status_accuracy", "{:.4%}"),
        ("Status Macro-F1", "status_macro_f1", "{:.4f}"),
        ("Field-Level Defect Precision", "field_precision", "{:.4f}"),
        ("Field-Level Defect Recall", "field_recall", "{:.4f}"),
        ("Field-Level Defect F1", "field_f1", "{:.4f}"),
        ("Missed Discrepancies (Bad OK)", "missed_discrepancies", "{:d}"),
        ("Incorrect Auto-Approvals", "incorrect_auto_approvals", "{:d}"),
        ("Human Review Rate", "human_review_rate", "{:.2%}"),
        ("Gated by Policy (Thompson)", "gated_by_policy_count", "{:d}"),
    ]

    for label, key, fmt in metrics_to_show:
        v_off = results_off[key]
        v_on = results_on[key]
        delta_str = "0"
        if isinstance(v_off, float):
            d = v_on - v_off
            delta_str = f"{d:+.4f}" if abs(d) > 0.00001 else "0.0000"
        elif isinstance(v_off, int):
            d = v_on - v_off
            delta_str = f"{d:+d}" if d != 0 else "0"
        print(f"{label:<30} | {fmt.format(v_off):<18} | {fmt.format(v_on):<18} | {delta_str:<10}")

    print("=" * 75)

    # Per Carrier Breakdown
    print("\nPer-Carrier Trust & Review Gating Breakdown (Held-out Split):")
    print(f"{'Carrier / Sender Domain':<30} | {'Docs':<5} | {'Off Acc':<8} | {'On Acc':<8} | {'Gated by Policy':<15} | {'Mean Trust':<10}")
    print("-" * 88)

    all_domains = sorted(set(list(results_off["per_carrier"].keys()) + list(results_on["per_carrier"].keys())))
    for d in all_domains:
        c_off = results_off["per_carrier"].get(d, {"total": 0, "accuracy_hits": 0, "gated": 0})
        c_on = results_on["per_carrier"].get(d, {"total": 0, "accuracy_hits": 0, "gated": 0})
        total = c_on["total"]
        if total == 0:
            continue
        acc_off = c_off["accuracy_hits"] / total
        acc_on = c_on["accuracy_hits"] / total
        pol = get_policy(d)
        trust_str = f"{pol['mean_trust']:.1%}" if pol else "50.0%"
        gated_str = f"{c_on['gated']} / {total}"
        print(f"{d:<30} | {total:<5} | {acc_off:<8.1%} | {acc_on:<8.1%} | {gated_str:<15} | {trust_str:<10}")

    print("=" * 88)

    # Save output artifacts
    output_payload = {
        "train_summary": train_summary,
        "results_off": results_off,
        "results_on": results_on,
    }
    with open(ROOT / "eval" / "memory_results.json", "w", encoding="utf-8") as fh:
        json.dump(output_payload, fh, indent=2)

    print(f"\n[OK] Machine-readable results saved to: {ROOT / 'eval' / 'memory_results.json'}")


if __name__ == "__main__":
    main()
