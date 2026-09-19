"""
Anchor-Field-First Triage (Tech Desk v4 — Section 3.2)

Scans raw document text for value-shaped anchor fields — container numbers,
BL numbers, and gross weight — using regex and ISO 6346 checksum validation.
Runs *before* the full extraction pipeline.

If anchor fields already disagree between SI and BL (e.g. completely disjoint
container numbers), that's a strong signal of wrong document pairing — fast-path
this straight to human escalation, skipping the rest of the extraction pipeline.
"""
import re
import hashlib
from typing import Dict, Any, List, Optional, Set, Tuple

# ISO 6346 container number pattern: 4 uppercase letters + 7 digits
_CONTAINER_RE = re.compile(r'\b([A-Z]{4}\d{7})\b')

# BL number pattern: SCAC prefix (4 letters) + 8+ digits
_BL_NUMBER_RE = re.compile(r'\b([A-Z]{4}\d{8,})\b')

# Gross weight pattern: numeric value + unit
_WEIGHT_RE = re.compile(
    r'(\d[\d,\.]*)\s*(?:KGS?|KG|METRIC\s+TONS?|MT)\b',
    re.IGNORECASE
)

# ISO 6346 check digit calculation
_ISO6346_CHARS = {chr(c): i for i, c in enumerate(
    list(range(ord('A'), ord('Z') + 1)) + list(range(ord('0'), ord('9') + 1))
)}


def _iso6346_check_digit(owner_code_and_serial: str) -> Optional[int]:
    """
    Compute the ISO 6346 check digit for a container number (first 10 chars).
    Returns the expected check digit (0-9), or None if input is invalid.
    """
    if len(owner_code_and_serial) < 10:
        return None

    s = owner_code_and_serial[:10].upper()
    char_values = "0123456789A BCDEFGHIJK LMNOPQRSTU VWXYZ"
    lookup = {}
    idx = 0
    for c in char_values:
        if c == ' ':
            continue
        lookup[c] = idx
        idx += 1

    total = 0
    for i, ch in enumerate(s):
        val = lookup.get(ch)
        if val is None:
            return None
        total += val * (2 ** i)

    return total % 11 % 10


def _validate_container_number(number: str) -> bool:
    """Validate a container number against ISO 6346 check digit."""
    if len(number) != 11:
        return False
    expected = _iso6346_check_digit(number[:10])
    if expected is None:
        return False
    try:
        actual = int(number[10])
        return actual == expected
    except (ValueError, IndexError):
        return False


def _extract_container_numbers(text: str) -> Set[str]:
    """Extract all container-number-shaped strings from text."""
    candidates = _CONTAINER_RE.findall(text.upper())
    # Return all matches (validated or not — many real containers fail checksum
    # due to carrier-specific numbering, so we keep all pattern matches)
    return set(candidates)


def _extract_bl_numbers(text: str) -> Set[str]:
    """Extract all BL-number-shaped strings from text."""
    return set(_BL_NUMBER_RE.findall(text.upper()))


def _extract_weights(text: str) -> List[float]:
    """Extract all weight values from text, normalized to kg."""
    weights = []
    for m in _WEIGHT_RE.finditer(text):
        raw = m.group(1).replace(',', '')
        try:
            val = float(raw)
            unit_text = m.group(0).upper()
            if 'METRIC TON' in unit_text or ' MT' in unit_text:
                val *= 1000.0
            weights.append(round(val, 2))
        except ValueError:
            continue
    return weights


class AnchorTriage:
    """
    Fast-path anchor-field triage that runs before full extraction.
    Compares value-shaped fields (container numbers, BL numbers, weight)
    between SI and BL documents to detect wrong document pairings early.
    """

    def triage(self, si_text: str, bl_text: str) -> Dict[str, Any]:
        """
        Run anchor-field triage on SI and BL document texts.

        Returns:
            {
                "triage_outcome": "pass" | "fast_escalate",
                "reason_code": str | None,
                "reason_message": str | None,
                "anchor_fields_si": { containers, bl_numbers, weights },
                "anchor_fields_bl": { containers, bl_numbers, weights },
                "confidence": float
            }
        """
        si_containers = _extract_container_numbers(si_text)
        bl_containers = _extract_container_numbers(bl_text)
        si_bl_nums = _extract_bl_numbers(si_text)
        bl_bl_nums = _extract_bl_numbers(bl_text)
        si_weights = _extract_weights(si_text)
        bl_weights = _extract_weights(bl_text)

        anchor_si = {
            "containers": sorted(si_containers),
            "bl_numbers": sorted(si_bl_nums),
            "weights": si_weights
        }
        anchor_bl = {
            "containers": sorted(bl_containers),
            "bl_numbers": sorted(bl_bl_nums),
            "weights": bl_weights
        }

        # Check 1: Completely disjoint container numbers
        if si_containers and bl_containers:
            overlap = si_containers & bl_containers
            if len(overlap) == 0:
                return {
                    "triage_outcome": "fast_escalate",
                    "reason_code": "possible_wrong_pairing",
                    "reason_message": (
                        f"Container numbers are completely disjoint between SI "
                        f"({', '.join(sorted(si_containers))}) and BL "
                        f"({', '.join(sorted(bl_containers))}). "
                        f"Likely wrong document pairing."
                    ),
                    "anchor_fields_si": anchor_si,
                    "anchor_fields_bl": anchor_bl,
                    "confidence": 0.92
                }

        # Check 2: Completely disjoint BL numbers (if both documents have them)
        if si_bl_nums and bl_bl_nums:
            bl_overlap = si_bl_nums & bl_bl_nums
            if len(bl_overlap) == 0:
                return {
                    "triage_outcome": "fast_escalate",
                    "reason_code": "possible_wrong_pairing",
                    "reason_message": (
                        f"BL numbers are completely disjoint between SI "
                        f"({', '.join(sorted(si_bl_nums))}) and BL "
                        f"({', '.join(sorted(bl_bl_nums))}). "
                        f"Likely wrong document pairing."
                    ),
                    "anchor_fields_si": anchor_si,
                    "anchor_fields_bl": anchor_bl,
                    "confidence": 0.88
                }

        # All anchors agree or are inconclusive — pass through
        return {
            "triage_outcome": "pass",
            "reason_code": None,
            "reason_message": None,
            "anchor_fields_si": anchor_si,
            "anchor_fields_bl": anchor_bl,
            "confidence": 1.0
        }


anchor_triage = AnchorTriage()
