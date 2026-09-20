import os
import re
import json
import csv
import unicodedata
import datetime
from typing import Dict, Any, Optional, Tuple
import rapidfuzz.fuzz

CANONICAL_FIELDS = {
    "shipper",
    "consignee",
    "notify_party",
    "port_of_loading",
    "port_of_discharge",
    "container_count",
    "gross_weight_kg"
}

def is_cjk(s: str) -> bool:
    """Check if string contains Chinese/Japanese/Korean characters."""
    for ch in s:
        if '\u4e00' <= ch <= '\u9fff' or '\u3400' <= ch <= '\u4dbf':
            return True
    return False

class FieldBank:
    """
    Resolves extracted document field labels into canonical field names.
    Uses exact/normalized lookup first, then rapidfuzz fuzzy matching.
    Unresolved labels are flagged as term_unresolved and appended to term_candidates.csv.
    """

    def __init__(self, terms_path: Optional[str] = None):
        self.terms_path = terms_path or self._find_terms_path()
        self.terms_dict: Dict[str, str] = {}
        self._load_terms()

    def _find_terms_path(self) -> str:
        candidates = [
            os.path.join(os.getcwd(), "data", "field_terms.json"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "field_terms.json"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "field_terms.json"),
            "data/field_terms.json"
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return "data/field_terms.json"

    def _load_terms(self):
        if not os.path.exists(self.terms_path):
            return
        with open(self.terms_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            for k, v in raw.items():
                norm_k = self.normalize_label(k)
                if norm_k:
                    self.terms_dict[norm_k] = v.strip().lower()

    def normalize_label(self, label: str) -> str:
        if not label:
            return ""
        # NFKC normalize, lowercase, and strip
        s = unicodedata.normalize("NFKC", str(label)).lower().strip()
        # Separate Latin characters and CJK ideographs
        s = re.sub(r'([a-zA-Z0-9])([\u4e00-\u9fff])', r'\1 \2', s)
        s = re.sub(r'([\u4e00-\u9fff])([a-zA-Z0-9])', r'\1 \2', s)
        # Replace punctuation brackets/hyphens/colons with spaces
        s = re.sub(r'[\(\)\[\]\{\}\-\_\:\/\\,\.]', ' ', s)
        return re.sub(r'\s+', ' ', s).strip()

    def resolve_label(self, raw_label: str, threshold: float = 85.0) -> Dict[str, Any]:
        """
        Resolves raw label string into canonical field name:
        1. Exact / normalized dictionary lookup
        2. Bilingual component extraction (Latin or CJK sub-portion)
        3. Rapidfuzz fuzzy match against dictionary keys (same-language script)
        4. If still unresolved -> flags as is_unresolved
        """
        if not raw_label:
            return {
                "canonical": None,
                "method": "unresolved",
                "confidence": 0.0,
                "raw_label": raw_label,
                "matched_term": None,
                "is_unresolved": True
            }

        norm = self.normalize_label(raw_label)

        # 1. Exact normalized lookup
        if norm in self.terms_dict:
            return {
                "canonical": self.terms_dict[norm],
                "method": "exact",
                "confidence": 1.0,
                "raw_label": raw_label,
                "matched_term": norm,
                "is_unresolved": False
            }

        # 2. Bilingual sub-component check (if mixed Latin & CJK)
        if is_cjk(norm):
            # Check Latin sub-component
            latin_sub = re.sub(r'[\u4e00-\u9fff]+', ' ', norm)
            latin_norm = re.sub(r'\s+', ' ', latin_sub).strip()
            if latin_norm and latin_norm in self.terms_dict:
                return {
                    "canonical": self.terms_dict[latin_norm],
                    "method": "exact",
                    "confidence": 1.0,
                    "raw_label": raw_label,
                    "matched_term": latin_norm,
                    "is_unresolved": False
                }

            # Check CJK sub-component
            cjk_chars = [ch for ch in norm if '\u4e00' <= ch <= '\u9fff']
            cjk_sub = "".join(cjk_chars).strip()
            if cjk_sub and cjk_sub in self.terms_dict:
                return {
                    "canonical": self.terms_dict[cjk_sub],
                    "method": "exact",
                    "confidence": 1.0,
                    "raw_label": raw_label,
                    "matched_term": cjk_sub,
                    "is_unresolved": False
                }

        # 3. Rapidfuzz fuzzy match against dictionary keys (same language script)
        raw_is_cjk = is_cjk(norm)
        best_score = 0.0
        best_term = None
        best_canonical = None

        for term_key, canonical in self.terms_dict.items():
            # Ensure same-language script matching
            if is_cjk(term_key) != raw_is_cjk:
                continue

            score = rapidfuzz.fuzz.token_sort_ratio(norm, term_key)
            if score > best_score:
                best_score = score
                best_term = term_key
                best_canonical = canonical

        if best_score >= threshold and best_canonical:
            return {
                "canonical": best_canonical,
                "method": "fuzzy",
                "confidence": round(best_score / 100.0, 2),
                "raw_label": raw_label,
                "matched_term": best_term,
                "is_unresolved": False
            }

        # 4. Unresolved
        return {
            "canonical": None,
            "method": "unresolved",
            "confidence": 0.0,
            "raw_label": raw_label,
            "matched_term": None,
            "is_unresolved": True
        }

    def record_unresolved_candidate(
        self,
        email_id: str,
        raw_label: str,
        raw_value: str,
        doc_type: str = "SI"
    ):
        """Appends unrecognised label candidate to data/term_candidates.csv."""
        candidates_file = os.path.join("data", "term_candidates.csv")
        os.makedirs(os.path.dirname(candidates_file), exist_ok=True)
        is_new = not os.path.exists(candidates_file)
        
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        try:
            with open(candidates_file, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if is_new:
                    writer.writerow(["timestamp", "email_id", "raw_label", "raw_value", "doc_type"])
                writer.writerow([now_ts, email_id, raw_label, raw_value[:150], doc_type])
        except Exception as ex:
            print(f"Failed to record term candidate: {ex}")

field_bank = FieldBank()
