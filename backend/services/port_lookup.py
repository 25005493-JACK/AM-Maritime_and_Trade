import os
import csv
import re
from typing import Dict, Any, Optional, Tuple

class PortLookup:
    """
    Normalizes shipping port descriptions and resolves them to UN/LOCODE standard codes.
    Loads data/unlocode.csv and provides code-first comparison with fallback auditing.
    """

    KNOWN_COUNTRIES = {
        "SINGAPORE", "INDONESIA", "CHINA", "MALAYSIA", "US", "USA", "UNITED STATES",
        "SOUTH KOREA", "KOREA", "INDIA", "UAE", "UNITED ARAB EMIRATES", "POLAND",
        "VIETNAM", "KENYA", "TURKEY", "LITHUANIA", "PAKISTAN", "PHILIPPINES",
        "GUINEA", "PERU", "JORDAN", "SLOVENIA", "AUSTRALIA", "CHILE", "NETHERLANDS",
        "GERMANY", "FRANCE", "BELGIUM", "UNITED KINGDOM", "UK", "THAILAND", "MYANMAR",
        "EGYPT", "SOUTH AFRICA", "BRAZIL", "SAUDI ARABIA", "ISRAEL"
    }

    ALIAS_MAP = {
        "singapore": "SGSIN",
        "buatan": "IDBUA",
        "busan": "KRPUS",
        "rotterdam": "NLRTM",
        "new york": "USNYC",
        "nantong": "CNNTG",
        "shanghai": "CNSHA",
        "port klang": "MYPKG",
        "port klang westport": "MYPKG",
        "westport": "MYPKG",
        "jebel ali": "AEJEA",
        "nhava sheva": "INNSA",
        "koper": "SIKOP",
        "aqaba": "JOAQB",
        "apapa": "NGAPP",
        "baltimore": "USBAL",
        "brisbane": "AUBNE",
        "callao": "PECLL",
        "cebu": "PHCEB",
        "conakry": "GNCKY",
        "fremantle": "AUFRE",
        "gdansk": "PLGDN",
        "hochiminh city": "VNSGN",
        "ho chi minh city": "VNSGN",
        "ho chi minh": "VNSGN",
        "saigon": "VNSGN",
        "houston": "USHOU",
        "karachi": "PKKHI",
        "klaipeda": "LTKLJ",
        "mersin": "TRMER",
        "mombasa": "KEMBA",
        "long beach": "USLGB",
        "pyeongtaek": "KRPTK",
        "savannah": "USSAV",
        "ashdod": "ILASH",
        "valparaiso": "CLVAP",
        "yantian": "CNYTN",
        "qingdao": "CNQDG",
        "ningbo": "CNNGB",
        "yangon": "MMRGN",
        "hamburg": "DEHAM",
        "le havre": "FRLEH",
        "antwerp": "BEANR"
    }

    def __init__(self, csv_path: Optional[str] = None):
        self.by_code: Dict[str, Dict[str, str]] = {}
        self.by_name: Dict[str, str] = {}
        self.csv_path = csv_path or self._find_csv_path()
        self._load_table()

    def _find_csv_path(self) -> str:
        candidates = [
            os.path.join(os.getcwd(), "data", "unlocode.csv"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "unlocode.csv"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "unlocode.csv"),
            "data/unlocode.csv"
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return "data/unlocode.csv"

    def _load_table(self):
        if not os.path.exists(self.csv_path):
            return

        with open(self.csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get("code", "").strip().upper()
                name = row.get("name", "").strip()
                country = row.get("country", "").strip().upper()
                if code and name:
                    self.by_code[code] = {"code": code, "name": name, "country": country}
                    norm_name = self.normalize_text(name)
                    self.by_name[norm_name] = code

    def normalize_text(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r'[\.,\-\/\\_\(\)\:\;]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def resolve_port_code(self, port_str: Any) -> Optional[str]:
        if not port_str:
            return None
        raw = str(port_str).strip()
        if not raw or raw.upper() in ("N/A", "TBA", "BLANK", "[BLANK]"):
            return None

        # 1. Check parenthetical UN/LOCODE e.g. "SINGAPORE (SGSIN)" or "BALTIMORE, US (USBAL)"
        m_code = re.search(r'\(([A-Z]{2}[A-Z0-9]{3})\)', raw)
        if m_code:
            code_cand = m_code.group(1).upper()
            return code_cand

        # 2. Check if the string itself is just a UN/LOCODE
        raw_clean = re.sub(r'[^A-Za-z0-9]', '', raw).upper()
        if len(raw_clean) == 5 and (raw_clean in self.by_code or raw_clean in self.ALIAS_MAP.values()):
            return raw_clean

        # 3. Strip parenthetical expressions
        stripped = re.sub(r'\(.*?\)', '', raw).strip()

        # Split city from country (e.g. "BUATAN, INDONESIA" -> city="BUATAN")
        parts = [p.strip() for p in stripped.split(',') if p.strip()]
        city_part = parts[0] if parts else stripped

        norm_city = self.normalize_text(city_part)
        norm_full = self.normalize_text(stripped)

        # Check in alias map
        if norm_city in self.ALIAS_MAP:
            return self.ALIAS_MAP[norm_city]
        if norm_full in self.ALIAS_MAP:
            return self.ALIAS_MAP[norm_full]

        # Check by_name from CSV
        if norm_city in self.by_name:
            return self.by_name[norm_city]
        if norm_full in self.by_name:
            return self.by_name[norm_full]

        # Check partial word matches in alias map
        for k, code in self.ALIAS_MAP.items():
            if k in norm_city or k in norm_full:
                return code

        return None

    def compare_ports(self, si_val: Any, bl_val: Any) -> Tuple[bool, Dict[str, Any]]:
        """
        Compares SI and BL port fields.
        Compares by resolved UN/LOCODE code first.
        Falls back to normalized string comparison if either side fails to resolve,
        and logs the fallback in the returned audit dict.
        """
        if si_val is None or bl_val is None:
            return (False, {
                "method": "missing_value",
                "si_code": None,
                "bl_code": None,
                "fallback_to_string": False,
                "is_match": False
            })

        si_code = self.resolve_port_code(si_val)
        bl_code = self.resolve_port_code(bl_val)

        if si_code is not None and bl_code is not None:
            is_match = (si_code == bl_code)
            return (is_match, {
                "method": "unlocode",
                "si_code": si_code,
                "bl_code": bl_code,
                "fallback_to_string": False,
                "is_match": is_match
            })

        # Fallback to normalized string comparison
        norm_si = self.normalize_text(str(si_val))
        norm_bl = self.normalize_text(str(bl_val))

        is_match = (norm_si == norm_bl) or (norm_si in norm_bl) or (norm_bl in norm_si)

        audit_entry = {
            "method": "normalized_string_fallback",
            "si_code": si_code,
            "bl_code": bl_code,
            "fallback_to_string": True,
            "is_match": is_match,
            "audit_warning": f"UN/LOCODE unresolved for SI='{si_val}' (code={si_code}) or BL='{bl_val}' (code={bl_code}); fell back to normalized string comparison."
        }

        return (is_match, audit_entry)

port_lookup = PortLookup()
