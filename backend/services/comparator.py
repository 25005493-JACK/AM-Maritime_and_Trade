import re
from typing import Dict, Any, List
from backend.services.extractor import extractor

class DocumentComparator:
    """
    Compares extracted SI fields (reference) against draft BL fields.
    Evaluates matches across 7 standard fields, formats diffs, and generates next actions.
    """

    FIELDS = [
        "shipper",
        "consignee",
        "notify_party",
        "port_of_loading",
        "port_of_discharge",
        "container_count",
        "gross_weight_kg"
    ]

    FIELD_LABELS = {
        "shipper": "Shipper Name & Address",
        "consignee": "Consignee",
        "notify_party": "Notify Party",
        "port_of_loading": "Port of Loading (POL)",
        "port_of_discharge": "Port of Discharge (POD)",
        "container_count": "Container Count",
        "gross_weight_kg": "Gross Weight (kg)"
    }

    def compare_documents(
        self,
        si_text: str,
        bl_text: str,
        overrides: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        si_extracted = extractor.extract_fields(si_text, doc_type="SI")
        bl_extracted = extractor.extract_fields(bl_text, doc_type="BL")

        # Apply manual human overrides if provided
        if overrides:
            for field, val in overrides.get("si_overrides", {}).items():
                if field in si_extracted:
                    si_extracted[field] = val
            for field, val in overrides.get("bl_overrides", {}).items():
                if field in bl_extracted:
                    bl_extracted[field] = val

        # Check for Human Review triggers (low confidence or missing critical values)
        requires_human_review = False
        human_review_reasons = []

        if si_extracted["confidence"] < 0.70:
            requires_human_review = True
            human_review_reasons.extend([f"SI: {r}" for r in si_extracted["unreadable_reasons"]])

        if bl_extracted["confidence"] < 0.70:
            requires_human_review = True
            human_review_reasons.extend([f"BL: {r}" for r in bl_extracted["unreadable_reasons"]])

        # Check missing required fields
        for f in self.FIELDS:
            if si_extracted[f] is None:
                requires_human_review = True
                human_review_reasons.append(f"SI missing value for {self.FIELD_LABELS[f]}")
            if bl_extracted[f] is None:
                requires_human_review = True
                human_review_reasons.append(f"BL missing value for {self.FIELD_LABELS[f]}")

        # Field Comparison Matrix
        matrix = []
        mismatched_fields = []
        matching_fields = []

        for f in self.FIELDS:
            si_val = si_extracted[f]
            bl_val = bl_extracted[f]

            is_match, formatted_si, formatted_bl = self._compare_single_field(f, si_val, bl_val)

            item = {
                "field_key": f,
                "field_name": self.FIELD_LABELS[f],
                "si_value": formatted_si,
                "bl_value": formatted_bl,
                "is_match": is_match,
                "diff_summary": f"SI: {formatted_si} / BL: {formatted_bl}" if not is_match else "Matched"
            }
            matrix.append(item)

            if is_match:
                matching_fields.append(f)
            else:
                mismatched_fields.append(item)

        # Status & Recommendation
        if requires_human_review:
            status = "HUMAN_REVIEW_REQUIRED"
            summary_message = "Human Review Required: Document unreadable or field missing."
            recommended_action = f"Escalate case to Document Supervisor. Reason: {'; '.join(set(human_review_reasons))}"
        elif len(mismatched_fields) > 0:
            status = "MISMATCH_DETECTED"
            diff_str_list = [f"{m['field_name']} ({m['diff_summary']})" for m in mismatched_fields]
            summary_message = f"Found {len(mismatched_fields)} field mismatch(es): {', '.join(diff_str_list)}"
            recommended_action = f"Request revised draft BL from carrier for {mismatched_fields[0]['field_name']} mismatch ({mismatched_fields[0]['diff_summary']})"
        else:
            status = "NO_MISMATCH_DETECTED"
            summary_message = "No mismatch detected."
            recommended_action = "Approve draft BL and notify Shipper for document release."

        return {
            "status": status,
            "summary_message": summary_message,
            "recommended_action": recommended_action,
            "requires_human_review": requires_human_review,
            "human_review_reasons": list(set(human_review_reasons)),
            "si_extracted": si_extracted,
            "bl_extracted": bl_extracted,
            "field_matrix": matrix,
            "mismatched_fields": [m["field_key"] for m in mismatched_fields],
            "matching_fields": matching_fields
        }

    def _compare_single_field(self, field_key: str, si_val: Any, bl_val: Any) -> tuple:
        if si_val is None or bl_val is None:
            return (False, str(si_val or "N/A"), str(bl_val or "N/A"))

        if field_key == "container_count":
            try:
                si_int = int(si_val)
                bl_int = int(bl_val)
                return (si_int == bl_int, str(si_int), str(bl_int))
            except (ValueError, TypeError):
                return (False, str(si_val), str(bl_val))

        if field_key == "gross_weight_kg":
            try:
                si_float = float(si_val)
                bl_float = float(bl_val)
                # Allow minor 0.1kg floating point rounding tolerance
                is_match = abs(si_float - bl_float) < 0.1
                return (is_match, f"{si_float:.2f} kg", f"{bl_float:.2f} kg")
            except (ValueError, TypeError):
                return (False, str(si_val), str(bl_val))

        # String fields: normalize whitespace & punctuation
        norm_si = self._normalize_str(str(si_val))
        norm_bl = self._normalize_str(str(bl_val))

        is_match = norm_si == norm_bl
        return (is_match, str(si_val), str(bl_val))

    def _normalize_str(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r'[\.,\-\/\\_\(\)]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

comparator = DocumentComparator()
