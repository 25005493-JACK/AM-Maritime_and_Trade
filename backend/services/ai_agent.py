"""
Evidence-backed AI assist (rules first, AI only for what rules cannot resolve).

Platform principle enforced here:
  * the rule engine runs first and always handles the fields it can match;
  * the agent is invoked ONLY for fields the rule engine could not resolve
    (unmapped labels / empty required fields) - the reasoning receipt records
    exactly which fields the agent saw and which the rules handled, so "AI was
    not used by default" is a verifiable number rather than a claim;
  * every proposal must pass provenance (the value must be locatable verbatim in
    the source document), code-list and DCSA-mapping validation before acceptance
    - failed proposals feed the circuit breaker;
  * token/latency accounting is honest: with no LLM provider configured the local
    deterministic provider is used, `is_llm` is False and `token_cost` is None
    (never a fabricated number).
"""
import os
import re
import time
from typing import Any, Dict, List, Optional

from backend.services import dcsa_mapping, field_evidence

PROVIDER_ENV = "DOCUMATCH_LLM_PROVIDER"
API_KEY_ENV = "DOCUMATCH_LLM_API_KEY"
MODEL_ENV = "DOCUMATCH_LLM_MODEL"

DEFAULT_MODEL = "gpt-4o-mini"
LOCAL_PROVIDER = "local-rules-derived"

#: Synonym glossary used ONLY by the local deterministic assistant (the stand-in
#: for the world knowledge an LLM would bring). The rule dictionary in
#: data/field_terms.json deliberately does not contain these wordings, which is
#: why reworded labels reach the AI path at all.
LOCAL_SYNONYMS: Dict[str, List[str]] = {
    "shipper": ["shipper", "shipper name", "consignor", "sender", "exporter"],
    "consignee": ["consignee", "party receiving cargo", "receiver entity", "receiver", "buyer"],
    "notify_party": ["notify party", "arrival advisory contact", "alert contact", "notify"],
    "port_of_loading": ["port of loading", "embarkation ocean gateway", "origin terminal", "load port", "pol"],
    "port_of_discharge": ["port of discharge", "unloading ocean gateway", "destination hub", "destination", "pod"],
    "container_count": ["container count", "equipment unit tally", "container quantity", "no of containers"],
    "gross_weight_kg": ["gross weight", "cargo mass total", "total weight tonnage", "gross wt"],
}


def provider_status() -> Dict[str, Any]:
    """Which provider would be used right now (and whether it is a real LLM)."""
    name = os.environ.get(PROVIDER_ENV, "").strip().lower()
    api_key = os.environ.get(API_KEY_ENV, "").strip()
    if name in ("openai", "anthropic", "azure-openai") and api_key:
        return {
            "name": name,
            "is_llm": True,
            "model": os.environ.get(MODEL_ENV, DEFAULT_MODEL),
            "credentialed": True,
        }
    return {
        "name": LOCAL_PROVIDER,
        "is_llm": False,
        "model": None,
        "credentialed": False,
        "note": (
            "No LLM provider configured (set "
            f"{PROVIDER_ENV} and {API_KEY_ENV} to enable one); using the deterministic "
            "local assistant, so no token cost is reported."
        ),
    }


class AIAgent:
    """Proposes values for fields the rule engine could not resolve."""

    def __init__(self, provider: Optional[Dict[str, Any]] = None):
        self.provider = provider or provider_status()

    def assist_field(
        self,
        field_key: str,
        doc_text: str,
        raw_label: Optional[str] = None,
        document: str = "SI",
        sender_domain: Optional[str] = None,
        email_id: Optional[str] = None,
        shipment_id: Optional[str] = None,
        retrieved_reflections: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Attempt to resolve one field. Returns a proposal record with evidence."""
        started = time.perf_counter()
        candidates: List[Dict[str, Any]] = []
        token_cost: Optional[int] = None

        reflections = retrieved_reflections
        if reflections is None and sender_domain:
            try:
                from backend.services.reflection import retrieve_reflections
                reflections = retrieve_reflections(
                    sender_domain=sender_domain,
                    doc_type=document,
                    field_name=field_key,
                    email_id=email_id,
                    shipment_id=shipment_id
                )
            except Exception as ex:
                print(f"[AIAgent] Failed to retrieve reflections: {ex}")
                reflections = []

        reflections = reflections or []

        if self.provider.get("is_llm"):
            candidates, token_cost = self._call_llm(
                field_key, doc_text, raw_label, reflections=reflections
            )
        else:
            candidates = self._local_candidates(field_key, doc_text, raw_label)

        latency_ms = int((time.perf_counter() - started) * 1000)
        best = candidates[0] if candidates else None

        return {
            "field_key": field_key,
            "document": document,
            "raw_label": raw_label,
            "attempted_value": best["value"] if best else None,
            "evidence": best,
            "provider": self.provider.get("name"),
            "is_llm": bool(self.provider.get("is_llm")),
            "model": self.provider.get("model"),
            "token_cost": token_cost,
            "latency_ms": latency_ms,
            "candidates_considered": len(candidates),
            "retrieved_reflections": reflections,
        }

    def validate_proposal(
        self,
        field_key: str,
        proposal: Dict[str, Any],
        doc_text: str,
    ) -> List[Dict[str, str]]:
        """Provenance + code-list + DCSA-mapping checks; each entry is pass/fail."""
        value = proposal.get("attempted_value")
        validators: List[Dict[str, str]] = []

        # A proposal must be a meaningful value, not punctuation left behind by a
        # blurred scan ("?" / "???") - those must fail, not slip through.
        meaningful = bool(value) and len(re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", str(value))) >= 3
        span = field_evidence.locate_span(doc_text, value, allow_partial=False) if meaningful else None
        if value in (None, ""):
            detail = "no value could be proposed for this required field"
        elif not meaningful:
            detail = "proposed value is not a meaningful value (fewer than 3 readable characters)"
        elif not span:
            # Check if this was a partial match that was rejected by strict provenance
            partial_span = field_evidence.locate_span(doc_text, value, allow_partial=True)
            if partial_span:
                detail = (f"partial match rejected: full normalised value not grounded in source text "
                          f"(only partial token matched at offset {partial_span['char_offset']})")
            else:
                detail = "proposed value not found in the source document"
        else:
            detail = (f"located at offset {span['char_offset']} "
                      f"(chars {span['start_char']}-{span['end_char']})")
        validators.append({
            "name": "source_match",
            "status": "pass" if (meaningful and span) else "fail",
            "detail": detail,
        })

        wl = field_evidence.check_whitelist(field_key, value, doc_text)
        validators.append({
            "name": "whitelist",
            "status": "pass" if wl.get("status") in ("pass", "n/a") else "fail",
            "detail": f"{wl.get('table') or 'no code list'}: {wl.get('details')}",
        })

        mapping = dcsa_mapping.mapping_for(field_key)
        known = mapping.get("dcsa_field") or mapping.get("internal_only")
        validators.append({
            "name": "dcsa_mapping",
            "status": "pass" if known else "fail",
            "detail": mapping.get("dcsa_field") or "internal-only field (no DCSA BoL equivalent)",
        })

        return validators

    # ── providers ─────────────────────────────────────────────────────────

    def _local_candidates(
        self,
        field_key: str,
        doc_text: str,
        raw_label: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Deterministic, rules-derived suggestion (no LLM call, no tokens).

        Looks for the (possibly reworded) label in the document and proposes the
        remainder of that line, so provenance validation can still decide.
        """
        if not doc_text:
            return []
        lines = doc_text.replace("\r", "").splitlines()
        needles: List[str] = []
        if raw_label:
            needles.append(raw_label.strip().lower())
        needles.append(field_key.replace("_", " ").lower())
        needles.extend(LOCAL_SYNONYMS.get(field_key, []))

        seen = set()
        for needle in needles:
            if not needle or needle in seen:
                continue
            seen.add(needle)
            for idx, line in enumerate(lines):
                stripped = line.strip()
                if not stripped or needle not in stripped.lower():
                    continue
                sep_index = None
                sep_len = 0
                for sep in (":", " - ", "|"):
                    pos = stripped.find(sep)
                    if pos > 0:
                        sep_index, sep_len = pos, len(sep)
                        break
                if sep_index is None:
                    # label alone on its own line -> take the next non-empty line
                    for nxt in lines[idx + 1:]:
                        if nxt.strip():
                            return [self._candidate(doc_text, nxt.strip())]
                    continue
                remainder = stripped[sep_index + sep_len:].strip()
                if remainder:
                    return [self._candidate(doc_text, remainder)]
        return []

    def _candidate(self, doc_text: str, value: str) -> Dict[str, Any]:
        span = field_evidence.locate_span(doc_text, value) or {}
        return {
            "value": value,
            "char_offset": span.get("char_offset"),
            "exact_text": span.get("exact_text"),
            "line_number": span.get("line_number"),
        }

    def _call_llm(
        self,
        field_key: str,
        doc_text: str,
        raw_label: Optional[str],
        reflections: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple:
        """LLM call path - only reachable when a provider and credential are set.

        The request is deliberately narrow: the agent receives the unresolved label
        plus a bounded window of the document, never the fields the rules already
        handled (that split is recorded in the reasoning receipt).
        Retrieved Reflexion memories are injected as lessons from past corrections.
        """
        model = self.provider.get("model") or DEFAULT_MODEL
        window = "\n".join(doc_text.splitlines()[:40])

        lessons_header = ""
        if reflections:
            lessons_text = "\n".join(f"- {r.get('reflection_text')}" for r in reflections if r.get('reflection_text'))
            if lessons_text:
                lessons_header = f"Lessons from past corrections with this sender:\n{lessons_text}\n\n"

        prompt = (
            f"{lessons_header}"
            "You extract one field from a shipping document. Return JSON "
            '{"value": "<verbatim text from the document>"}.\n'
            f"Field: {field_key}\nLabel seen: {raw_label}\nDocument window:\n{window}"
        )
        try:  # pragma: no cover - requires credentials/network
            import urllib.request
            import json as _json

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=_json.dumps({
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                }).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get(API_KEY_ENV, '')}",
                },
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = _json.loads(resp.read().decode())
            content = payload["choices"][0]["message"]["content"]
            value = _json.loads(re.search(r"\{.*\}", content, re.S).group(0)).get("value", "")
            tokens = int(payload.get("usage", {}).get("total_tokens") or 0)
            if value:
                return [self._candidate(doc_text, value.strip())], tokens
            return [], tokens
        except Exception:
            return [], None


ai_agent = AIAgent()
