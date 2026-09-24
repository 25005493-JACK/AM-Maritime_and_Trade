"""
DocuMatch LLM Agent Layer.
Provides schema-validated AI assistance governed by strict provenance,
UN/LOCODE/ISO 6346 validation, circuit-breaker tripping, and safety guardrails.
"""
import os
import json
from typing import Dict, Any, Optional, List

from backend.services.llm_agent.client import get_llm_client, LLMClient
from backend.services.llm_agent.schemas import (
    ClassificationResult,
    FieldExtractionResult,
    ExtractedFieldEvidence,
    ScanReadResult,
    MismatchExplanation,
    DraftReply,
)
from backend.services.field_evidence import locate_span, check_whitelist
from backend.services.circuit_breaker import circuit_breaker

REQUIRED_FIELDS = [
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg",
]

CONFIDENCE_THRESHOLD = float(os.environ.get("DOCUMATCH_LLM_CONFIDENCE_THRESHOLD", "0.85"))

class DocuMatchLLMAgent:
    def __init__(self, client: Optional[LLMClient] = None):
        self._client = client

    @property
    def client(self) -> LLMClient:
        if self._client is not None:
            return self._client
        return get_llm_client()

    def is_enabled(self) -> bool:
        return self.client.is_enabled()

    def classify_email(
        self,
        email: Dict[str, Any],
        rule_confidence: float = 1.0,
        threshold: float = CONFIDENCE_THRESHOLD,
    ) -> Optional[ClassificationResult]:
        """Classify email ONLY when rule confidence is below threshold."""
        if not self.is_enabled() or rule_confidence >= threshold:
            return None

        system_prompt = (
            "You are an expert maritime document intake classifier. "
            "Classify the email into one of: BL_COMPARISON, SI_REQUEST, INVOICE_QUERY, GENERAL, SPAM. "
            "Output JSON conforming to schema: {category: str, confidence: float, reasoning: str}."
        )

        user_prompt = (
            f"Email ID: {email.get('id')}\n"
            f"Subject: {email.get('subject')}\n"
            f"Sender: {email.get('sender')}\n"
            f"Body:\n{email.get('body')}\n"
            f"Attachments: {[a.get('filename') if isinstance(a, dict) else str(a) for a in email.get('attachments', [])]}"
        )

        raw = self.client.generate_json(system_prompt, user_prompt)
        if not raw:
            return None

        try:
            return ClassificationResult.model_validate(raw)
        except Exception as ex:
            print(f"[LLM Agent] Classification validation error: {ex}")
            return None

    def extract_missing_fields(
        self,
        doc_text: str,
        doc_type: str,
        existing_fields: Dict[str, Any],
        doc_key: str = "doc_key",
    ) -> Dict[str, Dict[str, Any]]:
        """Extract ONLY fields that are null or unrecognized in existing_fields.
        
        Strict safety:
        - Rejects any candidate that fails Phase 2 strict provenance (must be verbatim in source).
        - Rejects any port failing UN/LOCODE or container failing ISO 6346 check.
        - Failures are recorded into the circuit breaker counter.
        - NEVER overrides an existing valid value.
        """
        if not self.is_enabled() or not doc_text.strip():
            return {}

        # Determine missing/null fields
        missing = [
            f for f in REQUIRED_FIELDS
            if existing_fields.get(f) in (None, "", "(none)")
        ]
        if not missing:
            return {}

        system_prompt = (
            f"You are a strict maritime document data extractor for {doc_type} documents. "
            f"Extract ONLY the requested missing fields: {missing}. "
            "CRITICAL: For each extracted field, provide the exact verbatim quote substring from the text in evidence_quote. "
            "If a field is not present in the text, do NOT guess; omit it. "
            "Output JSON conforming to schema: {fields: {field_name: {value: str, evidence_quote: str, confidence: float}}}."
        )

        user_prompt = f"Document Text:\n{doc_text}"

        raw = self.client.generate_json(system_prompt, user_prompt)
        if not raw:
            return {}

        try:
            parsed = FieldExtractionResult.model_validate(raw)
        except Exception as ex:
            print(f"[LLM Agent] Field extraction schema validation error: {ex}")
            return {}

        accepted: Dict[str, Dict[str, Any]] = {}

        for field_name, evidence in parsed.fields.items():
            if field_name not in missing:
                continue

            val = evidence.value.strip() if evidence.value else ""
            if not val:
                continue

            # 1. Strict Provenance Check: full normalized value must exist in source text
            span = locate_span(doc_text, val, allow_partial=False)
            if not span and evidence.evidence_quote:
                # Fallback check on evidence_quote
                span = locate_span(doc_text, evidence.evidence_quote, allow_partial=False)

            validators = []
            if not span:
                validators.append({
                    "name": "source_match",
                    "status": "fail",
                    "detail": f"Strict provenance failed: '{val}' not grounded in source text"
                })
                circuit_breaker.record(doc_key, field_name, val, validators)
                continue
            else:
                validators.append({
                    "name": "source_match",
                    "status": "pass",
                    "detail": f"Strict provenance verified at char {span['start_char']}-{span['end_char']}"
                })

            # 2. Whitelist Check (UN/LOCODE / ISO 6346)
            wl = check_whitelist(field_name, val, raw_text=doc_text)
            if wl.get("status") == "fail":
                validators.append({
                    "name": "whitelist",
                    "status": "fail",
                    "detail": wl.get("details", "Whitelist check failed")
                })
                circuit_breaker.record(doc_key, field_name, val, validators)
                continue
            elif wl.get("status") == "pass":
                validators.append({
                    "name": "whitelist",
                    "status": "pass",
                    "detail": wl.get("details", "Whitelist validated")
                })

            # Record success in circuit breaker
            circuit_breaker.record(doc_key, field_name, val, validators)

            accepted[field_name] = {
                "value": wl.get("resolved_code") or val,
                "evidence_quote": evidence.evidence_quote,
                "confidence": evidence.confidence,
                "span": span,
                "source": "ai",
                "validators": validators,
            }

        return accepted

    def read_scan(self, raw_input: Any) -> ScanReadResult:
        """Vision pre-read for image-only PDFs.
        
        Output is marked 'unverified' and document still routes to NEEDS_REVIEW.
        """
        if not self.is_enabled():
            return ScanReadResult(
                raw_text="",
                is_scanned=True,
                confidence=0.0,
                status="unverified",
                notes="LLM mode off; unverified scan requiring manual review"
            )

        system_prompt = (
            "You are a vision document transcriber. Transcribe text visible in this scanned document. "
            "Output JSON: {raw_text: str, is_scanned: bool, confidence: float, status: 'unverified', notes: str}."
        )
        user_prompt = f"Scanned document input reference: {str(raw_input)[:200]}"
        raw = self.client.generate_json(system_prompt, user_prompt)
        if raw:
            try:
                res = ScanReadResult.model_validate(raw)
                res.status = "unverified"
                return res
            except Exception:
                pass

        return ScanReadResult(
            raw_text="",
            is_scanned=True,
            confidence=0.5,
            status="unverified",
            notes="Visual OCR pre-read; marked unverified"
        )

    def explain_mismatch(self, verification_data: Dict[str, Any]) -> Optional[MismatchExplanation]:
        """Advisory explanation of discrepancy causes."""
        if not self.is_enabled():
            return None

        system_prompt = (
            "You are an advisory maritime discrepancies auditor. "
            "Explain the discrepancies between SI and Draft BL concisely. "
            "Output JSON: {explanation: str, risk_level: str, key_discrepancies: [str]}."
        )
        user_prompt = f"Verification Matrix:\n{json.dumps(verification_data.get('field_matrix', []), indent=2)}"
        raw = self.client.generate_json(system_prompt, user_prompt)
        if not raw:
            return None
        try:
            return MismatchExplanation.model_validate(raw)
        except Exception:
            return None

    def draft_reply(self, email: Dict[str, Any], verification_data: Dict[str, Any]) -> Optional[DraftReply]:
        """Advisory draft email reply to carrier/shipper."""
        if not self.is_enabled():
            return None

        system_prompt = (
            "You are a maritime operations assistant drafting a clarification email to the carrier or shipper. "
            "Output JSON: {subject: str, recipient: str, body: str}."
        )
        user_prompt = (
            f"Email: {email.get('id')}, Sender: {email.get('sender')}, Subject: {email.get('subject')}\n"
            f"Discrepancies: {verification_data.get('status')}, Details: {verification_data.get('message')}"
        )
        raw = self.client.generate_json(system_prompt, user_prompt)
        if not raw:
            return None
        try:
            return DraftReply.model_validate(raw)
        except Exception:
            return None

llm_agent = DocuMatchLLMAgent()
