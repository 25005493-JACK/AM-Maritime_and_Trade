import re
from typing import Dict, Any, Optional, List

class DocumentExtractor:
    """
    Extracts the 7 required shipment fields from SI and draft BL document text.
    Handles field aliases, string normalization, weight conversion, and readability scoring.
    """

    PORT_ALIASES = {
        "load_port": ["port of loading", "load port", "pol", "port of load", "place of loading"],
        "discharge_port": ["port of discharge", "discharge port", "pod", "port of unloading", "place of discharge"]
    }

    def extract_fields(self, raw_text: str, doc_type: str = "SI") -> Dict[str, Any]:
        result = {
            "shipper": None,
            "consignee": None,
            "notify_party": None,
            "port_of_loading": None,
            "port_of_discharge": None,
            "container_count": None,
            "gross_weight_kg": None,
            "raw_text": raw_text,
            "confidence": 1.0,
            "unreadable_reasons": []
        }

        # Check for OCR corruption or unreadable text warnings
        if "[error:" in raw_text.lower() or "[ocr scan result" in raw_text.lower() or "illegible" in raw_text.lower():
            result["confidence"] = 0.40
            result["unreadable_reasons"].append("OCR quality degrade / damaged text stream detected")

        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

        for line in lines:
            line_lower = line.lower()

            # 1. SHIPPER
            if not result["shipper"]:
                if line_lower.startswith("shipper:") or line_lower.startswith("shipper ") or "shipper name:" in line_lower:
                    val = line.split(":", 1)[-1].strip() if ":" in line else line[7:].strip()
                    cleaned = self._clean_string(val)
                    if cleaned is None and val:
                        result["unreadable_reasons"].append("Shipper field is blank/missing in document")
                        result["confidence"] = min(result["confidence"], 0.60)
                    result["shipper"] = cleaned

            # 2. CONSIGNEE
            if not result["consignee"]:
                if line_lower.startswith("consignee:") or line_lower.startswith("consignee ") or "consignee name:" in line_lower:
                    val = line.split(":", 1)[-1].strip() if ":" in line else line[10:].strip()
                    cleaned = self._clean_string(val)
                    if cleaned is None and val:
                        result["unreadable_reasons"].append("Consignee field is blank/missing in document")
                        result["confidence"] = min(result["confidence"], 0.60)
                    result["consignee"] = cleaned

            # 3. NOTIFY PARTY
            if not result["notify_party"]:
                if "notify party:" in line_lower or "notify:" in line_lower or line_lower.startswith("notify "):
                    val = line.split(":", 1)[-1].strip() if ":" in line else line[6:].strip()
                    cleaned = self._clean_string(val)
                    if cleaned is None and val:
                        result["unreadable_reasons"].append("Notify party field is blank/missing in document")
                        result["confidence"] = min(result["confidence"], 0.60)
                    result["notify_party"] = cleaned

            # 4. PORT OF LOADING
            if not result["port_of_loading"]:
                for alias in self.PORT_ALIASES["load_port"]:
                    if alias in line_lower:
                        val = line.split(":", 1)[-1].strip() if ":" in line else line
                        cleaned_port = self._normalize_port(val)
                        if cleaned_port is None and val:
                            result["unreadable_reasons"].append("Port of loading is blank/missing in document")
                            result["confidence"] = min(result["confidence"], 0.60)
                        result["port_of_loading"] = cleaned_port
                        break

            # 5. PORT OF DISCHARGE
            if not result["port_of_discharge"]:
                for alias in self.PORT_ALIASES["discharge_port"]:
                    if alias in line_lower:
                        val = line.split(":", 1)[-1].strip() if ":" in line else line
                        cleaned_port = self._normalize_port(val)
                        if cleaned_port is None and val:
                            result["unreadable_reasons"].append("Port of discharge is blank/missing in document")
                            result["confidence"] = min(result["confidence"], 0.60)
                        result["port_of_discharge"] = cleaned_port
                        break

            # 6. CONTAINER COUNT
            if result["container_count"] is None:
                if "container count:" in line_lower or "total containers:" in line_lower or "container summary:" in line_lower or "containers" in line_lower:
                    match = re.search(r'(\d+)\s*(?:x\s*40|\s*containers|\s*cntr)', line, re.IGNORECASE)
                    if match:
                        result["container_count"] = int(match.group(1))

            # 7. GROSS WEIGHT KG
            if result["gross_weight_kg"] is None:
                if "gross weight" in line_lower or "weight:" in line_lower:
                    if "[error:" in line_lower or "damaged" in line_lower:
                        result["gross_weight_kg"] = None
                        if "Gross weight corrupted / illegible OCR text" not in result["unreadable_reasons"]:
                            result["unreadable_reasons"].append("Gross weight corrupted / illegible OCR text")
                        result["confidence"] = min(result["confidence"], 0.35)
                    else:
                        weight_val = self._parse_weight_kg(line)
                        if weight_val is not None:
                            result["gross_weight_kg"] = weight_val

        # Fallback regex search for container count & gross weight if not matched line-by-line
        if result["container_count"] is None:
            m = re.search(r'(?:containers?|cntrs?):\s*(\d+)', raw_text, re.IGNORECASE)
            if m:
                result["container_count"] = int(m.group(1))
            else:
                m2 = re.search(r'(\d+)\s*(?:containers|cntr)', raw_text, re.IGNORECASE)
                if m2:
                    result["container_count"] = int(m2.group(1))

        if result["gross_weight_kg"] is None and "Gross weight corrupted / illegible OCR text" not in result["unreadable_reasons"]:
            weight_val = self._parse_weight_kg(raw_text)
            if weight_val is not None:
                result["gross_weight_kg"] = weight_val

        return result

    def _clean_string(self, text: str) -> Optional[str]:
        text = re.sub(r'\s+', ' ', text).strip()
        text_lower = text.lower()
        if not text or "[not specified" in text_lower or "blank" in text_lower or "[error:" in text_lower or "illegible" in text_lower or "[missing]" in text_lower:
            return None
        return text

    def _normalize_port(self, text: str) -> Optional[str]:
        text = re.sub(r'^(?:port of loading|load port|pol|port of load|place of loading|port of discharge|discharge port|pod|port of unloading|place of discharge):\s*', '', text, flags=re.IGNORECASE)
        return self._clean_string(text)

    def _parse_weight_kg(self, text: str) -> Optional[float]:
        # Matches patterns like 22000 kg, 22,000.00 kg, 22.0 Metric Tons
        mt_match = re.search(r'([\d\.,]+)\s*(?:metric tons?|mt)', text, re.IGNORECASE)
        if mt_match:
            try:
                num = float(mt_match.group(1).replace(",", ""))
                return round(num * 1000.0, 2)
            except ValueError:
                pass

        kg_match = re.search(r'([\d\.,]+)\s*(?:kg|kilograms?|kgs)', text, re.IGNORECASE)
        if kg_match:
            try:
                num = float(kg_match.group(1).replace(",", ""))
                return round(num, 2)
            except ValueError:
                pass
        return None

extractor = DocumentExtractor()

