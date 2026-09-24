"""
DocuMatch LLM Agent Layer (Opt-in).

Flag: DOCUMATCH_LLM_MODE=off|assist (default off)

Principles:
- Rules run first; LLM is called ONLY when needed (low rule confidence, null fields).
- Strict Pydantic schemas enforce type safety and reject malformed outputs.
- Phase 2 strict verbatim provenance, UN/LOCODE, and ISO 6346 validation.
- Failed extractions increment the circuit breaker.
- LLM NEVER overrides valid rule-extracted values and NEVER issues an OK verdict.
"""

from llm_agent.client import (
    LLMClient,
    FakeTransport,
    LLMClientError,
    LLMDisabledError,
    LLMSchemaValidationError,
    llm_client,
)
from llm_agent.schemas import (
    ClassificationOutput,
    FieldExtraction,
    ExtractFieldsOutput,
    ScanReadOutput,
    MismatchExplanation,
    DraftReply,
)
from llm_agent.validators import (
    check_verbatim_provenance,
    validate_unlocode,
    validate_iso6346,
    calculate_iso6346_check_digit,
)
from llm_agent.tasks import (
    classify_email,
    extract_fields,
    read_scan,
    explain_mismatch,
    draft_reply,
)

def is_llm_available() -> bool:
    """Helper to check if LLM agent layer is active and configured."""
    return llm_client.is_enabled

__all__ = [
    "LLMClient",
    "FakeTransport",
    "LLMClientError",
    "LLMDisabledError",
    "LLMSchemaValidationError",
    "llm_client",
    "is_llm_available",
    "ClassificationOutput",
    "FieldExtraction",
    "ExtractFieldsOutput",
    "ScanReadOutput",
    "MismatchExplanation",
    "DraftReply",
    "check_verbatim_provenance",
    "validate_unlocode",
    "validate_iso6346",
    "calculate_iso6346_check_digit",
    "classify_email",
    "extract_fields",
    "read_scan",
    "explain_mismatch",
    "draft_reply",
]
