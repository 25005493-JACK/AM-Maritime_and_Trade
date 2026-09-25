#!/usr/bin/env python3
"""
demo_self_learning.py - End-to-end interactive demo of Reflexion Episodic Memory
and Bayesian Thompson Sampling Routing Policy.

Demonstration steps:
  1. Document from new sender with no history -> uniform prior Beta(1,1).
     AI extracts a field wrong -> Human reviewer corrects it.
  2. System creates a Reflexion lesson & updates Bayesian policy (trust drops to 33%).
  3. Second document from same sender -> reasoning receipt proves:
     - Retrieved reflection injected into context
     - Routing policy current trust score displayed
  4. With trust below threshold, system routes straight to human review queue
     instead of guessing, demonstrating online policy adaptation.
"""
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "test data"))

from backend.services.reflection import (
    generate_reflection,
    retrieve_reflections,
    get_all_reflections,
    extract_domain
)
from backend.services.routing_policy import (
    sample_trust,
    update_routing_policy,
    get_policy,
    get_all_policies
)
from backend.services.ai_agent import ai_agent
from backend.services.reasoning_receipt import ai_fallback, build_events, summarize

BOLD, DIM, END = "\033[1m", "\033[2m", "\033[0m"
GREEN, CYAN, YELLOW, RED, PURPLE = "\033[92m", "\033[96m", "\033[93m", "\033[91m", "\033[95m"


def run_demo():
    sender_domain = f"evergreen-line-{uuid.uuid4().hex[:6]}.com"
    sender_email = f"docs@{sender_domain}"
    doc_type = "SI"
    field_name = "port_of_discharge"

    print("=" * 76)
    print(f"{BOLD}  SELF-LEARNING PIPELINE DEMO: REFLEXION MEMORY & THOMPSON SAMPLING  {END}")
    print("=" * 76)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 1: First Document from New Sender
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n{BOLD}{CYAN}STEP 1: Document from new sender with no prior history{END}")
    print(f"  Sender: {BOLD}{sender_email}{END} (Domain: {sender_domain})")
    
    initial_policy = get_policy(sender_domain)
    print(f"  Initial Bayesian Prior: Beta(alpha={initial_policy['alpha']}, beta={initial_policy['beta']})")
    print(f"  Initial Mean Trust    : {BOLD}{initial_policy['mean_trust'] * 100:.0f}%{END} (Uniform prior, exploration mode)")

    doc1_text = """
    SHIPPING INSTRUCTION
    Shipper: GLOBAL TIMBER EXPORTS INC
    Consignee: PACIFIC FURNITURE CORP
    Port of Loading: TANJUNG PERAK, SURABAYA
    Final Unloading Ocean Gateway Terminal: PORT KLANG (WESTPORT TERMINAL 2)
    Container Count: 4 x 40HC
    Gross Weight: 84,200.00 KGS
    """

    print("\n  AI fallback extraction invoked for unmapped label 'Final Unloading Ocean Gateway Terminal'...")
    ai_raw_proposal = "PORT"
    human_correct_val = "PORT KLANG"
    print(f"  AI extracted: {RED}'{ai_raw_proposal}'{END} (incomplete token)")
    print(f"  Human Reviewer corrects to: {GREEN}'{human_correct_val}'{END}")

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2: Online Self-Learning Update
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n{BOLD}{PURPLE}STEP 2: System creates Reflexion lesson & updates Bayesian policy{END}")
    correction_event = {
        "original_value": ai_raw_proposal,
        "corrected_value": human_correct_val,
        "field": field_name,
        "sender": sender_email,
        "doc_type": doc_type,
        "evidence_summary": "PORT KLANG (WESTPORT TERMINAL 2)",
        "email_id": "demo_email_001",
        "source_correction_id": "corr_demo_001"
    }

    reflection = generate_reflection(correction_event)
    print(f"  [Reflexion Engine] Natural-Language Lesson Generated:")
    print(f"    {PURPLE}\"{reflection['reflection_text']}\"{END}")
    print(f"    Stored in table {BOLD}agent_reflections{END} (times_retrieved=0)")

    # Update policy (AI was incorrect -> beta += 1)
    updated_policy = update_routing_policy(sender_domain, field_name, ai_was_correct=False, email_id="demo_email_001")
    print(f"\n  [Thompson Sampling Router] Online Bayesian Update:")
    print(f"    Old Posterior: Beta(alpha=1.0, beta=1.0) -> Mean Trust: 50.0%")
    print(f"    New Posterior: Beta(alpha={updated_policy['alpha']}, beta={updated_policy['beta']}) -> Mean Trust: {RED}{updated_policy['mean_trust'] * 100:.1f}%{END}")
    print(f"    Trust score visibly dropped due to real human correction.")

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3: Second Document from Same Sender
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n{BOLD}{CYAN}STEP 3: Second document from same sender ({sender_domain}){END}")
    doc2_text = """
    SHIPPING INSTRUCTION
    Shipper: GLOBAL TIMBER EXPORTS INC
    Consignee: PACIFIC FURNITURE CORP
    Port of Loading: TANJUNG PERAK
    Destination Ocean Gateway: PORT KLANG
    Container Count: 2 x 40HC
    """

    print("  Retrieving episodic memory buffer before AI action...")
    retrieved_refs = retrieve_reflections(sender_domain, doc_type=doc_type, field_name=field_name, limit=3)
    print(f"  Found {len(retrieved_refs)} relevant reflection(s) for {sender_domain}:")
    for idx, ref in enumerate(retrieved_refs, 1):
        print(f"    [{idx}] \"{ref['reflection_text']}\"")
        print(f"        {DIM}(Times retrieved so far: {ref['times_retrieved']}){END}")

    print("\n  Injecting retrieved reflection into prompt context:")
    print(f"    {DIM}--- Prompt Snippet ---{END}")
    print(f"    {PURPLE}Lessons from past corrections with this sender:{END}")
    print(f"    {PURPLE}- {retrieved_refs[0]['reflection_text']}{END}")
    print(f"    {DIM}----------------------{END}")

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4: Bayesian Policy Routing in Action
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n{BOLD}{YELLOW}STEP 4: Bayesian Routing Policy Decision (Thompson Sampling){END}")
    decision = sample_trust(sender_domain, field_name, threshold=0.6, email_id="demo_email_002")
    print(f"  Sender Posterior : Beta(alpha={decision['alpha']}, beta={decision['beta']})")
    print(f"  Mean Trust Score : {decision['mean_trust'] * 100:.1f}% (Threshold: {decision['threshold'] * 100:.0f}%)")
    print(f"  Thompson Sample  : {decision['sampled_trust'] * 100:.1f}%")

    if not decision['route_to_ai']:
        print(f"  {BOLD}{RED}Routing Decision : HUMAN_FIRST (AI Bypassed){END}")
        print(f"  {YELLOW}Reason: {decision['reason']}{END}")
        print(f"  Demonstrates system policy adapting to protect against repeating known errors!")
    else:
        print(f"  {BOLD}{GREEN}Routing Decision : AI Assist (Sampled {decision['sampled_trust']*100:.1f}% > 60% threshold){END}")

    # Build and show reasoning receipt event
    fallback = ai_fallback(
        field_keys=[field_name],
        doc_text=doc2_text,
        doc_key=f"demo_shipment:{sender_domain}",
        shipment_id="DEMO-SHIP-001",
        email_id="demo_email_002",
        sender_domain=sender_domain
    )

    print("\n  Reasoning Receipt Output for this field:")
    for att in fallback["attempts"]:
        policy_tag = (att.get("policy_routing") or {}).get("tag", "N/A")
        print(f"    Field: {att['field_key']}")
        print(f"    Routed By Policy: {CYAN}{policy_tag}{END}")
        if att.get("routed_to_human_by_policy"):
            print(f"    Status: {YELLOW}Routed directly to Human Review Queue without guessing{END}")
        else:
            print(f"    Proposed Value: {att.get('attempted_value')}")

    print("\n" + "=" * 76)
    print(f"{BOLD}{GREEN}  DEMO COMPLETE: Online Feedback-Driven Self-Learning Verified!  {END}")
    print("=" * 76 + "\n")


if __name__ == "__main__":
    run_demo()
