"""
DocuMatch LLM Agent Layer (Opt-in).
Configured via DOCUMATCH_LLM_MODE=off|assist (default: off).
Provides schema-validated AI assistance with strict provenance checks and circuit breaker integration.
"""
from backend.services.llm_agent.client import LLMClient, get_llm_client
from backend.services.llm_agent.agent import DocuMatchLLMAgent, llm_agent

__all__ = ["LLMClient", "get_llm_client", "DocuMatchLLMAgent", "llm_agent"]
