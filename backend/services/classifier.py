import re
from typing import Dict, Any, List

class EmailClassifier:
    """
    Categorizes emails into the 5 standard hackathon categories:
    - BL_COMPARISON
    - SI_REQUEST
    - INVOICE_QUERY
    - GENERAL
    - SPAM
    Also enriches with operational UI tags and super categories for the management interface.
    """

    CATEGORIES = {
        "BL_COMPARISON": "BL_COMPARISON",
        "SI_REQUEST": "SI_REQUEST",
        "INVOICE_QUERY": "INVOICE_QUERY",
        "GENERAL": "GENERAL",
        "SPAM": "SPAM"
    }

    SUPER_CATEGORIES = {
        "BL_COMPARISON": "Documentation (SI & BL)",
        "SI_REQUEST": "Documentation (SI & BL)",
        "INVOICE_QUERY": "Finance & Billing",
        "GENERAL": "Operations & Scheduling",
        "SPAM": "Spam / Quarantine"
    }

    def classify(self, email: Dict[str, Any]) -> Dict[str, Any]:
        subject = email.get("subject", "")
        body = email.get("body", "")
        subject_lower = subject.lower()
        body_lower = body.lower()
        text = f"{subject_lower} {body_lower}"
        
        raw_atts = email.get("attachments", [])
        att_paths: List[str] = []
        for a in raw_atts:
            if isinstance(a, dict):
                att_paths.append(a.get("path") or a.get("filename") or "")
            elif isinstance(a, str):
                att_paths.append(a)

        # 1. SPAM & PHISHING CHECK
        spam_patterns = [
            r'\bweird trick\b',
            r'\bbitcoin investment\b',
            r'\bguaranteed 300% returns\b',
            r'\bexclusive offer:\s*90%\s*off\b',
            r'\burgent:\s*your email storage is full\b',
            r'\bupdate your account to avoid suspension\b',
            r'\burgent business proposal\b',
            r'\bbank officer\b.*(?:\$|million|bank details)',
            r'\bclick here to claim\b',
            r'\bviagra\b',
            r'\bdiscount on office stationery\b',
            r'\bspecial sale\b'
        ]
        for pat in spam_patterns:
            if re.search(pat, text, re.I):
                return {
                    "category": "SPAM",
                    "super_category": self.SUPER_CATEGORIES["SPAM"],
                    "ui_tag": "Spam / Phishing Alert",
                    "is_comparison_request": False,
                    "confidence": 0.99,
                    "reason": "Contains recognized spam or phishing signatures"
                }

        # 2. BL_COMPARISON CHECK
        has_si = any(
            "_si." in a.lower() or a.lower().endswith("si.txt") or "/si." in a.lower()
            for a in att_paths
        )
        has_bl = any(
            "_bl." in a.lower() or a.lower().endswith("bl.txt") or "/bl." in a.lower()
            for a in att_paths
        )
        # Also check dict attachments doc_type if passed
        for raw_a in raw_atts:
            if isinstance(raw_a, dict):
                dt = raw_a.get("doc_type", "").upper()
                fn = (raw_a.get("filename") or "").lower()
                if dt == "SI" or fn.startswith("si.") or fn.endswith("_si.txt") or "si" in fn:
                    has_si = True
                if dt == "BL" or fn.startswith("bl.") or fn.endswith("_bl.txt") or "bl" in fn:
                    has_bl = True

        explicit_comp_request = bool(
            re.search(r'(?:compare|cross\s*check|verify|check)\s+(?:the\s+)?(?:si|shipping\s+instruction)\s+and\s+(?:the\s+)?(?:draft\s+)?bl', text, re.I) or
            re.search(r'compare (?:the )?shipping instruction and (?:the )?draft bl', text, re.I) or
            re.search(r'verify (?:the )?bl matches (?:the )?si', text, re.I) or
            re.search(r'check the bl against (?:the )?si', text, re.I) or
            ("draft bl" in text and ("si " in text or "shipping instruction" in text) and any(w in text for w in ["check", "verify", "compare", "confirmation"]))
        )

        is_confirm_docs_subject = (
            "to confirm docs" in subject_lower or
            "request bl draft" in subject_lower or
            "draft bl" in subject_lower or
            "draft_bl" in subject_lower or
            "check and confirm" in body_lower or
            "please check and confirm" in body_lower or
            "verify details" in body_lower
        )

        if (has_si and has_bl) or explicit_comp_request:
            return {
                "category": "BL_COMPARISON",
                "super_category": self.SUPER_CATEGORIES["BL_COMPARISON"],
                "ui_tag": "Document Comparison Request",
                "is_comparison_request": True,
                "confidence": 0.98,
                "reason": "Email requests comparison of Shipping Instruction against draft Bill of Lading"
            }

        if len(att_paths) >= 1 and is_confirm_docs_subject and (has_si or has_bl):
            return {
                "category": "BL_COMPARISON",
                "super_category": self.SUPER_CATEGORIES["BL_COMPARISON"],
                "ui_tag": "Document Comparison Request",
                "is_comparison_request": True,
                "confidence": 0.95,
                "reason": "Email contains shipment document attachment requiring BL comparison"
            }

        # 3. SI_REQUEST CHECK (Checked before invoice keywords to prevent footer boilerplate false triggers)
        is_si_sub = (
            "request si" in subject_lower or "si needed" in subject_lower or "submit si" in subject_lower or
            "cust si" in subject_lower or subject_lower.strip().startswith("si -") or " si - " in subject_lower or
            "submission of si" in subject_lower or "re_ si -" in subject_lower
        )
        is_si_body = (
            "please find shipping instruction" in body_lower or
            "please send si" in body_lower or
            "please provide si" in body_lower or
            "submit si & aed" in body_lower or
            "find shipping instruction" in body_lower
        )
        if is_si_sub or is_si_body:
            return {
                "category": "SI_REQUEST",
                "super_category": self.SUPER_CATEGORIES["SI_REQUEST"],
                "ui_tag": "Shipping Instruction Request",
                "is_comparison_request": False,
                "confidence": 0.95,
                "reason": "Inbound request for Shipping Instruction submission or preparation"
            }

        # 4. INVOICE_QUERY CHECK
        invoice_sub = any(w in subject_lower for w in [
            "charges", "freight", "invoice", "billing", "payment", "debit note",
            "credit note", "remittance", "statement of account", "d & d", "demurrage", "detention"
        ])
        invoice_body = any(w in body_lower for w in [
            "local charges", "telex release charges", "total freight", "d & d charges",
            "cancel invoice", "freight invoice", "payment confirmation", "statement of account",
            "billing process completed"
        ])
        if invoice_sub or invoice_body:
            return {
                "category": "INVOICE_QUERY",
                "super_category": self.SUPER_CATEGORIES["INVOICE_QUERY"],
                "ui_tag": "Invoice & Billing Query",
                "is_comparison_request": False,
                "confidence": 0.94,
                "reason": "Freight billing, charge dispute, or invoice payment enquiry"
            }

        # 5. GENERAL (Operations & Schedules)
        return {
            "category": "GENERAL",
            "super_category": self.SUPER_CATEGORIES["GENERAL"],
            "ui_tag": "General Operations & Schedule",
            "is_comparison_request": False,
            "confidence": 0.88,
            "reason": "General operational notice, schedule enquiry, or status broadcast"
        }

classifier = EmailClassifier()
