"""
Circuit breaker + refusal certificate.

When the AI agent repeatedly fails validation on the same document it must stop
and hand over a structured, actionable refusal instead of continuing to guess.

The counter is per document: it increments on every AI-extracted field that fails
a validator (source_match / whitelist / dcsa_mapping) and resets to zero on any
pass. Once `consecutive_ai_failures >= threshold` (default 3, configurable via
AVERISH_CIRCUIT_BREAKER_THRESHOLD) AI processing for that document stops and a
refusal certificate is produced.
"""
import os
import threading
import datetime
from typing import Any, Dict, List, Optional

DEFAULT_THRESHOLD = int(os.environ.get("AVERISH_CIRCUIT_BREAKER_THRESHOLD", "3"))

#: How the "who should fix this" hint is derived (first match wins).
RECIPIENT_RULES = [
    ("carrier", {"container_count", "vessel_voyage", "port_of_loading",
                 "port_of_discharge", "bl_reference", "carrier_reference"}),
    ("shipper", {"shipper", "consignee", "notify_party", "hs_code",
                 "description_of_goods", "gross_weight_kg"}),
]

#: Documented, configurable assumption used for the delay estimate only
#: (a manual query to the counterparty typically costs half a working day).
MANUAL_QUERY_MINUTES = int(os.environ.get("AVERISH_MANUAL_QUERY_MINUTES", "240"))


def suggest_recipient(missing_fields: List[str]) -> Dict[str, str]:
    """Infer who can actually resolve the missing/unclear fields."""
    fields = {f for f in (missing_fields or []) if f}
    for recipient, bucket in RECIPIENT_RULES:
        overlap = fields & bucket
        if overlap:
            if recipient == "carrier":
                rationale = (f"Missing/unclear fields ({', '.join(sorted(overlap))}) are "
                             "shipment/carrier-side data, so the carrier is the fastest source.")
            else:
                rationale = (f"Missing/unclear fields ({', '.join(sorted(overlap))}) are party/"
                             "commercial data provided by the shipper.")
            return {"recipient": recipient, "rationale": rationale}
    return {
        "recipient": "internal_ops",
        "rationale": "No counterparty-specific pattern detected; route to internal operations for triage.",
    }


class CircuitBreaker:
    """Per-document consecutive AI failure counter."""

    def __init__(self, threshold: Optional[int] = None):
        self.threshold = threshold or DEFAULT_THRESHOLD
        self._lock = threading.Lock()
        self._state: Dict[str, Dict[str, Any]] = {}

    def _entry(self, doc_key: str) -> Dict[str, Any]:
        return self._state.setdefault(doc_key, {
            "doc_key": doc_key,
            "consecutive_ai_failures": 0,
            "total_ai_fields": 0,
            "total_ai_failures": 0,
            "tripped": False,
            "failed_fields": [],
            "certificate": None,
        })

    def state(self, doc_key: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._entry(doc_key))

    def reset(self, doc_key: Optional[str] = None) -> None:
        with self._lock:
            if doc_key is None:
                self._state.clear()
            else:
                self._state.pop(doc_key, None)

    def is_tripped(self, doc_key: str) -> bool:
        with self._lock:
            return bool(self._entry(doc_key)["tripped"])

    def record(
        self,
        doc_key: str,
        field_key: str,
        attempted_value: Any,
        validators: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Record one AI field attempt. Returns the state after recording."""
        failures = [v for v in validators if v.get("status") == "fail"]
        with self._lock:
            entry = self._entry(doc_key)
            entry["total_ai_fields"] += 1
            if failures:
                entry["consecutive_ai_failures"] += 1
                entry["total_ai_failures"] += 1
                entry["failed_fields"].append({
                    "field_name": field_key,
                    "attempted_value": attempted_value,
                    "why_failed": "; ".join(
                        f"{v['name']}: {v.get('detail', 'failed')}" for v in failures
                    ),
                })
            else:
                entry["consecutive_ai_failures"] = 0
            if entry["consecutive_ai_failures"] >= self.threshold:
                entry["tripped"] = True
            return dict(entry)

    def build_certificate(
        self,
        doc_key: str,
        shipment_id: str,
        email_id: Optional[str] = None,
        missing_or_unclear: Optional[List[str]] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Structured, actionable refusal for a document that tripped the breaker."""
        with self._lock:
            entry = dict(self._entry(doc_key))
            failed_fields = list(entry["failed_fields"])
            consecutive = entry["consecutive_ai_failures"]

        unresolved = sorted({
            *(f["field_name"] for f in failed_fields),
            *(missing_or_unclear or []),
        })
        recipient = suggest_recipient(unresolved)
        delay_minutes = MANUAL_QUERY_MINUTES * max(len(unresolved), 1)

        certificate = {
            "certificate_type": "ai_refusal",
            "doc_key": doc_key,
            "shipment_id": shipment_id,
            "email_id": email_id,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "reason": f"{consecutive} consecutive AI extractions failed validation",
            "threshold": self.threshold,
            "consecutive_ai_failures": consecutive,
            "failed_fields": failed_fields,
            "missing_or_unclear": unresolved + list((extra_context or {}).get("scan_notes", [])),
            "suggested_recipient": recipient["recipient"],
            "recipient_rationale": recipient["rationale"],
            "estimated_delay_minutes": delay_minutes,
            "estimated_delay_hours": round(delay_minutes / 60, 1),
            "estimated_delay_basis": (
                f"{MANUAL_QUERY_MINUTES} min per unresolved field for a manual counterparty query "
                "(documented constant, configurable via AVERISH_MANUAL_QUERY_MINUTES)"
            ),
            "what_would_unblock": [
                "Provide a machine-readable SI/BL (not a scan) so labels can be rule-matched",
                "Confirm the correct values for: "
                + (", ".join(unresolved) if unresolved else "the flagged fields"),
                "Re-send the document using the standard field labels "
                "(shipper, consignee, port of discharge, containers, gross weight)",
            ],
            "notice": (
                "AI processing stopped for this document: no further AI guesses were made. "
                "Every failed attempt and its validator outcome is listed above."
            ),
        }
        if extra_context:
            certificate["context"] = extra_context

        with self._lock:
            self._entry(doc_key)["certificate"] = certificate
        return certificate

    def certificate(self, doc_key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._entry(doc_key).get("certificate")


circuit_breaker = CircuitBreaker()
