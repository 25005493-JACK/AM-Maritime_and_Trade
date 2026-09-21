"""
Reasoning receipt: an auditable record of every field-level decision.

This module only OBSERVES the existing pipeline - it re-runs nothing and rewrites
no logic. It reads the extraction audit trail (field_bank / anchors), the
comparator verdict, the AI agent's proposals and the reviewer's corrections, and
emits one receipt row per field:

    { email_id, field_name, decision_path: "rule"|"ai"|"human",
      rule_matched, ai_fields_read, ai_fields_skipped,
      source_evidence: {document, page, char_offset, exact_text},
      validators: [{name, status}], final_decision_by,
      token_cost, latency_ms }

plus shipment-level aggregates (total_ai_calls, total_tokens, total_latency_ms)
that make the "rules first, AI sparingly" claim measurable.
"""
import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.services import dcsa_mapping, field_evidence
from backend.services.ai_agent import ai_agent, provider_status
from backend.services.circuit_breaker import CircuitBreaker, circuit_breaker
from backend.services.comparator import comparator

#: Fields resolved by the dedicated numeric anchor parsers rather than field_bank.
ANCHOR_FIELDS = {"container_count", "gross_weight_kg"}


def _extracted(verification: Optional[Dict[str, Any]], side: str) -> Dict[str, Any]:
    data = (verification or {}).get(f"{side}_extracted") or {}
    return data if isinstance(data, dict) else {}


def _audit_method(extracted: Dict[str, Any], field_key: str) -> Tuple[Optional[str], float]:
    """Which extraction rule matched this field (from the existing audit trail)."""
    for entry in extracted.get("audit_trail") or []:
        if entry.get("canonical") == field_key:
            return entry.get("method"), float(entry.get("confidence") or 0.0)
    return None, 0.0


def _rule_id(field_key: str, extracted: Dict[str, Any]) -> Optional[str]:
    method, _ = _audit_method(extracted, field_key)
    if field_key in ANCHOR_FIELDS:
        return f"anchors:parse_{field_key}"
    if method:
        return f"field_bank:{method}"
    return None


def _source_evidence(
    field_key: str,
    si_value: Any,
    bl_value: Any,
    si_text: str,
    bl_text: str,
    names: Dict[str, str],
) -> Optional[Dict[str, Any]]:
    """Reuse the DCSA evidence builder so receipts quote the same span as reviews."""
    record = field_evidence.build_field_evidence(
        field_key, si_value, bl_value, si_text, bl_text, names.get("si", "SI"), names.get("bl", "BL")
    )
    for source in record["sources"]:
        if source.get("found_in_document"):
            return {
                "document": source["document"],
                "document_type": source["document_type"],
                "value": source["value"],
                "char_offset": source["char_offset"],
                "exact_text": source["exact_text"],
                "line_number": source["line_number"],
                # Text-extracted documents carry line offsets, not page numbers.
                "page": None,
                "page_note": "text extraction: page not tracked, line_number provided instead",
            }
    return None


def _validators(field_key: str, value: Any, source_text: str, evidence: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    validators: List[Dict[str, str]] = []
    validators.append({
        "name": "source_match",
        "status": "pass" if evidence else "fail",
        "detail": (f"{evidence['document']}#{evidence['char_offset']}" if evidence
                   else "value not located in the source document"),
    })
    wl = field_evidence.check_whitelist(field_key, value, source_text)
    validators.append({
        "name": "whitelist",
        "status": "pass" if wl.get("status") in ("pass", "n/a") else "fail",
        "detail": f"{wl.get('table') or 'no code list'}: {wl.get('details')}",
    })
    mapping = dcsa_mapping.mapping_for(field_key)
    validators.append({
        "name": "dcsa_mapping",
        "status": "pass" if (mapping.get("dcsa_field") or mapping.get("internal_only")) else "fail",
        "detail": mapping.get("dcsa_field") or "internal-only field",
    })
    return validators


def ai_fallback(
    field_keys: List[str],
    doc_text: str,
    doc_key: str,
    shipment_id: str,
    email_id: Optional[str] = None,
    document: str = "BL",
    breaker: Optional[CircuitBreaker] = None,
    scan_notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Run the AI agent for the fields the rule engine could not resolve.

    Stops as soon as the circuit breaker trips (no further guesses), and returns
    the attempts, the validator outcomes and any refusal certificate.
    """
    breaker = breaker or circuit_breaker
    attempts: List[Dict[str, Any]] = []
    blocked: List[str] = []

    for field_key in field_keys:
        if breaker.is_tripped(doc_key):
            # Refuse to keep guessing on this document.
            blocked.append(field_key)
            continue

        proposal = ai_agent.assist_field(field_key, doc_text, raw_label=None, document=document)
        validators = ai_agent.validate_proposal(field_key, proposal, doc_text)
        state = breaker.record(doc_key, field_key, proposal.get("attempted_value"), validators)

        attempts.append({
            **proposal,
            "validators": validators,
            "accepted": all(v["status"] == "pass" for v in validators),
            "consecutive_ai_failures_after": state["consecutive_ai_failures"],
        })

    certificate = None
    if breaker.is_tripped(doc_key):
        certificate = breaker.build_certificate(
            doc_key=doc_key,
            shipment_id=shipment_id,
            email_id=email_id,
            missing_or_unclear=field_keys,
            extra_context={"scan_notes": scan_notes or []} if scan_notes else None,
        )

    return {
        "doc_key": doc_key,
        "attempts": attempts,
        "blocked_by_circuit_breaker": blocked,
        "circuit_breaker": breaker.state(doc_key),
        "refusal_certificate": certificate,
    }


def build_events(
    email_id: str,
    verification: Optional[Dict[str, Any]],
    si_text: str = "",
    bl_text: str = "",
    names: Optional[Dict[str, str]] = None,
    overrides: Optional[Dict[str, Any]] = None,
    ai_attempts: Optional[List[Dict[str, Any]]] = None,
    timestamp: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """One receipt row per compared field, observed from the existing pipeline."""
    names = names or {"si": "SI", "bl": "BL"}
    ai_attempts = ai_attempts or []
    ts = timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat()

    si_extracted = _extracted(verification, "si")
    bl_extracted = _extracted(verification, "bl")
    matrix = {row.get("field_key"): row
              for row in (verification or {}).get("field_matrix") or []}

    override_fields = set()
    override_payload = overrides or {}
    for key in ("si_overrides", "bl_overrides"):
        override_fields.update((override_payload.get(key) or {}).keys())
    for correction in override_payload.get("corrections") or []:
        if correction.get("field"):
            override_fields.add(correction["field"])

    ai_by_field = {a["field_key"]: a for a in ai_attempts}

    rule_resolved = {
        f for f, row in matrix.items()
        if _rule_id(f, bl_extracted) and f not in ai_by_field and f not in override_fields
    }

    events: List[Dict[str, Any]] = []
    for field_key in comparator.FIELDS:
        row = matrix.get(field_key) or {}
        si_value = row.get("si_value", si_extracted.get(field_key))
        bl_value = row.get("bl_value", bl_extracted.get(field_key))
        attempt = ai_by_field.get(field_key)

        if field_key in override_fields:
            path, decided_by = "human", "human_reviewer"
        elif attempt:
            path, decided_by = "ai", "ai_agent"
        else:
            path, decided_by = "rule", "rule_engine"

        evidence = _source_evidence(field_key, si_value, bl_value, si_text, bl_text, names)
        validators = _validators(field_key, bl_value, bl_text or si_text, evidence)
        if attempt:
            # AI-origin validators come from the agent's own provenance checks.
            validators = attempt["validators"]

        events.append({
            "event_id": f"{email_id}:{field_key}:{path}",
            "timestamp": ts,
            "email_id": email_id,
            "field_name": field_key,
            "dcsa_field": dcsa_mapping.dcsa_field_name(field_key),
            "decision_path": path,
            "rule_matched": None if path != "rule" else _rule_id(field_key, bl_extracted),
            "ai_fields_read": (["raw_label:unresolved", "document_window:BL"] if path == "ai" else []),
            "ai_fields_skipped": sorted(rule_resolved) if path == "ai" else [],
            "source_evidence": evidence,
            "validators": validators,
            "final_decision_by": decided_by,
            "value": None if bl_value is None else str(bl_value),
            "agreement": "match" if row.get("is_match") else "conflict",
            "token_cost": attempt.get("token_cost") if attempt else None,
            "latency_ms": attempt.get("latency_ms") if attempt else None,
            "ai_provider": attempt.get("provider") if attempt else None,
        })
    return events


def summarize(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate a receipt: rules vs AI vs human, and real token/latency totals."""
    rules = [e for e in events if e["decision_path"] == "rule"]
    ai = [e for e in events if e["decision_path"] == "ai"]
    human = [e for e in events if e["decision_path"] == "human"]

    tokens = [e["token_cost"] for e in ai if e.get("token_cost") is not None]
    latencies = [e["latency_ms"] for e in ai if e.get("latency_ms") is not None]
    provider = provider_status()

    vpass = sum(1 for e in events for v in (e.get("validators") or []) if v["status"] == "pass")
    vfail = sum(1 for e in events for v in (e.get("validators") or []) if v["status"] == "fail")

    total_tokens = sum(tokens)
    total_latency = sum(latencies)
    note = (
        "Tokens reported by the configured LLM provider."
        if tokens else
        "No LLM provider configured: the AI path used the deterministic local assistant, "
        "so no token cost is claimed."
    )

    return {
        "total_fields": len(events),
        "resolved_by_rules": len(rules),
        "resolved_by_ai": len(ai),
        "resolved_by_human": len(human),
        "total_ai_calls": len(ai),
        "total_tokens": total_tokens,
        "total_latency_ms": total_latency,
        "tokens_reported": bool(tokens),
        "tokens_note": note,
        "provider": provider,
        "validators": {"passed": vpass, "failed": vfail},
        "summary_line": (
            f"{len(rules)} fields resolved by rules, {len(ai)} by AI, {len(human)} by human "
            f"- {total_tokens} tokens spent, {total_latency}ms total AI latency."
        ),
    }


def _unresolved_fields(verification: Optional[Dict[str, Any]]) -> List[str]:
    """Fields the rule engine left empty *on the document under review* (the BL).

    These - and only these - are handed to the AI agent.
    """
    bl_extracted = _extracted(verification, "bl")
    return [f for f in comparator.FIELDS if bl_extracted.get(f) in (None, "")]


def build_receipt(
    shipment_id: str,
    documents: List[Dict[str, Any]],
    overrides_by_email: Optional[Dict[str, Dict[str, Any]]] = None,
    breaker: Optional[CircuitBreaker] = None,
    persist: bool = True,
) -> Dict[str, Any]:
    """Full shipment receipt: observe the pipeline, then run the AI fallback.

    ``documents`` items: ``{email_id, si_text, bl_text, names, email, scan_notes}``.
    """
    overrides_by_email = overrides_by_email or {}
    breaker = breaker or circuit_breaker

    all_events: List[Dict[str, Any]] = []
    per_document: List[Dict[str, Any]] = []
    certificate: Optional[Dict[str, Any]] = None

    for doc in documents:
        email_id = doc["email_id"]
        si_text = doc.get("si_text") or ""
        bl_text = doc.get("bl_text") or ""
        names = doc.get("names") or {"si": "SI", "bl": "BL"}
        overrides = overrides_by_email.get(email_id)

        # Existing pipeline, unchanged.
        verification = comparator.compare_documents(
            si_text, bl_text, overrides=overrides, email_metadata=doc.get("email")
        )

        doc_key = f"{shipment_id}:{email_id}"
        unresolved = _unresolved_fields(verification)
        scan_notes = list(doc.get("scan_notes") or [])
        lowered = (bl_text or si_text or "").lower()
        if any(marker in lowered for marker in ("[unreadable", "[read_error", "damaged text", "ocr_corrupted")):
            scan_notes.append("document text carries unreadable / low scan-quality markers")
        fallback = ai_fallback(
            unresolved, bl_text or si_text, doc_key, shipment_id, email_id,
            breaker=breaker, scan_notes=scan_notes,
        )
        if fallback.get("refusal_certificate"):
            certificate = fallback["refusal_certificate"]

        events = build_events(
            email_id, verification, si_text, bl_text, names,
            overrides=overrides, ai_attempts=fallback["attempts"],
        )
        for event in events:
            event["shipment_id"] = shipment_id
        all_events.extend(events)

        if persist:
            for event in events:
                _persist(event)

        per_document.append({
            "email_id": email_id,
            "status": verification.get("status"),
            "review_reason": verification.get("review_reason"),
            "document_validity": verification.get("document_validity"),
            "unresolved_fields": unresolved,
            "ai_attempts": fallback["attempts"],
            "blocked_by_circuit_breaker": fallback["blocked_by_circuit_breaker"],
            "events": events,
            "summary": summarize(events),
        })

    summary = summarize(all_events)
    return {
        "shipment_id": shipment_id,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "documents": per_document,
        "fields": all_events,
        "summary": summary,
        "circuit_breaker": breaker.state(f"{shipment_id}:{documents[0]['email_id']}") if documents else None,
        "refusal_certificate": certificate,
    }


def _persist(event: Dict[str, Any]) -> None:
    """Best-effort persistence into DuckDB (never breaks the request path)."""
    try:
        from backend.services.event_logger import event_logger

        event_logger.log_field_decision(event)
    except Exception as ex:  # pragma: no cover - degraded mode
        print(f"[ReasoningReceipt] Could not persist field decision: {ex}")
