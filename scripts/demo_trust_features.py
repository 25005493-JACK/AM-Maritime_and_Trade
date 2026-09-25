#!/usr/bin/env python3
"""
demo_trust_features.py - the 5-minute trust demo, end to end.

  1. Reasoning Receipt on a normal document  -> "N tokens / rules vs AI" summary
  2. Red Team -> Reword                      -> AI fallback, evidence-validated
  3. Red Team -> Remove field                -> circuit breaker + refusal certificate
  4. Automation slider L1 -> L3 -> back to L1 -> live tiles + card states

Usage:
  python demo_trust_features.py                 # walk all four steps
  python demo_trust_features.py --step 2        # single step
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "test data"))

import backend.main as api  # noqa: E402

BOLD, DIM, END = "\033[1m", "\033[2m", "\033[0m"
GREEN, CYAN, YELLOW, RED, PURPLE = "\033[92m", "\033[96m", "\033[93m", "\033[91m", "\033[95m"


def _shipment_id(email_id: str) -> str:
    return api._derive_shipment_id_from_email(api.loader.get_email(email_id))


def _client():
    from fastapi.testclient import TestClient

    return TestClient(api.app)


def step1(client, email_id: str) -> dict:
    shipment_id = _shipment_id(email_id)
    print(f"\n{BOLD}STEP 1 - Reasoning Receipt{END}")
    receipt = client.get(f"/api/shipments/{shipment_id}/receipt").json()
    print(f"  shipment {shipment_id} / {len(receipt['fields'])} field decisions")
    for row in receipt["fields"]:
        path_colour = {"rule": CYAN, "ai": PURPLE, "human": GREEN}[row["decision_path"]]
        validators = " ".join(f"{v['name']}:{v['status'][0].upper()}" for v in row["validators"])
        print(f"    {row['field_name']:18s} {path_colour}{row['decision_path']:5s}{END} "
              f"{row['rule_matched'] or '-':28s} {validators}")
    summary = receipt["summary"]
    print(f"  {BOLD}{summary['summary_line']}{END}")
    print(f"  {DIM}{summary['tokens_note']}{END}")
    return receipt


def step2(client, email_id: str) -> dict:
    print(f"\n{BOLD}STEP 2 - Red Team: Reword (rules miss, AI fallback fires){END}")
    result = client.post(f"/api/shipments/{email_id}/red-team", json={"transform": "reword"}).json()
    print(f"  {result['notes'][0]}")
    print(f"  comparison: {result['before']['status']} -> {result['after']['status']}")
    for attempt in result["receipt"]["documents"][0]["ai_attempts"]:
        status = f"{GREEN}accepted{END}" if attempt["accepted"] else f"{RED}rejected{END}"
        evidence = (attempt.get("evidence") or {}).get("exact_text")
        print(f"    {attempt['field_key']:18s} {status}  value={attempt['attempted_value']!r}")
        if evidence:
            print(f"      {DIM}evidence: \"{evidence}\"{END}")
    print(f"  {DIM}provider={result['receipt']['summary']['provider']['name']} "
          f"tokens={result['receipt']['summary']['total_tokens']}{END}")
    return result


def step3(client, email_id: str) -> dict:
    print(f"\n{BOLD}STEP 3 - Red Team: Remove field (circuit breaker){END}")
    result = client.post(f"/api/shipments/{email_id}/red-team", json={"transform": "remove_field"}).json()
    print(f"  {result['notes'][0]}")
    certificate = result.get("refusal_certificate")
    if not certificate:
        print(f"  {YELLOW}circuit breaker did not trip on this document{END}")
        return result
    print(f"  {RED}{certificate['reason']}{END}")
    print(f"  failed fields: {', '.join(f['field_name'] for f in certificate['failed_fields'])}")
    for failure in certificate["failed_fields"]:
        print(f"    - {failure['field_name']}: {failure['why_failed']}")
    print(f"  suggested recipient: {CYAN}{certificate['suggested_recipient']}{END} "
          f"({certificate['recipient_rationale']})")
    print(f"  estimated delay: {certificate['estimated_delay_hours']}h "
          f"{DIM}({certificate['estimated_delay_basis']}){END}")
    print(f"  {DIM}{certificate['notice']}{END}")
    return result


def step4(client) -> None:
    print(f"\n{BOLD}STEP 4 - Automation level slider{END}")
    for level in (1, 3, 1):
        payload = client.post("/api/settings/automation-level", json={"level": level}).json()
        preview = payload["preview"]
        print(f"  L{level}: auto={preview['auto_processed_pct']}%  "
              f"review={preview['flagged_for_review_pct']}%  "
              f"exposure={preview['estimated_error_exposure_pct']}%  "
              f"time saved={preview['estimated_time_saved_minutes']}min")
        print(f"    {DIM}basis: {preview['sample_basis']['emails_considered']} emails / "
              f"{preview['sample_basis']['fields_considered']} compared fields{END}")
    states: dict = {}
    for email in client.get("/api/emails").json():
        state = (email.get("automation") or {}).get("state")
        states[state] = states.get(state, 0) + 1
    print(f"  inbox card states after the last change: {states}")
    print(f"  {DIM}L1 is the safer default: nothing is written without a human confirmation.{END}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Trust-feature demo")
    parser.add_argument("--email", default="email_004", help="inbox email used for steps 1-3")
    parser.add_argument("--step", type=int, choices=[1, 2, 3, 4], default=None)
    args = parser.parse_args()

    client = _client()
    steps = {1: lambda: step1(client, args.email),
             2: lambda: step2(client, args.email),
             3: lambda: step3(client, args.email),
             4: lambda: step4(client)}
    for number in ([args.step] if args.step else [1, 2, 3, 4]):
        steps[number]()
    print(f"\n{GREEN}Demo complete.{END} Endpoints: /api/shipments/{{id}}/receipt, "
          f"/api/shipments/{{id}}/refusal-certificate, /api/shipments/{{id}}/red-team, "
          f"/api/settings/automation-level/preview")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
