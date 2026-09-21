"""
Red Team harness: adversarial input rehearsal through the SAME pipeline.

Transforms mutate the documents (never the pipeline) and the result is produced by
the existing classifier -> extractor -> comparator -> receipt/certificate code
paths, so what the UI renders is genuine pipeline behaviour rather than a scripted
demo path.

Transforms (deterministic, seeded by field):
  * blur         - simulate a low-quality scan (values become unreadable)
  * reword       - replace standard labels with non-standard synonyms so the rule
                   engine cannot match them (AI fallback is triggered)
  * remove_field - delete required lines so the circuit breaker trips
  * conflict     - change one side's value so SI and BL disagree
"""
import re
from typing import Any, Dict, List, Optional, Tuple

TRANSFORMS: Dict[str, Dict[str, str]] = {
    "blur": {
        "label": "Blur (low-quality scan)",
        "description": "Blurs the draft BL text so values are no longer readable; exercises the unreadable/scan-quality path.",
    },
    "reword": {
        "label": "Reword",
        "description": "Renames standard field labels to non-standard synonyms so the rule engine cannot match them; the AI fallback is invoked.",
    },
    "remove_field": {
        "label": "Remove field",
        "description": "Deletes required field lines so the AI has nothing to validate against; exercises the circuit breaker.",
    },
    "conflict": {
        "label": "Conflict",
        "description": "Changes one value on the draft BL so the two documents disagree; exercises the propose-and-confirm comparison.",
    },
}

#: Non-standard label synonyms used by the "reword" transform (and the local
#: assistant's synonym glossary). These wordings have minimal token overlap with
#: data/field_terms.json, so the rule engine cannot resolve them - which is the
#: point: reworded labels are exactly what the AI fallback exists for.
REWORD_LABELS = [
    (r"^(\s*)Consignee\b", r"\1Party Receiving Cargo"),
    (r"^(\s*)Notify\s*Party\b", r"\1Arrival Advisory Contact"),
    (r"^(\s*)Port\s*of\s*Discharge\b", r"\1Unloading Ocean Gateway"),
    (r"^(\s*)Port\s*of\s*Loading\b", r"\1Embarkation Ocean Gateway"),
    (r"^(\s*)(?:No\.\s*of\s*Containers(?:\s*or\s*Packages)?|Container\s*Count|Total\s*Containers)\b", r"\1Equipment Unit Tally"),
    (r"^(\s*)Gross\s*(?:Weight|Wt)\b", r"\1Cargo Mass Total"),
    (r"^(\s*)POD\b", r"\1Unloading Ocean Gateway"),
    (r"^(\s*)POL\b", r"\1Embarkation Ocean Gateway"),
]

REMOVE_FIELDS = [
    r"^(\s*)(?:No\.\s*of\s*Containers(?:\s*or\s*Packages)?|Container\s*Count|Total\s*Containers)\b",
    r"^(\s*)Gross\s*(?:Weight|Wt)\b",
    r"^(\s*)(?:Port\s*of\s*Discharge|POD)\b",
    r"^(\s*)(?:Port\s*of\s*Loading|POL)\b",
]


def _blur_line(line: str) -> str:
    """Keep the label, degrade the value characters (simulated scan noise)."""
    if ":" not in line:
        return line
    label, value = line.split(":", 1)
    blurred = "".join("?" if ch.isalnum() else ch for ch in value)
    return f"{label}:{blurred}"


def apply_transform(
    si_text: str,
    bl_text: str,
    transform: str,
) -> Tuple[str, str, List[str]]:
    """Return (si_text, bl_text, notes) with the transform applied to the BL."""
    notes: List[str] = []

    if transform == "blur":
        blurred = "\n".join(_blur_line(line) for line in bl_text.splitlines())
        blurred = "[UNREADABLE_SCAN_QUALITY: blurred]\n" + blurred
        notes.append("Draft BL values blurred; unreadable scan marker injected.")
        return si_text, blurred, notes

    if transform == "reword":
        reworded = bl_text
        replaced = 0
        for pattern, replacement in REWORD_LABELS:
            reworded, count = re.subn(pattern, replacement, reworded, flags=re.MULTILINE)
            replaced += count
        notes.append(f"Renamed {replaced} standard field label(s) to non-standard synonyms.")
        return si_text, reworded, notes

    if transform == "remove_field":
        reduced = bl_text
        removed = 0
        for pattern in REMOVE_FIELDS:
            reduced, count = re.subn(pattern + r".*$", "", reduced, flags=re.MULTILINE)
            removed += count
        notes.append(f"Removed {removed} required field line(s) from the draft BL.")
        return si_text, reduced, notes

    if transform == "conflict":
        def change(match: "re.Match") -> str:
            prefix, label, value = match.group(1), match.group(2), match.group(3)
            number = re.search(r"\d+", value)
            if number:
                if number.group(0) == "0":
                    bumped = "2"
                else:
                    bumped = str(int(number.group(0)) + 2)
                new_value = f"{value[:number.start()]}{bumped}{value[number.end():]}"
            else:
                new_value = f"{value} (AMENDED)"
            return f"{prefix}{label}: {new_value}"

        altered, count = re.subn(
            r"^(\s*)((?:No\.\s*of\s*Containers(?:\s*or\s*Packages)?|Container\s*Count|Total\s*Containers))\s*[:]?\s*(.*)$",
            change,
            bl_text,
            flags=re.MULTILINE,
        )
        notes.append(f"Changed the draft BL container count ({count} line(s)) to force a conflict.")
        return si_text, altered, notes

    raise ValueError(f"Unknown transform '{transform}'. Expected one of {sorted(TRANSFORMS)}")


def transform_catalog() -> List[Dict[str, str]]:
    return [{"id": key, **value} for key, value in TRANSFORMS.items()]
