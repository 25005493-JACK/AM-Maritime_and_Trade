import re
from typing import Optional, Union

# Pattern to pull leading container count from strings like "15 x 20'GP", "12 x 20'FCL"
_CONTAINER_SPEC_RE = re.compile(
    r"(\d+)\s*[xX×]\s*\d+['\"]?\s*(?:GP|HQ|HC|RF|OT|FCL|LCL)?",
    re.IGNORECASE
)

def parse_container_count(val: Union[str, int, float, None]) -> Optional[int]:
    """
    Extracts an integer container count from a value string.
    Supports specifications such as '15 x 20'GP', '12 x 20'FCL', '3 containers', '4', etc.
    Returns None if blank or unparseable.
    """
    if val is None:
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)

    s = str(val).strip()
    if not s or s.upper() in ("N/A", "TBA", "BLANK", "[BLANK]", "[MISSING]") or "____" in s:
        return None

    # Check container specification pattern first (e.g. 15 x 20'GP)
    m = _CONTAINER_SPEC_RE.search(s)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass

    # Fallback to standalone integer
    m_num = re.search(r'\b(\d+)\b', s)
    if m_num:
        try:
            return int(m_num.group(1))
        except ValueError:
            pass

    return None


def parse_gross_weight_kg(val: Union[str, int, float, None]) -> Optional[float]:
    """
    Strips thousands separators (',', ' ') and unit suffixes (KG/kgs/MT/metric tons),
    converting to float kilograms rounded to 2 decimal places.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return round(float(val), 2)

    s = str(val).strip()
    if not s or s.upper() in ("N/A", "TBA", "BLANK", "[BLANK]", "[MISSING]") or "____" in s:
        return None

    s_lower = s.lower()
    is_metric_ton = ("metric ton" in s_lower or "mt" in s_lower)

    # Strip thousands separators (commas and spaces between digits)
    cleaned = re.sub(r'(?<=\d)[,\s](?=\d)', '', s)

    # Extract numeric portion
    m = re.search(r'(\d+(?:\.\d+)?)', cleaned)
    if not m:
        return None

    try:
        w = float(m.group(1))
        if is_metric_ton:
            w *= 1000.0
        return round(w, 2)
    except ValueError:
        return None
