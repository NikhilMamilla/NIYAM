"""HTTP LLM providers on plain httpx (no SDK dependency)."""

import logging
import time
from collections.abc import Callable

import httpx

from app.llm.base import LLMError, LLMResponse, Message

log = logging.getLogger(__name__)
RETRYABLE_STATUS = {429, 500, 502, 503, 504, 529}
MAX_BACKOFF_S = 60.0
MAX_RETRY_AFTER_S = 600.0  # a longer Retry-After is a quota stop, not a pause: give up and let the run stop early
ANTHROPIC_VERSION = "2023-06-01"


class _HttpProvider:
    name = "llm"

    def __init__(self, *, api_key: str | None, model: str, base_url: str, timeout_s: float = 120.0,
                 max_retries: int = 3, backoff_s: float = 1.0, transport: httpx.BaseTransport | None = None,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic,
                 rate_limit_retries: int = 8, min_interval_s: float = 0.0, extra_body: dict | None = None):
        self._api_key = api_key or None
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_retries, self.backoff_s, self._sleep, self._clock = max_retries, backoff_s, sleep, clock
        self.rate_limit_retries, self.min_interval_s = rate_limit_retries, min_interval_s
        self.extra_body = dict(extra_body or {})  # provider-specific request fields, e.g. turning off thinking
        self._last_call: float | None = None
        self._client = httpx.Client(timeout=timeout_s, transport=transport)

    def __repr__(self):
        return f"{type(self).__name__}(model={self.model!r}, base_url={self.base_url!r})"

    def _redact(self, text: str) -> str:
        return text.replace(self._api_key, "***") if self._api_key else text

    def _wait_for_slot(self):
        """Free-tier rate limits: at least min_interval_s between the starts of two requests."""
        if self._last_call is not None and (wait := self._last_call + self.min_interval_s - self._clock()) > 0:
            self._sleep(wait)
        self._last_call = self._clock()

    @staticmethod
    def _retry_after(resp: httpx.Response | None) -> float | None:
        try:
            value = float(resp.headers["Retry-After"])
        except (AttributeError, KeyError, ValueError):  # no response, no header, or an HTTP date
            return None
        return value if 0 <= value <= MAX_RETRY_AFTER_S else None

    def _post(self, path: str, headers: dict, body: dict) -> tuple[dict, float]:
        url = f"{self.base_url}{path}"
        body = {**body, **self.extra_body}
        attempt = 0
        while True:
            self._wait_for_slot()
            started, resp = time.perf_counter(), None
            try:
                resp = self._client.post(url, headers=headers, json=body)
            except httpx.TransportError as e:  # timeouts and connection errors
                problem, retryable = f"{type(e).__name__}", True
            else:
                if resp.status_code < 400:
                    return resp.json(), time.perf_counter() - started
                problem = f"HTTP {resp.status_code}: {self._error_text(resp)}"
                retryable = resp.status_code in RETRYABLE_STATUS
            limit = self.rate_limit_retries if resp is not None and resp.status_code == 429 else self.max_retries
            if not retryable or attempt >= limit:
                raise LLMError(self._redact(f"{self.name} request failed after {attempt + 1} attempt(s): {problem}"))
            delay = self._retry_after(resp)
            if delay is None:
                delay = min(self.backoff_s * 2**attempt, MAX_BACKOFF_S)
            log.warning("%s: %s, retry %d/%d in %.1fs", self.name, self._redact(problem.split(":")[0]),
                        attempt + 1, limit, delay)
            self._sleep(delay)
            attempt += 1

    @staticmethod
    def _error_text(resp: httpx.Response) -> str:
        try:
            error = resp.json().get("error", {})
            return error.get("message") or str(error) if isinstance(error, dict) else str(error)
        except (ValueError, AttributeError):  # not JSON, or JSON that is not an object
            return resp.text[:500]


class AnthropicProvider(_HttpProvider):
    name = "anthropic"

    def __init__(self, *, api_key: str, model: str, base_url: str = "https://api.anthropic.com", **kw):
        super().__init__(api_key=api_key, model=model, base_url=base_url, **kw)

    def complete(self, system: str, messages: list[Message], *, temperature: float, max_tokens: int) -> LLMResponse:
        headers = {"x-api-key": self._api_key or "", "anthropic-version": ANTHROPIC_VERSION}
        body = {"model": self.model, "system": system, "max_tokens": max_tokens, "temperature": temperature,
                "messages": [{"role": m.role, "content": m.content} for m in messages]}
        data, latency = self._post("/v1/messages", headers, body)
        text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        usage = data.get("usage", {})
        return LLMResponse(text, data.get("model", self.model), usage.get("input_tokens", 0),
                           usage.get("output_tokens", 0), latency, raw=data)


class OpenAICompatProvider(_HttpProvider):
    """Chat completions at <base_url>/chat/completions (OpenAI, Ollama, vLLM, LM Studio)."""

    name = "openai_compat"

    def __init__(self, *, base_url: str, model: str, api_key: str | None = None, **kw):
        super().__init__(api_key=api_key, model=model, base_url=base_url, **kw)

    def complete(self, system: str, messages: list[Message], *, temperature: float, max_tokens: int) -> LLMResponse:
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        body = {"model": self.model, "temperature": temperature, "max_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}]
                + [{"role": m.role, "content": m.content} for m in messages]}
        data, latency = self._post("/chat/completions", headers, body)
        choices = data.get("choices") or [{}]
        usage = data.get("usage") or {}
        return LLMResponse(choices[0].get("message", {}).get("content") or "", data.get("model", self.model),
                           usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), latency, raw=data)
