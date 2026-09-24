"""
Provider-agnostic LLM client with strict Pydantic schema enforcement,
timeouts, retries, and offline fake-transport support.
"""
import os
import json
import re
import time
import urllib.request
import urllib.error
from typing import Any, Callable, Dict, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

DEFAULT_TIMEOUT = 10
DEFAULT_RETRIES = 2
DEFAULT_MODEL = "gpt-4o-mini"


class LLMClientError(Exception):
    """Base exception for LLM client failures."""
    pass


class LLMDisabledError(LLMClientError):
    """Raised when LLM calls are attempted while the client or mode is disabled."""
    pass


class LLMSchemaValidationError(LLMClientError):
    """Raised when LLM output violates the expected Pydantic schema."""
    pass


class FakeTransport:
    """
    Hook for offline testing and deterministic simulation.
    Takes a handler function: (prompt: str, schema: Type[BaseModel]) -> dict | str
    """
    def __init__(self, handler: Callable[[str, Type[BaseModel]], Any]):
        self.handler = handler
        self.call_count = 0
        self.last_prompt: Optional[str] = None
        self.history = []

    def __call__(self, prompt: str, schema: Type[BaseModel]) -> Any:
        self.call_count += 1
        self.last_prompt = prompt
        res = self.handler(prompt, schema)
        self.history.append({"prompt": prompt, "schema": schema.__name__, "response": res})
        return res


class LLMClient:
    """
    Provider-agnostic client for DocuMatch LLM Agent Layer.
    Only enabled when DOCUMATCH_LLM_MODE=assist and credentials or fake transport are present.
    """

    def __init__(
        self,
        mode: Optional[str] = None,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        retries: Optional[int] = None,
        transport: Optional[Callable[[str, Type[BaseModel]], Any]] = None,
    ):
        self._explicit_mode = mode.strip().lower() if mode is not None else None
        self._mode = (mode or os.environ.get("DOCUMATCH_LLM_MODE", "off")).strip().lower()
        self._provider = (provider or os.environ.get("DOCUMATCH_LLM_PROVIDER", "openai")).strip().lower()
        self._api_key = api_key or os.environ.get("DOCUMATCH_LLM_API_KEY", "").strip()
        self._model = model or os.environ.get("DOCUMATCH_LLM_MODEL", DEFAULT_MODEL)
        self._timeout = timeout if timeout is not None else int(os.environ.get("DOCUMATCH_LLM_TIMEOUT", str(DEFAULT_TIMEOUT)))
        self._retries = retries if retries is not None else int(os.environ.get("DOCUMATCH_LLM_RETRIES", str(DEFAULT_RETRIES)))
        self._transport = transport
        self.total_tokens_spent = 0
        self.total_calls = 0

    @property
    def mode(self) -> str:
        if self._explicit_mode is not None:
            return self._explicit_mode
        return os.environ.get("DOCUMATCH_LLM_MODE", "off").strip().lower()

    @property
    def is_enabled(self) -> bool:
        """True only if mode is 'assist' AND (api_key exists or a custom transport is active)."""
        current_mode = self.mode
        if current_mode != "assist":
            return False
        if self._transport is not None:
            return True
        key = self._api_key or os.environ.get("DOCUMATCH_LLM_API_KEY", "").strip()
        return bool(key)

    def set_transport(self, transport: Optional[Callable[[str, Type[BaseModel]], Any]]) -> None:
        """Inject or clear a test transport."""
        self._transport = transport

    def generate_json(self, prompt: str, schema: Type[T]) -> T:
        """
        Invokes LLM with system prompt + user prompt requesting strict JSON adhering to `schema`.
        Validates output using Pydantic, retrying on malformed outputs up to `retries` times.
        Rejects anything malformed.
        """
        if not self.is_enabled:
            raise LLMDisabledError(
                f"LLM agent layer is disabled (mode={self.mode}, transport={self._transport is not None}). "
                "Set DOCUMATCH_LLM_MODE=assist and configure an API key or fake transport."
            )

        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        full_prompt = (
            f"You are a specialized maritime shipping verification assistant.\n"
            f"You MUST respond ONLY with valid, raw JSON conforming to this JSON Schema:\n"
            f"{schema_json}\n\n"
            f"Do not include markdown fences, code blocks, or extraneous conversational text.\n"
            f"Task Prompt:\n{prompt}"
        )

        last_error = None
        for attempt in range(1 + self._retries):
            self.total_calls += 1
            try:
                raw_response = self._execute_request(full_prompt, schema)
                validated = self._parse_and_validate(raw_response, schema)
                return validated
            except (ValidationError, json.JSONDecodeError, ValueError) as ex:
                last_error = LLMSchemaValidationError(f"Attempt {attempt + 1}: Malformed response failed schema validation: {ex}")
            except Exception as ex:
                last_error = LLMClientError(f"Attempt {attempt + 1}: Request error: {ex}")

        raise last_error or LLMClientError("Failed to generate valid JSON after retries.")

    def _execute_request(self, full_prompt: str, schema: Type[BaseModel]) -> str:
        """Executes via injected transport or HTTP API."""
        if self._transport is not None:
            res = self._transport(full_prompt, schema)
            if isinstance(res, dict):
                return json.dumps(res)
            return str(res)

        key = self._api_key or os.environ.get("DOCUMATCH_LLM_API_KEY", "").strip()
        if not key:
            raise LLMDisabledError("No API key configured.")

        # Real HTTP call (OpenAI-compatible format)
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            usage = body.get("usage", {})
            self.total_tokens_spent += usage.get("total_tokens", 0)
            return body["choices"][0]["message"]["content"]

    def _parse_and_validate(self, raw_text: str, schema: Type[T]) -> T:
        """Parses JSON and enforces Pydantic schema validation."""
        text = raw_text.strip()
        # Clean potential markdown fences if returned
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text, flags=re.I)
            text = re.sub(r"\n?```$", "", text)
            text = text.strip()

        # Find first { ... } or [ ... ]
        m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if m:
            text = m.group(0)

        data = json.loads(text)
        return schema.model_validate(data)


# Global singleton client
llm_client = LLMClient()
