import os
import re
import json
import csv
import unicodedata
import datetime
from typing import Dict, Any, List, Optional, Tuple
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


# ─────────────────────────────────────────────────────────────────────────────
# Field header patterns (label recognition)
# ─────────────────────────────────────────────────────────────────────────────

#: Fields whose values are free-text party blocks (company name + address).
COMPANY_NAME_FIELDS = {"shipper", "consignee", "notify_party"}

#: Party fields where a P.O. BOX line is treated as formatting noise instead of
#: a material difference between the SI and the draft BL. Financial/commercial
#: fields are never P.O. BOX-normalized.
PO_BOX_NORMALIZED_FIELDS = {"shipper", "consignee", "notify_party"}

# Label alternatives for every canonical field header. Parenthetical qualifiers
# ("(Principal or Seller)", "(Non-Negotiable)", "(KGS)"...) and bilingual
# suffixes ("(发货人)", "(通知人)"...) are absorbed by the generic optional
# bracket group that is appended to each pattern below, so a single source of
# truth covers the plain, bracketed and Chinese header variants.
HEADER_LABEL_SOURCES: Dict[str, str] = {
    "shipper": (
        r"shipper\s*/\s*exporter|shipper\s*name(?:\s*&\s*address)?|shipper"
        r"|consignor|exporter|seller|principal|发货人|托运人"
    ),
    "consignee": (
        r"consignee\s*/\s*importer|consignee|to\s*the\s*order\s*of|importer|收货人"
    ),
    "notify_party": (
        r"notify\s*party\s*/\s*intermediate\s*consignee|notify\s*address"
        r"|notify\s*party|notify|intermediate\s*consignee|通知方|通知人"
    ),
    "port_of_loading": (
        r"port\s*of\s*loading|place\s*of\s*loading|place\s*of\s*receipt"
        r"|loading\s*port|load\s*port|pol|装货港|起运港"
    ),
    "port_of_discharge": (
        r"port\s*of\s*discharge|place\s*of\s*delivery|place\s*of\s*discharge"
        r"|port\s*of\s*unloading|discharge\s*port|discharging\s*port|pod|卸货港|目的港"
    ),
    "container_count": (
        r"no\.?\s*of\s*containers(?:\s*or\s*packages)?|number\s*of\s*containers"
        r"|total\s*containers|container\s*summary|container\s*count|cntr\s*count"
        r"|total\s*cntrs|containers|箱数|集装箱数"
    ),
    "gross_weight_kg": (
        r"(?:total\s+)?gross\s*(?:weight|wt)|weight\s*\(kg\)|total\s*weight|毛重|总重量"
    ),
}

_BRACKET_SUFFIX = r"(?:\s*\([^)]*\))?"
_SEPARATOR_SUFFIX = r"\s*[:\-\)]?\s*"

#: Whole-label patterns: "Shipper (Principal or Seller):" -> "shipper".
FIELD_HEADER_PATTERNS: Dict[str, "re.Pattern"] = {
    canonical: re.compile(rf"^\s*(?:{source}){_BRACKET_SUFFIX}{_SEPARATOR_SUFFIX}$", re.I)
    for canonical, source in HEADER_LABEL_SOURCES.items()
}


def match_header_label(label: str) -> Optional[str]:
    """Return the canonical field for a raw header label, or ``None``.

    Deterministic companion to :meth:`FieldBank.resolve_label`. It recognises
    parenthetical header variants such as ``Shipper (Principal or Seller)`` and
    ``Consignee (Non-Negotiable)`` as well as the Chinese headers
    (``发货人`` / ``收货人`` / ``通知方`` / ``通知人``) even when they are absent
    from ``data/field_terms.json`` or score below the fuzzy threshold.
    """
    if not label:
        return None
    text = str(label).strip()
    for canonical, pattern in FIELD_HEADER_PATTERNS.items():
        if pattern.match(text):
            return canonical
    return None


def build_header_map() -> List[Tuple["re.Pattern", str]]:
    """Compiled ``(prefix pattern, canonical)`` list for line-level headers.

    Drop-in replacement for ``DocumentExtractor.HEADER_MAP``: it anchors on the
    label at the start of a line and swallows the trailing separator, e.g.
    ``Shipper (Principal or Seller): `` -> ``shipper``.
    """
    return [
        (re.compile(rf"^\s*(?:{source}){_BRACKET_SUFFIX}{_SEPARATOR_SUFFIX}", re.I), canonical)
        for canonical, source in HEADER_LABEL_SOURCES.items()
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Company-name normalization & comparison
# ─────────────────────────────────────────────────────────────────────────────

# ``P.O. BOX 12345``, ``P.O.BOX 12345``, ``PO BOX 12345``, ``POST OFFICE BOX 12345``
# and ``P.O. BOX: 293775`` are all removed, including the trailing box number.
_PO_BOX_RE = re.compile(
    r"\b(?:p\.?\s*o\.?\s*box|post\s+office\s+box|po\s*box)\b\.?"
    r"(?:\s*(?:no\.?|number|nr\.?|#)\s*)?\s*[:\-]?\s*[\w\-]*",
    re.I,
)

# Everything that is not a letter/digit (Latin or CJK) collapses to a space.
_PUNCTUATION_RE = re.compile(r"[^0-9A-Z\u4e00-\u9fff]+")


def _is_missing_value(value: Any) -> bool:
    """True when a field value is absent/blank and therefore not comparable."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().upper() in {"", "N/A", "NA", "NONE", "TBA", "BLANK", "-"}
    return False


def company_name_normalizer(
    value: Any,
    field_key: Optional[str] = None,
    strip_po_box: Optional[bool] = None,
) -> str:
    """Normalize a party/company name for SI-vs-BL comparison.

    Steps:
      1. NFKC-normalize and uppercase
      2. optionally drop ``P.O. BOX`` / ``POST OFFICE BOX`` / ``PO BOX``
         (default: on for :data:`PO_BOX_NORMALIZED_FIELDS` and for generic calls
         without a ``field_key``; override explicitly with ``strip_po_box``)
      3. replace punctuation with spaces
      4. collapse repeated whitespace

    ``company_name_normalizer("AL GURG STATIONERY LLC P.O. BOX 5069", "notify_party")``
    yields ``"AL GURG STATIONERY LLC"``, i.e. the same as the P.O. BOX-free SI/BL
    value, so the comparator can report a formatting-only difference.
    """
    if _is_missing_value(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).upper().strip()
    if strip_po_box is None:
        strip_po_box = field_key is None or field_key in PO_BOX_NORMALIZED_FIELDS
    if strip_po_box:
        text = _PO_BOX_RE.sub(" ", text)
    text = _PUNCTUATION_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def compare_company_name(
    si_value: Any,
    bl_value: Any,
    field_key: str = "notify_party",
) -> Dict[str, Any]:
    """Compare a party field (shipper / consignee / notify_party) across SI & BL.

    Returns the reviewer-facing verdict contract:
      * ``{"status": "NEEDS_REVIEW", "reason": "extraction_missing"}`` when
        either side is ``None``/blank - a missing value must never be reported as
        a MISMATCH defect.
      * ``{"status": "OK", "note": "exact_match"}`` when the raw values are equal.
      * ``{"status": "OK", "note": "formatting_only"}`` when the raw values differ
        but normalize to the same string (case, punctuation, P.O. BOX...).
      * ``{"status": "MISMATCH", "si": ..., "bl": ...}`` otherwise, with the
        normalized forms attached for the audit trail.
    """
    if _is_missing_value(si_value) or _is_missing_value(bl_value):
        return {
            "status": "NEEDS_REVIEW",
            "reason": "extraction_missing",
            "field_key": field_key,
            "si": si_value,
            "bl": bl_value,
        }

    si_norm = company_name_normalizer(si_value, field_key)
    bl_norm = company_name_normalizer(bl_value, field_key)

    if si_norm and si_norm == bl_norm:
        exact = str(si_value).strip() == str(bl_value).strip()
        return {
            "status": "OK",
            "note": "exact_match" if exact else "formatting_only",
            "field_key": field_key,
            "si": si_value,
            "bl": bl_value,
        }

    return {
        "status": "MISMATCH",
        "field_key": field_key,
        "si": si_value,
        "bl": bl_value,
        "si_normalized": si_norm,
        "bl_normalized": bl_norm,
    }

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

# Re-export Layer 2 document validity assessment
try:
    from backend.services.document_validator import assess_document_validity, REQUIRED_SI_FIELDS
except ImportError:
    from document_validator import assess_document_validity, REQUIRED_SI_FIELDS

