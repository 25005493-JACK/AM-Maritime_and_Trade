#!/usr/bin/env python3
"""
demo_dcsa_conflict.py - SI vs draft BL conflict -> reviewer decision -> DCSA export.

  1. load a shipment whose SI and draft BL disagree on one or more fields
     (default: email_004 - the SI and BL consignees differ);
  2. print both candidate values side by side with their *exact quoted* source
     text, offsets, line numbers and code-list checks - nothing is auto-resolved;
  3. let the reviewer pick a value (or supply a third value);
  4. write the reviewer-confirmed record structured by DCSA Bill of Lading field
     names and export it as JSON.

Usage:
  python demo_dcsa_conflict.py                       # evidence only
  python demo_dcsa_conflict.py --choose si --reviewer "Pohyi Chong"
  python demo_dcsa_conflict.py --field consignee --choose bl
  python demo_dcsa_conflict.py --choose custom --value "EAST BRIGHT FZ-LLC, DUBAI"
  python demo_dcsa_conflict.py --email email_055 --field container_count --choose bl
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services import correction_flow  # noqa: E402
from backend.services.comparator import comparator  # noqa: E402
from backend.services.dataset_loader import loader  # noqa: E402

C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_CYAN = "\033[96m"
C_YELLOW = "\033[93m"
C_DIM = "\033[2m"
C_BOLD = "\033[1m"
C_END = "\033[0m"


def _doc_texts(email: Dict[str, Any]) -> tuple:
    si_text = bl_text = ""
    for att in email.get("attachments", []):
        path = att["path"] if isinstance(att, dict) else str(att)
        if "_si." in path.lower():
            si_text = loader.read_attachment_text(path)
        elif "_bl." in path.lower():
            bl_text = loader.read_attachment_text(path)
    return si_text, bl_text


def _fmt_candidate(candidate: Dict[str, Any], label: str) -> str:
    return "\n".join([
        f"  {C_BOLD}{label}{C_END} ({candidate['document']})",
        f"    value        : {candidate['value']}",
        f"    char_offset  : {candidate['char_offset']}  (line {candidate['line_number']})",
        f"    exact text   : {C_DIM}\"{candidate['exact_text']}\"{C_END}",
        f"    span match   : {candidate['span_match']}",
    ])


def show_proposals(email_id: str, proposals: Dict[str, Any]) -> None:
    print(f"\n{C_BOLD}DCSA standard{C_END}: {proposals['standard']['name']}")
    print(f"{C_BOLD}Shipment{C_END}     : {email_id}")
    print(f"{C_BOLD}Policy{C_END}       : {proposals['policy']}")
    print(f"{C_BOLD}Auto-resolve{C_END} : {C_YELLOW}{proposals['auto_resolution']}{C_END} "
          f"(a reviewer decision is required for every conflict)\n")

    if not proposals["proposals"]:
        print(f"{C_GREEN}No conflicts: every compared field agrees.{C_END}")
        return

    for proposal in proposals["proposals"]:
        badge = (f"{C_CYAN}DCSA: {proposal['dcsa_field']}{C_END}" if proposal["dcsa_field"]
                 else f"{C_YELLOW}DCSA: (internal only){C_END}")
        print(f"{C_RED}CONFLICT{C_END} {C_BOLD}{proposal['field_name']}{C_END} "
              f"[{proposal['field_key']}]  {badge}")
        print(f"  reason: {proposal['reason']}")
        print(_fmt_candidate(proposal["si_candidate"], "SI  "))
        print(_fmt_candidate(proposal["bl_candidate"], "BL  "))
        print()



def resolve(
    email_id: str,
    field_key: Optional[str],
    choice: str,
    value: Optional[str],
    reviewer: str,
    all_fields: bool = False,
) -> Dict[str, Any]:
    email = loader.get_email(email_id)
    si_text, bl_text = _doc_texts(email)
    verification = comparator.compare_documents(si_text, bl_text, email_metadata=email)
    proposals = correction_flow.build_conflict_proposals(email_id, verification, si_text, bl_text, email)

    targets = [p["field_key"] for p in proposals["proposals"]]
    if not all_fields:
        targets = [field_key] if field_key else targets[:1]
    decisions: List[Dict[str, Any]] = []
    for target in targets:
        decision: Dict[str, Any] = {"field_key": target, "choice": choice}
        if choice == "custom":
            decision["value"] = value
        decisions.append(decision)

    print(f"{C_BOLD}Reviewer decision{C_END}: {reviewer} -> "
          + ", ".join(f"{d['field_key']}={d['choice']}" for d in decisions))
    return correction_flow.apply_human_resolution(
        email_id, decisions, reviewer,
        verification=verification, si_text=si_text, bl_text=bl_text, email=email,
    )


def show_result(result: Dict[str, Any]) -> None:
    record = result["resolved_bl"]
    print(f"\n{C_GREEN}Resolved record{C_END} (reviewer-confirmed, DCSA field names)")
    print(f"  reviewer        : {record['reviewer']}")
    print(f"  generated_at    : {record['generated_at']}")
    print(f"  standard        : {record['standard']['name']}")
    print(f"  corrections log : {result['corrections_logged']} row(s) written (with DCSA field column)")
    if result["pending_decisions"]:
        print(f"  {C_YELLOW}pending         : {', '.join(result['pending_decisions'])} "
              f"(left unresolved on purpose){C_END}")

    print(f"\n{C_BOLD}DCSA-mapped transport document{C_END}")
    print(json.dumps({"transportDocument": record["transportDocument"]}, indent=2, ensure_ascii=False))

    if record["internal_only_fields"]:
        print(f"{C_DIM}internal-only fields (no DCSA BoL equivalent): "
              f"{json.dumps(record['internal_only_fields'], ensure_ascii=False)}{C_END}")

    print(f"\n{C_BOLD}Flattened DCSA paths{C_END}")
    for path, value in result["dcsa_export"].items():
        print(f"  {path} = {value}")

    print(f"\n{C_GREEN}Exported{C_END}: {correction_flow.resolved_record_path(result['email_id'])}")
    print(f"{C_DIM}{record['notice']}{C_END}")


def main() -> int:
    parser = argparse.ArgumentParser(description="SI/BL conflict -> reviewer decision -> DCSA export")
    parser.add_argument("--email", default="email_004", help="inbox email id (default: email_004)")
    parser.add_argument("--field", default=None, help="internal field key to decide (default: first conflict)")
    parser.add_argument("--choose", choices=["si", "bl", "custom"], default=None,
                        help="reviewer choice; omit to only show the evidence")
    parser.add_argument("--value", default=None, help="value for --choose custom")
    parser.add_argument("--reviewer", default="Pohyi Chong", help="reviewer recorded in the log")
    parser.add_argument("--all", action="store_true", help="apply the choice to every conflicting field")
    args = parser.parse_args()

    email = loader.get_email(args.email)
    if not email:
        print(f"{C_RED}Unknown email id: {args.email}{C_END}")
        return 2

    si_text, bl_text = _doc_texts(email)
    verification = comparator.compare_documents(si_text, bl_text, email_metadata=email)
    proposals = correction_flow.build_conflict_proposals(args.email, verification, si_text, bl_text, email)
    show_proposals(args.email, proposals)

    if not proposals["proposals"]:
        return 0

    if not args.choose:
        print(f"{C_YELLOW}Nothing was auto-resolved.{C_END} Re-run with "
              f"--choose si|bl|custom to record your decision.")
        return 0

    if args.choose == "custom" and not args.value:
        print(f"{C_RED}--choose custom requires --value{C_END}")
        return 2

    result = resolve(args.email, args.field, args.choose, args.value, args.reviewer, args.all)
    show_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
