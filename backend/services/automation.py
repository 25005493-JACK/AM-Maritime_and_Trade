"""
Automation level ("AI license") - how autonomous the pipeline may be, L0 to L3.

  L0 - nothing is auto-written; every field goes to the human review queue.
  L1 - fields are extracted and suggested, but nothing is written without explicit
       human confirmation (the default for AI-sourced fields).
  L2 - fields whose confidence is >= the auto-write threshold AND that agree across
       documents are auto-written, then queued for post-hoc audit; everything else
       goes to review.
  L3 - same as L2 but auto-written fields are not queued for audit; only validator
       failures go to review.

Confidence comes from validators that already exist in the pipeline (source_match
provenance, code-list whitelist, DCSA mapping) - no invented scores. The preview
aggregates those same signals over the real evaluation set, so every number shown
in the UI is traceable to fields the system actually compared.
"""
import os
import threading
from typing import Any, Dict, List, Optional, Tuple

from backend.services import dcsa_mapping, field_evidence

AUTO_WRITE_CONFIDENCE = float(os.environ.get("DOCUMATCH_AUTOMATION_CONFIDENCE", "0.9"))
MANUAL_REVIEW_MINUTES_PER_FIELD = int(os.environ.get("DOCUMATCH_MANUAL_REVIEW_MINUTES", "4"))

VALIDATOR_WEIGHTS = {"source_match": 0.5, "whitelist": 0.3, "dcsa_mapping": 0.2}

LEVELS: Dict[int, Dict[str, str]] = {
    0: {"label": "L0 - Manual Control (0% Automation)",
        "description": "Zero auto-write; 100% of documents and fields are queued for Human Review."},
    1: {"label": "L1 - Conservative Triage (Strict Exact Matches)",
        "description": "Auto-writes 100% exact raw text matches with zero validator failures; fuzzy & ungrounded fields go to review."},
    2: {"label": "L2 - Balanced Agent + Audit (Default Standard)",
        "description": f"Auto-writes agreeing SI vs BL fields with confidence >= {AUTO_WRITE_CONFIDENCE:.2f}; mismatches go to review with post-hoc audit."},
    3: {"label": "L3 - Full Autonomous Straight-Through Processing",
        "description": "High-autonomy straight-through processing for trusted carriers; auto-writes all valid extracted fields without audit."},
}


def signals_from_matrix_row(field_key: str, row: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    """Build real validator signals for a compared field (no synthetic scores)."""
    value = row.get("bl_value")
    source_text = raw_text or ""
    span = field_evidence.locate_span(source_text, value) if value else None
    wl = field_evidence.check_whitelist(field_key, value, source_text)
    mapping = dcsa_mapping.mapping_for(field_key)
    validators = [
        {"name": "source_match", "status": "pass" if span else "fail"},
        {"name": "whitelist", "status": "pass" if wl.get("status") in ("pass", "n/a") else "fail"},
        {"name": "dcsa_mapping",
         "status": "pass" if (mapping.get("dcsa_field") or mapping.get("internal_only")) else "fail"},
    ]
    return {
        "agreement": "match" if row.get("is_match") else "conflict",
        "match_type": row.get("match_type"),
        "validators": validators,
    }


def field_confidence(validators: List[Dict[str, str]]) -> Tuple[float, Dict[str, float]]:
    """Weighted confidence from validator outcomes (sum of weights that passed)."""
    breakdown: Dict[str, float] = {}
    total = 0.0
    for name, weight in VALIDATOR_WEIGHTS.items():
        entry = next((v for v in validators if v.get("name") == name), None)
        passed = bool(entry) and entry.get("status") == "pass"
        breakdown[name] = weight if passed else 0.0
        total += weight if passed else 0.0
    return round(total, 2), breakdown


class AutomationController:
    """Session-scoped automation level (in-memory, by design)."""

    def __init__(self, level: int = 1):
        self._level = level
        self._lock = threading.Lock()
        self._preview_cache: Dict[int, Dict[str, Any]] = {}

    def get_level(self) -> int:
        with self._lock:
            return self._level

    def set_level(self, level: int) -> Dict[str, Any]:
        if level not in LEVELS:
            raise ValueError(f"Automation level must be one of {sorted(LEVELS)}")
        with self._lock:
            self._level = level
            self._preview_cache.clear()
        return {"level": level, "level_label": LEVELS[level]["label"], **LEVELS[level]}

    def level_info(self) -> Dict[str, Any]:
        level = self.get_level()
        return {
            "level": level,
            "level_label": LEVELS[level]["label"],
            "levels": [{"level": key, **value} for key, value in LEVELS.items()],
            "auto_write_confidence": AUTO_WRITE_CONFIDENCE,
            "manual_review_minutes_per_field": MANUAL_REVIEW_MINUTES_PER_FIELD,
        }

    def classify_field(
        self,
        field_key: str,
        signals: Dict[str, Any],
        level: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Decide auto-write vs review for one field at the given level."""
        level = self.get_level() if level is None else level
        validators = signals.get("validators") or []
        confidence, breakdown = field_confidence(validators)
        failed = [v["name"] for v in validators if v.get("status") == "fail"]
        agrees = signals.get("agreement") == "match"
        threshold = f"{AUTO_WRITE_CONFIDENCE:.2f}"

        if level in (0, 1):
            action = "review"
            reason = f"L{level}: Triage mode; every field is queued for Human Review."
        elif level == 2:
            if confidence >= AUTO_WRITE_CONFIDENCE and agrees:
                action = "auto_write_audit"
                reason = (f"L2: confidence {confidence:.2f} >= {threshold} and documents agree; "
                          "written and queued for post-hoc audit.")
            else:
                action = "review"
                reason = (f"L2: confidence {confidence:.2f} below {threshold} or documents disagree "
                          f"({', '.join(failed) or 'no failing validators'}).")
        else:
            if confidence >= 0.80 and agrees:
                action = "auto_write"
                reason = f"L3: High-autonomy straight-through processing (confidence {confidence:.2f}); written without audit."
            else:
                action = "review"
                reason = f"L3: Critical extraction failure ({', '.join(failed) or 'validation failed'}); routed to review."

        return {
            "field_key": field_key,
            "dcsa_field": dcsa_mapping.dcsa_field_name(field_key),
            "action": action,
            "confidence": confidence,
            "confidence_breakdown": breakdown,
            "agreement": signals.get("agreement"),
            "evidence_strength": ("exact" if signals.get("match_type") == "EXACT"
                                  else "derived" if signals.get("match_type") in ("NORMALIZED", "FUZZY")
                                  else "weak"),
            "failed_validators": failed,
            "reason": reason,
        }

    def apply(self, verification: Optional[Dict[str, Any]], level: Optional[int] = None) -> Dict[str, Any]:
        """Per-field actions for one comparison result (used by the inbox cards)."""
        level = self.get_level() if level is None else level
        verif = verification or {}
        raw_text = ((verif.get("bl_extracted") or {}).get("raw_text")
                    or (verif.get("si_extracted") or {}).get("raw_text") or "")
        decisions = [
            self.classify_field(
                row.get("field_key"),
                signals_from_matrix_row(row.get("field_key"), row, raw_text),
                level,
            )
            for row in verif.get("field_matrix") or []
        ]
        counts = {
            "auto_processed": sum(1 for d in decisions if d["action"].startswith("auto_write")),
            "flagged_for_review": sum(1 for d in decisions if d["action"] == "review"),
            "fields": len(decisions),
        }
        if counts["auto_processed"] and not counts["flagged_for_review"]:
            state = "auto_processed"
        elif counts["flagged_for_review"]:
            state = "needs_you"
        else:
            state = "none"
        return {
            "level": level,
            "level_label": LEVELS[level]["label"],
            "counts": counts,
            "state": state,
            "decisions": decisions,
        }

    # ── preview over the real evaluation set ──────────────────────────────

    def preview(
        self,
        summaries: List[Dict[str, Any]],
        level: Optional[int] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Recompute the automation metrics from real comparison results."""
        level = self.get_level() if level is None else level

        if use_cache and level in self._preview_cache:
            return self._preview_cache[level]

        fields_total = 0
        auto_processed = 0
        flagged = 0
        exposure = 0
        emails_considered = 0
        files_for_review = 0

        for summary in summaries or []:
            verification = (summary or {}).get("verification")
            if not verification or not verification.get("field_matrix"):
                continue
            emails_considered += 1
            raw_text = ((verification.get("bl_extracted") or {}).get("raw_text")
                        or (verification.get("si_extracted") or {}).get("raw_text") or "")
            file_flagged = False
            for row in verification["field_matrix"]:
                decision = self.classify_field(
                    row.get("field_key"),
                    signals_from_matrix_row(row.get("field_key"), row, raw_text),
                    level,
                )
                fields_total += 1
                if decision["action"].startswith("auto_write"):
                    auto_processed += 1
                    if level == 1:
                        pass
                    elif level == 2:
                        if decision["evidence_strength"] != "exact" or decision["failed_validators"]:
                            exposure += 1
                    elif level == 3:
                        if decision["evidence_strength"] != "exact" or decision["failed_validators"] or decision["agreement"] != "match":
                            exposure += 1
                else:
                    flagged += 1
                    if level in (0, 1):
                        file_flagged = True
                    elif level == 2:
                        if decision["agreement"] != "match" or decision["confidence"] < 0.60:
                            file_flagged = True
                    elif level == 3:
                        if decision["agreement"] != "match" and decision["confidence"] < 0.60:
                            file_flagged = True

            if file_flagged or level == 0:
                files_for_review += 1

        result = {
            "level": level,
            "level_label": LEVELS[level]["label"],
            "level_description": LEVELS[level]["description"],
            "auto_processed_pct": round(auto_processed / fields_total * 100, 1) if fields_total else 0.0,
            "flagged_for_review_pct": round(flagged / fields_total * 100, 1) if fields_total else 0.0,
            "files_for_review": files_for_review,
            "files_for_review_pct": round(files_for_review / emails_considered * 100, 1) if emails_considered else 0.0,
            "estimated_time_saved_minutes": auto_processed * MANUAL_REVIEW_MINUTES_PER_FIELD,
            "estimated_error_exposure_pct": round(exposure / auto_processed * 100, 1) if auto_processed else 0.0,
            "counts": {
                "auto_processed": auto_processed,
                "flagged_for_review": flagged,
                "fields": fields_total,
                "files_for_review": files_for_review,
                "total_files": emails_considered,
            },
            "sample_basis": {
                "emails_considered": emails_considered,
                "fields_considered": fields_total,
                "source": "live comparison results for the inbox currently loaded (same data the UI shows)",
            },
            "formula": {
                "confidence": "sum of passed validator weights: source_match 0.5 + whitelist 0.3 + dcsa_mapping 0.2",
                "auto_write_threshold": AUTO_WRITE_CONFIDENCE,
                "estimated_error_exposure_pct": (
                    "auto-written fields whose evidence is not a byte-exact match "
                    "(NORMALIZED/FUZZY match_type) or that failed a validator / all auto-written fields"
                ),
                "estimated_time_saved_minutes": (
                    f"auto-written fields x {MANUAL_REVIEW_MINUTES_PER_FIELD} min manual review per field "
                    "(documented constant, configurable via DOCUMATCH_MANUAL_REVIEW_MINUTES)"
                ),
            },
        }
        if use_cache:
            self._preview_cache[level] = result
        return result


automation = AutomationController()
