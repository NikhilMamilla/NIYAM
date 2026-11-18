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


# --- free-tier limits (Phase 12) ------------------------------------------------------------------------------


class FakeClock:
    """Injected clock + sleep: sleeping advances time, so interval waits are exact and instant."""

    def __init__(self):
        self.now, self.slept = 100.0, []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


def openai(recorder, **kw):
    clock = kw.pop("clock", None) or FakeClock()
    return OpenAICompatProvider(base_url="http://h/v1", model="x", api_key=KEY, transport=httpx.MockTransport(recorder),
                                sleep=clock.sleep, clock=clock, **kw), clock


def rate_limited(retry_after=None):
    headers = {"Retry-After": str(retry_after)} if retry_after is not None else {}
    return lambda r: httpx.Response(429, headers=headers, json={"error": {"message": "slow down"}})


def test_429_waits_for_the_retry_after_header():
    provider, clock = openai(Recorder(rate_limited(7), openai_ok))
    assert provider.complete("S", MSGS, temperature=0, max_tokens=10).text == "hi"
    assert clock.slept == [7.0]


def test_429_without_retry_after_backs_off_exponentially_up_to_60_s():
    rec = Recorder(*[rate_limited()] * 4, openai_ok)
    provider, clock = openai(rec, backoff_s=16)
    assert provider.complete("S", MSGS, temperature=0, max_tokens=10).text == "hi"
    assert clock.slept == [16, 32, 60, 60]


def test_429_gets_more_retries_than_other_errors():
    rec = Recorder(*[rate_limited(1)] * 5, openai_ok)
    provider, _ = openai(rec, max_retries=2, rate_limit_retries=5)
    assert provider.complete("S", MSGS, temperature=0, max_tokens=10).text == "hi"
    assert len(rec.requests) == 6
    rec = Recorder(lambda r: httpx.Response(503, text="down"))
    with pytest.raises(LLMError, match="503"):
        openai(rec, max_retries=2, rate_limit_retries=5)[0].complete("S", MSGS, temperature=0, max_tokens=10)
    assert len(rec.requests) == 3


def test_429_exhausted_raises_without_the_key():
    rec = Recorder(lambda r: httpx.Response(429, json={"error": {"message": f"quota for {KEY}"}}))
    with pytest.raises(LLMError, match="429") as exc:
        openai(rec, rate_limit_retries=2)[0].complete("S", MSGS, temperature=0, max_tokens=10)
    assert len(rec.requests) == 3 and KEY not in str(exc.value)


def test_5xx_then_success_honours_retry_after():
    provider, clock = openai(Recorder(lambda r: httpx.Response(502, headers={"Retry-After": "3"}), openai_ok))
    assert provider.complete("S", MSGS, temperature=0, max_tokens=10).text == "hi"
    assert clock.slept == [3.0]


def test_min_interval_spaces_calls_using_the_injected_clock():
    provider, clock = openai(Recorder(openai_ok), min_interval_s=1.6)
    for _ in range(3):
        provider.complete("S", MSGS, temperature=0, max_tokens=10)
    assert clock.slept == [pytest.approx(1.6), pytest.approx(1.6)]  # none before the first call
    clock.now += 5  # enough time has passed: no wait
    provider.complete("S", MSGS, temperature=0, max_tokens=10)
    assert len(clock.slept) == 2


def test_extra_body_is_merged_into_the_request():
    rec = Recorder(openai_ok)
    provider, _ = openai(rec, extra_body={"thinking": {"type": "disabled"}})
    provider.complete("S", MSGS, temperature=0, max_tokens=10)
    body = json.loads(rec.requests[0].content)
    assert body["thinking"] == {"type": "disabled"} and body["model"] == "x"


def test_open_slot_sends_its_key_as_bearer_and_redacts_it():
    s = Settings(_env_file=None, open_model_endpoint="http://h/v1", open_model_name="nemo", open_model_api_key=KEY,
                 open_model_extra_body={"reasoning_effort": "none"}, open_model_min_interval_s=0)
    provider = get_provider("open", s)
    rec = Recorder(lambda r: httpx.Response(401, json={"error": {"message": f"bad key {KEY}"}}))
    provider._client = httpx.Client(transport=httpx.MockTransport(rec))
    with pytest.raises(LLMError) as exc:
        provider.complete("S", MSGS, temperature=0, max_tokens=10)
    assert rec.requests[0].headers["authorization"] == f"Bearer {KEY}"
    assert json.loads(rec.requests[0].content)["reasoning_effort"] == "none"
    assert KEY not in str(exc.value) and KEY not in repr(provider)


def test_open_slot_without_a_key_sends_no_auth_header():
    s = Settings(_env_file=None, open_model_endpoint="http://localhost:11434/v1", open_model_name="qwen")
    provider = get_provider("open", s)
    rec = Recorder(openai_ok)
    provider._client = httpx.Client(transport=httpx.MockTransport(rec))
    provider.complete("S", MSGS, temperature=0, max_tokens=10)
    assert "authorization" not in rec.requests[0].headers


def test_slot_settings_defaults():
    s = Settings(_env_file=None)
    assert (s.open_model_min_interval_s, s.hosted_llm_min_interval_s) == (1.6, 0.0)
    assert s.llm_rate_limit_retries > s.llm_max_retries


def test_tests_cannot_reach_the_network():
    with pytest.raises(RuntimeError, match="network"):
        httpx.get("https://example.invalid/")
