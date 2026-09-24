"""
Pydantic schemas for the LLM Agent layer.
Enforces strict structural validation on every model output.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class ClassificationResult(BaseModel):
    category: str = Field(description="Category of the maritime email (e.g. BL_COMPARISON, SI_REQUEST, INVOICE_QUERY, GENERAL, SPAM)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Brief justification grounded in email subject and content")

class ExtractedFieldEvidence(BaseModel):
    value: str = Field(description="Extracted field value")
    evidence_quote: str = Field(description="Exact verbatim substring quoted directly from source text")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in extraction")

class FieldExtractionResult(BaseModel):
    fields: Dict[str, ExtractedFieldEvidence] = Field(
        default_factory=dict,
        description="Map of field_key to extracted evidence"
    )

class ScanReadResult(BaseModel):
    raw_text: str = Field(description="Text read from scanned visual PDF")
    is_scanned: bool = Field(default=True, description="Always true for scan pre-read")
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    status: str = Field(default="unverified", description="Must remain 'unverified' so document routes to human review")
    notes: str = Field(default="Visual OCR pre-read; requires human inspection")

class MismatchExplanation(BaseModel):
    explanation: str = Field(description="Advisory explanation of discrepancies between SI and BL")
    risk_level: str = Field(description="LOW, MEDIUM, or HIGH risk assessment")
    key_discrepancies: List[str] = Field(default_factory=list, description="List of fields causing the discrepancy")

class DraftReply(BaseModel):
    subject: str = Field(description="Subject line for email response")
    recipient: str = Field(description="Recipient address")
    body: str = Field(description="Advisory draft email body resolving or inquiring about the discrepancy")
