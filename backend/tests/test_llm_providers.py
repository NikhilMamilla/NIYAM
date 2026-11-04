import json
import logging

import httpx
import pytest

from app.config import Settings
from app.llm.base import LLMError, Message, ProviderNotConfigured
from app.llm.factory import get_provider
from app.llm.providers import AnthropicProvider, OpenAICompatProvider
from app.llm.scripted import ScriptedProvider

KEY = "sk-test-SECRET-123456"
MSGS = [Message(role="user", content="author an IDS")]


def anthropic_ok(request):
    return httpx.Response(200, json={
        "model": "claude-test-1", "content": [{"type": "text", "text": "hello "}, {"type": "text", "text": "world"}],
        "usage": {"input_tokens": 11, "output_tokens": 7},
    })


def openai_ok(request):
    return httpx.Response(200, json={
        "model": "qwen-test", "choices": [{"message": {"role": "assistant", "content": "hi"}}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3},
    })


class Recorder:
    def __init__(self, *handlers):
        self.handlers = list(handlers)
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        handler = self.handlers.pop(0) if len(self.handlers) > 1 else self.handlers[0]
        return handler(request)


def anthropic(recorder, **kw):
    return AnthropicProvider(api_key=KEY, model="claude-test-1", transport=httpx.MockTransport(recorder),
                             sleep=lambda s: None, **kw)


# --- Anthropic ----------------------------------------------------------------


def test_anthropic_request_shape_and_response_parsing():
    rec = Recorder(anthropic_ok)
    resp = anthropic(rec).complete("SYS", MSGS, temperature=0.0, max_tokens=256)

    [req] = rec.requests
    assert str(req.url) == "https://api.anthropic.com/v1/messages"
    assert req.headers["x-api-key"] == KEY
    assert req.headers["anthropic-version"]
    body = json.loads(req.content)
    assert body == {"model": "claude-test-1", "system": "SYS", "max_tokens": 256, "temperature": 0.0,
                    "messages": [{"role": "user", "content": "author an IDS"}]}
    assert (resp.text, resp.model, resp.input_tokens, resp.output_tokens) == ("hello world", "claude-test-1", 11, 7)
    assert resp.latency_s >= 0


def test_anthropic_retries_429_then_succeeds_with_backoff():
    slept = []
    rec = Recorder(lambda r: httpx.Response(429, json={"error": {"message": "rate limited"}}), anthropic_ok)
    provider = AnthropicProvider(api_key=KEY, model="m", transport=httpx.MockTransport(rec),
                                 sleep=slept.append, max_retries=3, backoff_s=0.5)
    assert provider.complete("S", MSGS, temperature=0, max_tokens=10).text == "hello world"
    assert len(rec.requests) == 2
    assert slept == [0.5]


def test_retries_on_timeout():
    def timeout(request):
        raise httpx.ReadTimeout("slow", request=request)
    rec = Recorder(timeout, anthropic_ok)
    assert anthropic(rec).complete("S", MSGS, temperature=0, max_tokens=10).text == "hello world"
    assert len(rec.requests) == 2


def test_retries_are_bounded_on_5xx():
    rec = Recorder(lambda r: httpx.Response(503, text="overloaded"))
    with pytest.raises(LLMError, match="503"):
        anthropic(rec, max_retries=2).complete("S", MSGS, temperature=0, max_tokens=10)
    assert len(rec.requests) == 3


def test_client_error_is_surfaced_without_retry():
    rec = Recorder(lambda r: httpx.Response(400, json={
        "type": "error", "error": {"type": "invalid_request_error", "message": "max_tokens: must be positive"}}))
    with pytest.raises(LLMError, match="max_tokens: must be positive"):
        anthropic(rec).complete("S", MSGS, temperature=0, max_tokens=10)
    assert len(rec.requests) == 1


def test_api_key_never_in_exception_or_logs(caplog):
    caplog.set_level(logging.DEBUG)
    echo = lambda r: httpx.Response(401, json={"error": {"message": f"invalid x-api-key {KEY}"}})  # noqa: E731
    retry_then_echo = Recorder(lambda r: httpx.Response(500, text=f"boom {KEY}"), echo)
    with pytest.raises(LLMError) as exc:
        anthropic(retry_then_echo).complete("S", MSGS, temperature=0, max_tokens=10)
    assert KEY not in str(exc.value)
    assert KEY not in repr(exc.value)
    assert KEY not in caplog.text
    assert "401" in str(exc.value)


# --- OpenAI-compatible ----------------------------------------------------------


def test_openai_compat_request_shape_with_and_without_key():
    for key in ("k-123", None):
        rec = Recorder(openai_ok)
        provider = OpenAICompatProvider(base_url="http://localhost:11434/v1/", model="qwen-test", api_key=key,
                                        transport=httpx.MockTransport(rec), sleep=lambda s: None)
        resp = provider.complete("SYS", MSGS, temperature=0.2, max_tokens=64)

        [req] = rec.requests
        assert str(req.url) == "http://localhost:11434/v1/chat/completions"
        assert ("authorization" in req.headers) == (key is not None)
        body = json.loads(req.content)
        assert body["messages"] == [{"role": "system", "content": "SYS"}, {"role": "user", "content": "author an IDS"}]
        assert (body["model"], body["temperature"], body["max_tokens"]) == ("qwen-test", 0.2, 64)
        assert (resp.text, resp.model, resp.input_tokens, resp.output_tokens) == ("hi", "qwen-test", 5, 3)


def test_openai_compat_missing_usage_counts_as_zero():
    rec = Recorder(lambda r: httpx.Response(200, json={"model": "x", "choices": [{"message": {"content": "ok"}}]}))
    resp = OpenAICompatProvider(base_url="http://h/v1", model="x", transport=httpx.MockTransport(rec)).complete(
        "S", MSGS, temperature=0, max_tokens=5)
    assert (resp.input_tokens, resp.output_tokens) == (0, 0)


# --- Scripted -------------------------------------------------------------------


def test_scripted_provider_replays_in_order_and_records_calls():
    p = ScriptedProvider(["first", "second"])
    assert p.complete("S1", MSGS, temperature=0, max_tokens=9).text == "first"
    assert p.complete("S2", MSGS + [Message("assistant", "first")], temperature=0, max_tokens=9).text == "second"
    assert [c["system"] for c in p.calls] == ["S1", "S2"]
    assert p.calls[1]["messages"][-1] == Message("assistant", "first")
    with pytest.raises(LLMError, match="exhausted"):
        p.complete("S3", MSGS, temperature=0, max_tokens=9)


# --- factory --------------------------------------------------------------------


def test_get_provider_unconfigured_raises_clear_error():
    with pytest.raises(ProviderNotConfigured, match="HOSTED_LLM_PROVIDER"):
        get_provider("hosted", Settings(_env_file=None))
    with pytest.raises(ProviderNotConfigured, match="OPEN_MODEL_ENDPOINT"):
        get_provider("open", Settings(_env_file=None))


def test_get_provider_builds_configured_providers():
    s = Settings(_env_file=None, hosted_llm_provider="anthropic", hosted_llm_model="claude-x",
                 hosted_llm_api_key=KEY, open_model_endpoint="http://localhost:11434/v1", open_model_name="qwen")
    hosted = get_provider("hosted", s)
    assert isinstance(hosted, AnthropicProvider) and hosted.model == "claude-x"
    opened = get_provider("open", s)
    assert isinstance(opened, OpenAICompatProvider) and opened.model == "qwen"
    assert KEY not in repr(hosted)
