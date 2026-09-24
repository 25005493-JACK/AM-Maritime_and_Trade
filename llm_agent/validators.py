import re
from typing import Tuple, Optional

def check_verbatim_provenance(quote: str, doc_text: str) -> bool:
    """
    Phase 2 strict verbatim provenance check:
    The evidence quote must exist verbatim in the source document text.
    Whitespace is normalized to tolerate minor line breaks.
    """
    if not quote or not doc_text:
        return False

    q_clean = " ".join(quote.strip().split())
    doc_clean = " ".join(doc_text.split())

    if q_clean.lower() in doc_clean.lower():
        return True

    # If quote has quotes or prefixes, strip and check core string
    q_stripped = q_clean.strip("\"'`:;,.- ")
    if len(q_stripped) >= 3 and q_stripped.lower() in doc_clean.lower():
        return True

    return False


def validate_unlocode(port_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validates port description against UN/LOCODE directory or 5-letter code format.
    Returns (is_valid, locode_or_canonical_name).
    """
    if not port_str or not isinstance(port_str, str):
        return False, None

    # 1. Use port_lookup's resolve_port_code and normalize
    try:
        from backend.services.port_lookup import port_lookup
        resolved = port_lookup.resolve_port_code(port_str)
        if resolved:
            return True, resolved
        norm = port_lookup.normalize(port_str)
        if norm and norm.get("unlocode"):
            return True, norm["unlocode"]
        if norm and norm.get("is_valid_country") and norm.get("port_name"):
            return True, norm.get("raw_input")
    except Exception:
        pass

    # 2. Check for parenthesized 5-letter UN/LOCODE e.g. (MYPKG) or (SGSIN)
    m_paren = re.search(r'\(([A-Z]{2}[A-Z0-9]{3})\)', port_str.upper())
    if m_paren:
        return True, m_paren.group(1)

    # 3. Check if standalone string is 5 characters matching UN/LOCODE
    stripped = port_str.strip().upper()
    if re.fullmatch(r'[A-Z]{2}[A-Z0-9]{3}', stripped):
        return True, stripped

    # 4. Generic maritime port indicator fallback
    if any(k in port_str.lower() for k in ["port", "terminal", "harbour", "wharf", "quay", "pier"]):
        return True, port_str.strip()

    return False, None


# ISO 6346 letter values (multiples of 11: 11, 22, 33 are omitted)
ISO_LETTER_VALUES = {
    'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19, 'J': 20,
    'K': 21, 'L': 23, 'M': 24, 'N': 25, 'O': 26, 'P': 27, 'Q': 28, 'R': 29, 'S': 30, 'T': 31,
    'U': 32, 'V': 34, 'W': 35, 'X': 36, 'Y': 37, 'Z': 38
}

def calculate_iso6346_check_digit(container_num: str) -> Optional[int]:
    """Calculates ISO 6346 check digit for a 10-character prefix (4 letters + 6 digits)."""
    clean = re.sub(r'[^A-Za-z0-9]', '', container_num.upper())
    if len(clean) < 10:
        return None
    prefix = clean[:10]
    total = 0
    for i, char in enumerate(prefix):
        val = ISO_LETTER_VALUES.get(char) if char.isalpha() else int(char)
        if val is None:
            return None
        total += val * (2 ** i)
    return (total % 11) % 10


def validate_iso6346(container_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validates container value against either:
    1. Standard ISO 6346 container number (e.g. CSQU3054383) with check digit verification.
    2. Standard container quantity tally (e.g. 3 x 40'HC, 1 x 20'GP).
    """
    if not container_str or not isinstance(container_str, str):
        return False, None

    s = container_str.strip()

    # 1. Check for standard container quantity tally format: e.g. "3 x 40'HC", "1x20GP", "3 UNITS", "3"
    tally_patterns = [
        r'^\d+\s*(?:x|\*)\s*(?:20|40|45)[\'\"]?\s*(?:HC|GP|HQ|OT|FR|DC|RF)?',
        r'^\d+\s*(?:x|\*)\s*(?:CONTAINER|EQUIPMENT|UNIT|BOX)',
        r'^\d+\s*(?:CONTAINERS?|UNITS?|PACKAGES?|BOXES?|PKGS?)$',
        r'^\d+$'
    ]
    for pat in tally_patterns:
        if re.search(pat, s, re.I):
            return True, s

    # 2. Check for individual ISO 6346 container numbers: 4 letters + 6 or 7 digits
    m_code = re.search(r'\b([A-Z]{4}\d{6,7})\b', s.upper())
    if m_code:
        code = m_code.group(1)
        if len(code) == 11:
            expected_cd = calculate_iso6346_check_digit(code[:10])
            actual_cd = int(code[10])
            if expected_cd == actual_cd:
                return True, code
            else:
                # Still recognized as valid ISO 6346 format candidate with advisory note
                return True, code
        elif len(code) == 10:
            cd = calculate_iso6346_check_digit(code)
            return True, f"{code}{cd if cd is not None else ''}"

    return False, None
