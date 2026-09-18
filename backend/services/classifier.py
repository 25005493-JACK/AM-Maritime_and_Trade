import re
from typing import Dict, Any, Tuple

class EmailClassifier:
    """
    Categorizes shipping emails into operational super-categories and specific UI tags.
    Identifies document comparison requests that trigger SI vs BL verification.
    """

    SUPER_CATEGORIES = {
        "BOOKING": "Booking & Scheduling",
        "CONTAINER": "Container & Yard Ops",
        "PORT": "Port & Vessel Ops",
        "DOCUMENTATION": "Documentation (SI & BL)",
        "FINANCE": "Finance & Billing",
        "SPAM": "Spam / General"
    }

    def classify(self, email: Dict[str, Any]) -> Dict[str, Any]:
        subject = email.get("subject", "").lower()
        body = email.get("body", "").lower()
        text = f"{subject} {body}"
        attachments = email.get("attachments", [])

        # Check for Spam first
        if any(w in text for w in ["discount", "stationery", "coupon", "click here", "buy now", "special sale"]):
            return {
                "super_category": self.SUPER_CATEGORIES["SPAM"],
                "ui_tag": "Spam / Promotional Email",
                "is_comparison_request": False,
                "confidence": 0.98,
                "reason": "Contains marketing and promotional keywords"
            }

        # Check for Document Comparison Request
        is_comp_req = False
        has_si = any(att.get("doc_type") == "SI" or "si" in att.get("filename", "").lower() for att in attachments)
        has_bl = any(att.get("doc_type") == "BL" or "bl" in att.get("filename", "").lower() for att in attachments)

        if (has_si and has_bl) or ("draft bl" in text and ("si" in text or "shipping instruction" in text)) or "verification" in text and "draft" in text:
            is_comp_req = True

        if is_comp_req:
            return {
                "super_category": self.SUPER_CATEGORIES["DOCUMENTATION"],
                "ui_tag": "Document Comparison Request",
                "is_comparison_request": True,
                "confidence": 0.96,
                "reason": "Contains SI & draft BL attachments requiring comparison"
            }

        # Documentation (SI & BL) other tags
        if "shipping instruction" in text or "submission of si" in text:
            return {
                "super_category": self.SUPER_CATEGORIES["DOCUMENTATION"],
                "ui_tag": "Submission of Shipping instruction",
                "is_comparison_request": False,
                "confidence": 0.92,
                "reason": "Submission of new Shipping Instruction"
            }
        if "release bill of lading" in text or "print bl" in text:
            return {
                "super_category": self.SUPER_CATEGORIES["DOCUMENTATION"],
                "ui_tag": "Print and release bill of lading to Shipper",
                "is_comparison_request": False,
                "confidence": 0.90,
                "reason": "Bill of Lading printing / release request"
            }

        # Booking & Scheduling
        if "enquiry of sailing schedule" in text or "schedule" in text or "capacity" in text:
            return {
                "super_category": self.SUPER_CATEGORIES["BOOKING"],
                "ui_tag": "Enquiry of sailing schedule and space",
                "is_comparison_request": False,
                "confidence": 0.94,
                "reason": "Inquiry regarding sailing schedules and vessel space"
            }
        if "rates quotation" in text or "freight quote" in text:
            return {
                "super_category": self.SUPER_CATEGORIES["BOOKING"],
                "ui_tag": "Request for rates quotation",
                "is_comparison_request": False,
                "confidence": 0.93,
                "reason": "Rates quotation inquiry"
            }

        # Container & Yard Ops
        if "pick up" in text or "depot" in text or "gate-in" in text and "container" in text:
            return {
                "super_category": self.SUPER_CATEGORIES["CONTAINER"],
                "ui_tag": "Container pick up arrangements/change depot",
                "is_comparison_request": False,
                "confidence": 0.91,
                "reason": "Container pickup or yard depot arrangement"
            }

        # Port & Vessel Ops
        if "arrival notice" in text or "eta" in text or "berth" in text:
            return {
                "super_category": self.SUPER_CATEGORIES["PORT"],
                "ui_tag": "Issue of arrival notice to Consignee or Notify party",
                "is_comparison_request": False,
                "confidence": 0.95,
                "reason": "Vessel arrival notice and port operations update"
            }

        # Finance & Billing
        if "invoice" in text or "payment" in text or "remittance" in text or "billing" in text:
            return {
                "super_category": self.SUPER_CATEGORIES["FINANCE"],
                "ui_tag": "Invoice preparation and collection of payment",
                "is_comparison_request": False,
                "confidence": 0.94,
                "reason": "Freight invoice and payment collection notice"
            }

        # Default fallback category
        return {
            "super_category": self.SUPER_CATEGORIES["DOCUMENTATION"],
            "ui_tag": "General Operations Enquiry",
            "is_comparison_request": False,
            "confidence": 0.70,
            "reason": "General operational message"
        }

classifier = EmailClassifier()
