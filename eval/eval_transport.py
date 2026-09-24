"""
Deterministic FakeTransport for offline evaluation benchmark.
Conforms strictly to Pydantic schemas in llm_agent.schemas.
"""
import re
from typing import Any, Type
from pydantic import BaseModel
from llm_agent.schemas import (
    ClassificationOutput,
    ExtractFieldsOutput,
    FieldExtraction,
    ScanReadOutput,
    MismatchExplanation,
    DraftReply,
)
from llm_agent.client import FakeTransport

FIELD_KEYWORDS = {
    "shipper": ["shipper", "exporter", "consignor"],
    "consignee": ["consignee", "receiver", "buyer"],
    "notify_party": ["notify", "notify party"],
    "port_of_loading": ["port of loading", "pol", "loading port"],
    "port_of_discharge": ["port of discharge", "pod", "discharge port"],
    "container_count": ["container count", "total containers", "containers"],
    "gross_weight_kg": ["gross weight", "gross wt", "cargo weight"],
}

def eval_transport_handler(prompt: str, schema: Type[BaseModel]) -> Any:
    schema_name = schema.__name__

    if schema_name == "ClassificationOutput":
        # Extract the email subject and body from the prompt (skip the system header)
        email_content = prompt.split("Subject:")[-1].lower() if "Subject:" in prompt else prompt.lower()
        m_tentative = re.search(r"Rule Engine tentative category was:\s*([A-Z_]+)", prompt)
        tentative = m_tentative.group(1) if m_tentative else "GENERAL"

        # Check for specific strong indicators in the email content only
        if any(w in email_content for w in ["weird trick", "bitcoin investment", "guaranteed 300%", "viagra"]):
            cat = "SPAM"
        elif any(w in email_content for w in ["cancel invoice", "local charges", "telex release charges", "debit note"]) and tentative != "BL_COMPARISON":
            cat = "INVOICE_QUERY"
        elif any(w in email_content for w in ["request si", "submit si", "please find shipping instruction"]) and tentative != "BL_COMPARISON":
            cat = "SI_REQUEST"
        else:
            cat = tentative

        return {
            "category": cat,
            "confidence": 0.95,
            "reasoning": f"Assistant verified {cat} category from context and document signals."
        }

    elif schema_name == "ExtractFieldsOutput":
        fields_result = {}
        # Parse target fields from prompt
        m_targets = re.search(r"Only extract these target fields:\s*\[(.*?)\]", prompt)
        targets = []
        if m_targets:
            targets = [t.strip().strip("'\"") for t in m_targets.group(1).split(",") if t.strip()]

        # Parse snippet from prompt
        snippet_part = prompt.split("Document text snippet:\n")[-1]
        lines = snippet_part.splitlines()

        for target in targets:
            keywords = FIELD_KEYWORDS.get(target, [target.replace("_", " ")])
            found = False
            for line in lines:
                l_strip = line.strip()
                if not l_strip:
                    continue
                for kw in keywords:
                    if kw in l_strip.lower():
                        # Extract value after separator
                        val = ""
                        for sep in (":", "-", "|"):
                            if sep in l_strip:
                                val = l_strip.split(sep, 1)[1].strip()
                                break
                        if not val and len(lines) > lines.index(line) + 1:
                            val = lines[lines.index(line) + 1].strip()
                        
                        if val:
                            fields_result[target] = {
                                "value": val,
                                "evidence_quote": l_strip,
                                "confidence": 0.95
                            }
                            found = True
                            break
                if found:
                    break

        return {"fields": fields_result}

    elif schema_name == "ScanReadOutput":
        return {
            "extracted_text": "Scanned document text pre-read preview",
            "confidence": 0.75,
            "is_image_scan": True,
            "verification_status": "unverified",
            "notes": "Offline evaluation scan pre-read. Routes to NEEDS_REVIEW."
        }

    elif schema_name == "MismatchExplanation":
        return {
            "field_name": "evaluated_field",
            "summary": "Discrepancy identified between submitted documents.",
            "recommended_action": "Request updated documentation from counterparty.",
            "advisory": True
        }

    elif schema_name == "DraftReply":
        return {
            "recipient": "operations@shipping.com",
            "subject": "Re: Shipping Document Verification Discrepancy",
            "body": "Dear Partner,\n\nPlease clarify the discrepancies flagged during verification.\n\nBest regards,\nOps Team",
            "advisory": True
        }

    return {}


def create_eval_transport() -> FakeTransport:
    return FakeTransport(eval_transport_handler)
