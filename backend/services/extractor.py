import re
from typing import Dict, Any, Optional, List

class DocumentExtractor:
    """
    Extracts the 7 required shipment fields from SI and draft BL documents:
    - shipper
    - consignee
    - notify_party
    - port_of_loading
    - port_of_discharge
    - container_count
    - gross_weight_kg

    Handles multi-format text (TXT, PDF, DOCX, XLSX), bilingual/multilingual headers,
    multi-line addresses, wrong document types, unreadable/corrupted files, and missing values.
    """

    HEADER_MAP = [
        (re.compile(r'^(?:shipper/exporter|shipper\s*\([^\)]*\)|shipper)\s*[:\-\)]?\s*', re.I), 'shipper'),
        (re.compile(r'^(?:consignee\s*\([^\)]*\)|consignee\s*/\s*importer|to\s*the\s*order\s*of|consignee)\s*[:\-\)]?\s*', re.I), 'consignee'),
        (re.compile(r'^(?:notify\s*party/intermediate\s*consignee|notify\s*party\s*\([^\)]*\)|notify\s*party|notify)\s*[:\-\)]?\s*', re.I), 'notify_party'),
        (re.compile(r'^(?:port\s*of\s*loading\s*\([^\)]*\)|port\s*of\s*loading|load\s*port|pol|place\s*of\s*loading)\s*[:\-\)]?\s*', re.I), 'port_of_loading'),
        (re.compile(r'^(?:port\s*of\s*discharge\s*\([^\)]*\)|port\s*of\s*discharge|discharge\s*port|pod|place\s*of\s*delivery|place\s*of\s*discharge|port\s*of\s*unloading)\s*[:\-\)]?\s*', re.I), 'port_of_discharge'),
        (re.compile(r'^(?:no\.\s*of\s*containers\s*or\s*packages|no\.\s*of\s*containers|total\s*containers|container\s*summary|container\s*count|containers)\s*[:\-\)]?\s*', re.I), 'container_count'),
        (re.compile(r'^(?:total\s*)?gross\s*(?:weight|wt)(?:\s*\([^\)]*\))?\s*[:\-\)]?\s*', re.I), 'gross_weight_kg'),
    ]

    STOP_HEADERS = re.compile(
        r'^(?:ocean\s*vessel|vessel\s*name|vessel|export\s*carrier|voy\.\s*no|voyage|commodity|description|kinds\s*of\s*packages|hs\s*code|booking\s*ref|booking\s*no|booking\s*reference|oc\s*no|freight|bill\s*of\s*lading\s*no|b/l\s*no|order\s*no|bl\s*instruction|bill\s*of\s*lading|container\s*no\.)\b',
        re.I
    )

    def extract_fields(self, raw_text: str, doc_type_hint: str = "SI") -> Dict[str, Any]:
        result = {
            "shipper": None,
            "consignee": None,
            "notify_party": None,
            "port_of_loading": None,
            "port_of_discharge": None,
            "container_count": None,
            "gross_weight_kg": None,
            "raw_text": raw_text,
            "doc_type": "UNKNOWN",
            "is_unreadable": False,
            "is_wrong_doc_type": False,
            "missing_fields": [],
            "review_reason": None,
            "confidence": 1.0
        }

        # Check for unreadable / damaged / corrupted file indicators
        if not raw_text or len(raw_text.strip()) == 0:
            result["is_unreadable"] = True
            result["review_reason"] = "unreadable"
            result["confidence"] = 0.0
            return result

        raw_lower = raw_text.lower()
        if (
            "[unreadable" in raw_lower or
            "[read_error" in raw_lower or
            "failed to open" in raw_lower or
            "ocr_corrupted" in raw_lower or
            "damaged text" in raw_lower
        ):
            result["is_unreadable"] = True
            result["review_reason"] = "unreadable"
            result["confidence"] = 0.2
            return result

        # Detect Document Type
        first_400 = raw_text[:400].upper()
        if "COMMERCIAL INVOICE" in first_400 or "INVOICE NO." in first_400:
            result["doc_type"] = "COMMERCIAL_INVOICE"
            result["is_wrong_doc_type"] = True
            result["review_reason"] = "wrong_doc_type"
            return result
        elif "PACKING LIST" in first_400:
            result["doc_type"] = "PACKING_LIST"
            result["is_wrong_doc_type"] = True
            result["review_reason"] = "wrong_doc_type"
            return result
        elif "CERTIFICATE OF ORIGIN" in first_400:
            result["doc_type"] = "CERTIFICATE_OF_ORIGIN"
            result["is_wrong_doc_type"] = True
            result["review_reason"] = "wrong_doc_type"
            return result
        elif "BILL OF LADING" in first_400:
            result["doc_type"] = "BILL_OF_LADING"
        elif "SHIPPING INSTRUCTION" in first_400 or "BL INSTRUCTION" in first_400:
            result["doc_type"] = "SHIPPING_INSTRUCTION"
        else:
            result["doc_type"] = "BILL_OF_LADING" if doc_type_hint == "BL" else "SHIPPING_INSTRUCTION"

        # Line-by-line parsing
        lines = raw_text.replace('\r', '').splitlines()
        curr_key = None
        curr_val: List[str] = []

        for line in lines:
            line_s = line.strip()
            if not line_s or line_s.startswith("==="):
                continue

            # Strip Chinese characters for matching headers
            line_ascii = re.sub(r'[\u4e00-\u9fff]+', '', line_s).strip()

            matched_field = None
            rem = None
            for pat, fkey in self.HEADER_MAP:
                m = pat.match(line_ascii)
                if m:
                    matched_field = fkey
                    rem = line_ascii[m.end():].strip()
                    if rem.startswith(":") or rem.startswith("-") or rem.startswith(")"):
                        rem = rem[1:].strip()
                    break

            if matched_field:
                if curr_key:
                    result[curr_key] = self._clean_val(curr_key, ' '.join(curr_val))
                curr_key = matched_field
                curr_val = [rem] if rem else []
            elif self.STOP_HEADERS.match(line_ascii):
                if curr_key:
                    result[curr_key] = self._clean_val(curr_key, ' '.join(curr_val))
                curr_key = None
                curr_val = []
            else:
                if curr_key:
                    curr_val.append(line_s)
                    # Complete single-line fields
                    if curr_key in ['port_of_loading', 'port_of_discharge', 'container_count', 'gross_weight_kg']:
                        result[curr_key] = self._clean_val(curr_key, ' '.join(curr_val))
                        curr_key = None
                        curr_val = []

        if curr_key:
            result[curr_key] = self._clean_val(curr_key, ' '.join(curr_val))

        # Secondary fallback regex for container count & weight if missed
        if result["container_count"] is None:
            m = re.search(r'(?:total\s*containers|container\s*summary|container\s*count|containers|no\.\s*of\s*containers)[^\d\r\n]*(\d+)', raw_text, re.I)
            if m:
                result["container_count"] = int(m.group(1))

        if result["gross_weight_kg"] is None:
            m = re.search(r'(?:total\s*)?gross\s*(?:weight|wt)[^\d\r\n]*([\d\.,]+)\s*(?:kgs?|kg|metric tons?|mt)?', raw_text, re.I)
            if m:
                raw_w = m.group(1).replace(',', '')
                try:
                    num_w = float(raw_w)
                    if "metric ton" in m.group(0).lower() or " mt" in m.group(0).lower():
                        num_w *= 1000.0
                    result["gross_weight_kg"] = round(num_w, 2)
                except ValueError:
                    pass

        # Check for placeholder or blank values (e.g. '____MT', 'TBA')
        for f in ['shipper', 'consignee', 'notify_party', 'port_of_loading', 'port_of_discharge', 'container_count', 'gross_weight_kg']:
            val = result[f]
            if val is None or (isinstance(val, str) and (val.strip() == "" or "____" in val or val.strip().upper() == "TBA")):
                result[f] = None
                result["missing_fields"].append(f)

        if result["missing_fields"]:
            result["review_reason"] = "missing_value"
            result["confidence"] = 0.65

        return result

    def _clean_val(self, field_name: str, val: str) -> Any:
        if not val:
            return None
        val_clean = re.sub(r'^(?:\(pol\)|\(pod\)|pol|pod|load port|port of loading|discharge port|port of discharge)\s*[:\-\)]?\s*', '', val, flags=re.I)
        val_clean = val_clean.replace('|', ' ')
        val_clean = re.sub(r'\s+', ' ', val_clean).strip()

        if not val_clean or val_clean.upper() in ["BLANK", "[BLANK]", "[MISSING]", "N/A", "TBA"] or "____" in val_clean:
            return None

        if field_name == "container_count":
            m = re.search(r'(\d+)', val_clean)
            return int(m.group(1)) if m else None

        if field_name == "gross_weight_kg":
            raw_w = val_clean.replace(',', '').lower()
            m = re.search(r'([\d\.]+)', raw_w)
            if m:
                try:
                    w = float(m.group(1))
                    if "metric ton" in raw_w or " mt" in raw_w:
                        w *= 1000.0
                    return round(w, 2)
                except ValueError:
                    return None
            return None

        return val_clean

extractor = DocumentExtractor()
