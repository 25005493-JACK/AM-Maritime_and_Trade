"""
Specialized tasks for DocuMatch LLM Agent Layer.

Rules First Principles:
1. classify_email: Only invoked when rule confidence is below threshold (0.90).
2. extract_fields: Only invoked for fields that are null or unmapped in rule extraction.
3. Provenance & code-list validation: Every extracted field is tested for verbatim
   provenance in the source document, plus UN/LOCODE (ports) and ISO 6346 (containers).
4. Circuit Breaker: Validation failures increment the per-document circuit breaker.
5. Invariants: The LLM NEVER overrides a valid rule-extracted value and NEVER produces
   an OK verdict. Only deterministic comparator code decides OK / MISMATCH / NEEDS_REVIEW.
6. Advisory text: explain_mismatch and draft_reply are purely advisory.
"""
from typing import Any, Dict, List, Optional, Tuple
from pydantic import ValidationError

from llm_agent.client import llm_client, LLMDisabledError
from llm_agent.schemas import (
    ClassificationOutput,
    ExtractFieldsOutput,
    FieldExtraction,
    ScanReadOutput,
    MismatchExplanation,
    DraftReply,
)
from llm_agent.validators import (
    check_verbatim_provenance,
    validate_unlocode,
    validate_iso6346,
)
from backend.services.circuit_breaker import circuit_breaker


CONFIDENCE_THRESHOLD = 0.90


def classify_email(
    email: Dict[str, Any],
    rule_category: str,
    rule_confidence: float,
    sender_domain: Optional[str] = None,
    memory_enabled: bool = True,
) -> Dict[str, Any]:
    """
    Classifies email with LLM ONLY when rule confidence < 0.90.
    If LLM is disabled or rule confidence >= 0.90, the rule verdict is returned directly.
    When memory_enabled=True, relevant reflections from prior reviewer corrections are injected.
    """
    if rule_confidence >= CONFIDENCE_THRESHOLD or not llm_client.is_enabled:
        return {
            "category": rule_category,
            "confidence": rule_confidence,
            "source": "rules",
            "reasoning": "Rule confidence met or exceeded threshold (0.90) or LLM is off.",
        }

    # Extract sender domain and reflections if memory is enabled
    domain = sender_domain
    if not domain:
        s = email.get("sender") or email.get("from") or ""
        if "@" in str(s):
            domain = str(s).split("@")[-1].lower().strip().strip(">\"' ")

    lessons_header = ""
    if memory_enabled and domain and domain != "unknown":
        try:
            from backend.services.reflection import retrieve_reflections
            refs = retrieve_reflections(domain, doc_type="EMAIL", limit=2)
            if refs:
                lessons_text = "\n".join(f"- {r.get('reflection_text')}" for r in refs if r.get('reflection_text'))
                if lessons_text:
                    lessons_header = f"Lessons from past reviewer corrections for this sender:\n{lessons_text}\n\n"
        except Exception:
            pass

    prompt = (
        f"{lessons_header}"
        f"Classify the following shipping email into one of these exact categories: "
        f"BL_COMPARISON, SI_REQUEST, INVOICE_QUERY, GENERAL, SPAM.\n\n"
        f"Subject: {email.get('subject', '')}\n"
        f"Sender: {email.get('sender', email.get('from', ''))}\n"
        f"Body Preview:\n{email.get('body', '')[:1000]}\n"
        f"Attachment Count: {len(email.get('attachments', []))}\n"
        f"Rule Engine tentative category was: {rule_category} (confidence: {rule_confidence:.2f})"
    )

    try:
        output: ClassificationOutput = llm_client.generate_json(prompt, ClassificationOutput)
        return {
            "category": output.category,
            "confidence": output.confidence,
            "source": "ai",
            "reasoning": output.reasoning,
        }
    except Exception as ex:
        # Fallback safely to rule engine on any error
        return {
            "category": rule_category,
            "confidence": rule_confidence,
            "source": "rules",
            "reasoning": f"LLM classification bypassed/fallback due to: {ex}",
        }


def extract_fields(
    unmapped_fields: List[str],
    doc_text: str,
    doc_key: str,
    doc_type: str = "BL",
    sender_domain: Optional[str] = None,
    memory_enabled: bool = True,
) -> Dict[str, Any]:
    """
    Extracts values ONLY for fields that are null or unmapped.
    Every extraction MUST provide verbatim evidence quotes.
    Runs Phase 2 strict provenance, UN/LOCODE, and ISO 6346 validators.
    Failures increment the per-document circuit breaker.
    When memory_enabled=True:
      - Uses Bayesian trust posterior to gate low-trust senders straight to human review.
      - Injects relevant reflections from prior reviewer corrections into prompt.
    """
    if not unmapped_fields or not doc_text or not llm_client.is_enabled:
        return {
            "proposals": {},
            "receipt_entries": [],
            "circuit_breaker": circuit_breaker.state(doc_key),
        }

    if circuit_breaker.is_tripped(doc_key):
        return {
            "proposals": {},
            "receipt_entries": [],
            "circuit_breaker": circuit_breaker.state(doc_key),
            "refusal": circuit_breaker.certificate(doc_key),
        }

    # 1. Trust-based review gating (Thompson Sampling)
    policy_res = None
    if memory_enabled and sender_domain and sender_domain != "unknown":
        try:
            from backend.services.routing_policy import sample_trust
            policy_res = sample_trust(sender_domain)
            if policy_res and not policy_res.get("route_to_ai", True):
                # Trust is below threshold: gate straight to Human Review Queue
                return {
                    "proposals": {},
                    "receipt_entries": [],
                    "circuit_breaker": circuit_breaker.state(doc_key),
                    "routed_to_human_by_policy": True,
                    "policy_routing": policy_res,
                }
        except Exception:
            pass

    # 2. Retrieve relevant reflections for this sender
    lessons_header = ""
    if memory_enabled and sender_domain and sender_domain != "unknown":
        try:
            from backend.services.reflection import retrieve_reflections
            refs = retrieve_reflections(sender_domain, doc_type=doc_type, limit=3)
            if refs:
                lessons_text = "\n".join(f"- {r.get('reflection_text')}" for r in refs if r.get('reflection_text'))
                if lessons_text:
                    lessons_header = f"Lessons from past reviewer corrections for this sender:\n{lessons_text}\n\n"
        except Exception:
            pass

    # Bounded document window for token efficiency
    window = "\n".join(doc_text.splitlines()[:60])
    prompt = (
        f"{lessons_header}"
        f"You are extracting missing fields from a {doc_type} shipping document.\n"
        f"Only extract these target fields: {unmapped_fields}\n"
        f"For each field found, return the exact verbatim 'value' and 'evidence_quote' from the text, "
        f"plus your confidence (0.0 to 1.0).\n"
        f"Document text snippet:\n{window}\n"
    )

    try:
        output: ExtractFieldsOutput = llm_client.generate_json(prompt, ExtractFieldsOutput)
    except Exception as ex:
        return {
            "proposals": {},
            "receipt_entries": [],
            "circuit_breaker": circuit_breaker.state(doc_key),
            "error": str(ex),
        }

    proposals: Dict[str, Any] = {}
    receipt_entries: List[Dict[str, Any]] = []

    for field_name in unmapped_fields:
        if circuit_breaker.is_tripped(doc_key):
            break

        extraction = output.fields.get(field_name)
        if not extraction or not extraction.value.strip():
            continue

        val = extraction.value.strip()
        quote = extraction.evidence_quote.strip()

        # Run strict validation suite
        validators: List[Dict[str, str]] = []

        # 1. Verbatim quote provenance check
        quote_valid = check_verbatim_provenance(quote, doc_text)
        validators.append({
            "name": "strict_quote_provenance",
            "status": "pass" if quote_valid else "fail",
            "detail": "Verbatim quote matched in document text" if quote_valid else "Quote could not be located verbatim in source",
        })

        # 2. Verbatim value in document or quote
        val_in_quote = (val.lower() in quote.lower()) or (val.lower() in doc_text.lower())
        validators.append({
            "name": "verbatim_value_provenance",
            "status": "pass" if val_in_quote else "fail",
            "detail": "Value located in quote or document" if val_in_quote else "Value not found verbatim",
        })

        # 3. Domain specific validators: UN/LOCODE
        if field_name in ("port_of_loading", "port_of_discharge"):
            locode_ok, norm_locode = validate_unlocode(val)
            validators.append({
                "name": "unlocode_validator",
                "status": "pass" if locode_ok else "fail",
                "detail": f"UN/LOCODE resolved: {norm_locode}" if locode_ok else "Failed UN/LOCODE port directory match",
            })
            if locode_ok and norm_locode:
                val = norm_locode

        # 4. Domain specific validators: ISO 6346 (containers)
        if field_name == "container_count":
            iso_ok, norm_iso = validate_iso6346(val)
            validators.append({
                "name": "iso6346_validator",
                "status": "pass" if iso_ok else "fail",
                "detail": f"ISO 6346 check passed: {norm_iso}" if iso_ok else "Failed ISO 6346 check digit / unit tally format",
            })
            if iso_ok and norm_iso:
                val = norm_iso

        # Record to Circuit Breaker
        cb_state = circuit_breaker.record(doc_key, field_name, val, validators)
        is_accepted = all(v["status"] == "pass" for v in validators)

        receipt_entry = {
            "field_name": field_name,
            "source": "ai",
            "attempted_value": val,
            "evidence_quote": quote,
            "confidence": extraction.confidence,
            "validators": validators,
            "accepted": is_accepted,
            "consecutive_failures": cb_state["consecutive_ai_failures"],
            "circuit_breaker_tripped": cb_state["tripped"],
        }
        receipt_entries.append(receipt_entry)

        if is_accepted:
            proposals[field_name] = {
                "value": val,
                "confidence": extraction.confidence,
                "evidence_quote": quote,
            }

    return {
        "proposals": proposals,
        "receipt_entries": receipt_entries,
        "circuit_breaker": circuit_breaker.state(doc_key),
    }


def read_scan(
    image_metadata: Dict[str, Any],
    ocr_raw_text: str = "",
) -> ScanReadOutput:
    """
    Vision pre-read for image-only or low-fidelity scanned documents.
    IMPORTANT: Output is marked 'unverified' and strictly routes to NEEDS_REVIEW.
    Never produces an OK or auto-approved status.
    """
    if not llm_client.is_enabled:
        return ScanReadOutput(
            extracted_text=ocr_raw_text,
            confidence=0.5,
            is_image_scan=True,
            verification_status="unverified",
            notes="LLM agent layer disabled; routed to NEEDS_REVIEW as unverified scan.",
        )

    prompt = (
        f"Perform a vision/OCR pre-read interpretation of this scanned shipping document.\n"
        f"Image info: {image_metadata}\n"
        f"Raw OCR buffer:\n{ocr_raw_text[:2000]}\n"
        f"Transcribe and structure the legible text. Note any illegible sections."
    )

    try:
        output: ScanReadOutput = llm_client.generate_json(prompt, ScanReadOutput)
        # Enforce invariant: must be marked unverified
        return ScanReadOutput(
            extracted_text=output.extracted_text,
            confidence=output.confidence,
            is_image_scan=True,
            verification_status="unverified",
            notes=f"Vision pre-read completed. Human review mandatory. Notes: {output.notes}",
        )
    except Exception as ex:
        return ScanReadOutput(
            extracted_text=ocr_raw_text,
            confidence=0.3,
            is_image_scan=True,
            verification_status="unverified",
            notes=f"Vision read fallback: {ex}",
        )


def explain_mismatch(
    field_name: str,
    si_value: Any,
    bl_value: Any,
) -> MismatchExplanation:
    """Advisory-only discrepancy explanation."""
    if not llm_client.is_enabled:
        return MismatchExplanation(
            field_name=field_name,
            summary=f"Discrepancy detected between SI ('{si_value}') and BL ('{bl_value}').",
            recommended_action="Review both documents and request amendment if needed.",
            advisory=True,
        )

    prompt = (
        f"Explain the maritime shipping mismatch for field '{field_name}':\n"
        f"Shipping Instruction (SI) value: {si_value}\n"
        f"Bill of Lading (BL) value: {bl_value}\n"
        f"Provide a clear, 1-2 sentence maritime operations summary and recommended action."
    )

    try:
        output: MismatchExplanation = llm_client.generate_json(prompt, MismatchExplanation)
        return output
    except Exception:
        return MismatchExplanation(
            field_name=field_name,
            summary=f"SI states '{si_value}' while BL states '{bl_value}'.",
            recommended_action="Confirm party details with freight forwarder or carrier.",
            advisory=True,
        )


def draft_reply(
    email: Dict[str, Any],
    discrepancies: List[Dict[str, Any]],
) -> DraftReply:
    """Advisory-only draft clarification email for carrier or shipper."""
    sender = email.get("sender", email.get("from", "counterparty@shipping.com"))
    subject = f"Re: {email.get('subject', 'Shipping Document Verification')}"

    if not llm_client.is_enabled:
        disc_bullets = "\n".join(f"- {d.get('field')}: SI='{d.get('si')}', BL='{d.get('bl')}'" for d in discrepancies)
        body = (
            f"Dear Partner,\n\n"
            f"During automated document verification, we identified the following discrepancies:\n"
            f"{disc_bullets}\n\n"
            f"Please review and advise on the correct information.\n\n"
            f"Best regards,\nDocumentation Operations Team"
        )
        return DraftReply(recipient=sender, subject=subject, body=body, advisory=True)

    prompt = (
        f"Draft a polite, professional maritime ops clarification email to {sender}.\n"
        f"Subject: {subject}\n"
        f"Discrepancies found:\n{discrepancies}\n"
    )

    try:
        output: DraftReply = llm_client.generate_json(prompt, DraftReply)
        return output
    except Exception:
        disc_bullets = "\n".join(f"- {d.get('field')}: SI='{d.get('si')}', BL='{d.get('bl')}'" for d in discrepancies)
        return DraftReply(
            recipient=sender,
            subject=subject,
            body=f"Dear Partner,\n\nPlease clarify discrepancies:\n{disc_bullets}\n\nRegards,\nOps Team",
            advisory=True,
        )
