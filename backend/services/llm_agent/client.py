"""
Provider-agnostic HTTP client for LLM Agent.
Configured via environment variables with timeouts, retries, and offline-safe fallback.
"""
import os
import json
import time
from typing import Dict, Any, Optional, Callable
import httpx

DEFAULT_MODE = os.environ.get("DOCUMATCH_LLM_MODE", "off").lower()
DEFAULT_PROVIDER = os.environ.get("DOCUMATCH_LLM_PROVIDER", "openai").lower()
DEFAULT_BASE_URL = os.environ.get("DOCUMATCH_LLM_BASE_URL", "https://api.openai.com/v1")
DEFAULT_MODEL = os.environ.get("DOCUMATCH_LLM_MODEL", "gpt-4o-mini")
DEFAULT_TIMEOUT = float(os.environ.get("DOCUMATCH_LLM_TIMEOUT", "15.0"))
DEFAULT_RETRIES = int(os.environ.get("DOCUMATCH_LLM_MAX_RETRIES", "3"))

def get_api_key() -> str:
    return (
        os.environ.get("DOCUMATCH_LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or ""
    )

class LLMClient:
    def __init__(
        self,
        mode: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        mock_handler: Optional[Callable[[str, str], Dict[str, Any]]] = None,
    ):
        self.mode = (mode or os.environ.get("DOCUMATCH_LLM_MODE", DEFAULT_MODE)).lower()
        self.api_key = api_key if api_key is not None else get_api_key()
        self.base_url = (base_url or os.environ.get("DOCUMATCH_LLM_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.model = model or os.environ.get("DOCUMATCH_LLM_MODEL", DEFAULT_MODEL)
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.max_retries = max_retries or DEFAULT_RETRIES
        self.mock_handler = mock_handler

    def is_enabled(self) -> bool:
        """Returns True only when explicitly set to 'assist' and key is present (or mock active)."""
        if self.mock_handler is not None:
            return self.mode == "assist"
        return self.mode == "assist" and bool(self.api_key.strip())

    def status(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "enabled": self.is_enabled(),
            "has_api_key": bool(self.api_key.strip()) or (self.mock_handler is not None),
            "model": self.model,
            "base_url": self.base_url,
            "timeout_seconds": self.timeout,
        }

    def generate_json(self, system_prompt: str, user_prompt: str) -> Optional[Dict[str, Any]]:
        """Call the provider endpoint and return parsed JSON."""
        if not self.is_enabled():
            return None

        # If a mock transport is registered (e.g. for deterministic unit testing), use it
        if self.mock_handler:
            return self.mock_handler(system_prompt, user_prompt)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        url = f"{self.base_url}/chat/completions"

        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_content = data["choices"][0]["message"]["content"]
                        return json.loads(raw_content)
                    elif resp.status_code in (429, 500, 502, 503, 504):
                        time.sleep(0.5 * (2 ** (attempt - 1)))
                        continue
                    else:
                        print(f"[LLM Client] Error response: {resp.status_code} - {resp.text}")
                        return None
            except (httpx.TimeoutException, httpx.NetworkError) as ex:
                if attempt == self.max_retries:
                    print(f"[LLM Client] Retries exhausted: {ex}")
                    return None
                time.sleep(0.5 * (2 ** (attempt - 1)))
            except Exception as e:
                print(f"[LLM Client] Unexpected error: {e}")
                return None

        return None

_global_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    global _global_client
    if _global_client is None:
        _global_client = LLMClient()
    return _global_client
