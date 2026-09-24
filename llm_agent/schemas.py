from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class ClassificationOutput(BaseModel):
    """Schema-validated email classification result."""
    category: Literal["BL_COMPARISON", "SI_REQUEST", "INVOICE_QUERY", "GENERAL", "SPAM"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class FieldExtraction(BaseModel):
    """Schema-validated single field proposal with provenance quote."""
    value: str
    evidence_quote: str
    confidence: float = Field(ge=0.0, le=1.0)

class ExtractFieldsOutput(BaseModel):
    """Schema-validated batch field extractions for null/unmapped fields."""
    fields: Dict[str, FieldExtraction]

class ScanReadOutput(BaseModel):
    """Schema-validated vision pre-read for image-only PDFs."""
    extracted_text: str
    confidence: float = Field(ge=0.0, le=1.0)
    is_image_scan: bool = True
    verification_status: Literal["unverified"] = "unverified"
    notes: str

class MismatchExplanation(BaseModel):
    """Schema-validated advisory discrepancy explanation."""
    field_name: str
    summary: str
    recommended_action: str
    advisory: Literal[True] = True

class DraftReply(BaseModel):
    """Schema-validated advisory draft reply."""
    recipient: str
    subject: str
    body: str
    advisory: Literal[True] = True
