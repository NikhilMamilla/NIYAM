"""Preflight for real evaluation runs: is each configured provider reachable, and what might a run cost?

`run_preflight` makes ONE tiny call per configured model ("Reply with the single word OK.") and never compiles.
Nothing here prints or stores a key: configuration is reported by variable NAME (set / missing), and provider errors
are reduced to an HTTP status class and a fixed sentence, never the server's text or the request headers."""

import json
import math
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from app.config import Settings
from app.llm.base import LLMError, Message, ProviderNotConfigured
from app.llm.factory import get_provider

STAMP = None  # set below; tests point it elsewhere
STAMP_MAX_AGE = timedelta(hours=24)
PING = "Reply with the single word OK."
ENV_NAMES = {
    "hosted": ["HOSTED_LLM_PROVIDER", "HOSTED_LLM_MODEL", "HOSTED_LLM_API_KEY", "HOSTED_LLM_BASE_URL"],
    "open": ["OPEN_MODEL_ENDPOINT", "OPEN_MODEL_NAME", "OPEN_MODEL_API_KEY"],
}
STATUS_MESSAGES = {401: "authentication failed: check the API key variable", 403: "authentication failed: the key "
                   "is not allowed to use this model", 404: "model or endpoint not found: check the model name and "
                   "base URL", 429: "rate limited or out of quota: wait, or check the account's limits"}


def _stamp_path():
    from app.eval.runner import RUNS_DIR

    return STAMP or RUNS_DIR / ".preflight.json"


def default_settings() -> Settings:
    from app.config import settings

    return settings


def estimate_tokens(text: str) -> int:
    """Rough estimate: characters / 4, rounded up. Real tokenisers differ by model; treat it as an order of size."""
    return math.ceil(len(text) / 4)


def worst_case_tokens(base: int, *, max_tokens: int, repairs: int, repair_overhead: int) -> tuple[int, int]:
    """(input, output) tokens for one compilation with `repairs` repair turns. Each repair resends the history:
    the previous answer (at most max_tokens) and a repair message that quotes it again plus a diagnosis."""
    per_turn = 2 * max_tokens + repair_overhead
    return sum(base + k * per_turn for k in range(repairs + 1)), (repairs + 1) * max_tokens


def safe_error(error: Exception) -> str:
    text = str(error)
    if m := re.search(r"HTTP (\d{3})", text):
        status = int(m.group(1))
        message = STATUS_MESSAGES.get(status, "provider error: try again later" if status >= 500 else "request rejected")
        return f"HTTP {status // 100}xx ({status}): {message}"
    if m := re.search(r"(ConnectError|ConnectTimeout|ReadTimeout|WriteTimeout|PoolTimeout|RemoteProtocolError|"
                      r"\w*TransportError|\w*Timeout\w*)", text):
        return f"connection failed ({m.group(1)}): check the endpoint and network"
    return "request failed (no further detail is shown, to keep secrets out of logs)"


def config_lines(role: str, settings: Settings) -> list[str]:
    names = ENV_NAMES[role]
    return [f"    {n}: {'set' if getattr(settings, n.lower(), '') else 'missing'}" for n in names]


def run_preflight(config, *, settings: Settings | None = None, provider_factory=None, out=print) -> int:
    settings = settings or default_settings()
    make = provider_factory or (lambda spec: get_provider(spec.role, settings, model=spec.model))
    results, configured = {}, 0
    for spec in config.models:
        out(f"{spec.name} ({spec.role})")
        for line in config_lines(spec.role, settings):
            out(line)
        try:
            provider = make(spec)
        except ProviderNotConfigured:
            out(f"{spec.name}: skipped: not configured")
            continue
        configured += 1
        host = urlparse(getattr(provider, "base_url", "") or "").hostname or "(none)"
        out(f"    provider {type(provider).__name__}, host {host}, model {provider.model}")
        if hasattr(provider, "max_retries"):
            provider.max_retries = provider.rate_limit_retries = 0  # one call means one call
        try:
            r = provider.complete("Connectivity check.", [Message("user", PING)], temperature=0.0, max_tokens=8)
        except LLMError as e:
            out(f"{spec.name}: FAILED: {safe_error(e)}")
            results[spec.name] = {"ok": False, "provider_class": type(provider).__name__, "model": provider.model}
            continue
        except Exception as e:  # anything else: report the type only
            out(f"{spec.name}: FAILED: unexpected {type(e).__name__}")
            results[spec.name] = {"ok": False, "provider_class": type(provider).__name__, "model": provider.model}
            continue
        out(f"{spec.name}: OK in {r.latency_s:.2f} s latency, input tokens {r.input_tokens}, "
            f"output tokens {r.output_tokens}, reply {r.text.strip()[:20]!r}")
        results[spec.name] = {"ok": True, "provider_class": type(provider).__name__, "model": provider.model}
    path = _stamp_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "results": results}, indent=2),
                    encoding="utf-8")
    if not configured:
        out("FAILED: no model is configured (see .env.example)")
        return 2
    optional = {spec.name for spec in config.models if spec.optional}
    failed = [name for name, r in results.items() if not r["ok"] and name not in optional]
    skipped = [name for name, r in results.items() if not r["ok"] and name in optional]
    if skipped:
        out(f"optional, will be skipped: {', '.join(skipped)}")
    if not failed and any(r["ok"] for r in results.values()):
        out("preflight OK")
        return 0
    out(f"preflight FAILED for: {', '.join(failed) or 'every model'}")
    return 1


def check_stamp(config, now: datetime | None = None) -> tuple[bool, str, dict[str, str]]:
    """A real run needs a successful preflight in the last 24 hours on this machine of every selected model, except
    optional ones: those are returned as skipped {name: reason}. At least one model must remain."""
    path = _stamp_path()
    if not path.exists():
        return False, "no preflight found: run `python -m app.eval.cli preflight` first", {}
    data = json.loads(path.read_text(encoding="utf-8"))
    when = datetime.fromisoformat(data["timestamp"])
    if (now or datetime.now(timezone.utc)) - when > STAMP_MAX_AGE:
        return False, f"the last preflight ({data['timestamp']}) is older than 24 hours: run preflight again", {}
    skipped = {}
    for spec in config.models:
        if not data["results"].get(spec.name, {}).get("ok"):
            if not spec.optional:
                return False, f"{spec.name} did not pass the last preflight: fix it and run preflight again", {}
            skipped[spec.name] = f"optional model did not pass the preflight at {data['timestamp']}"
    if len(skipped) == len(config.models):
        return False, "no model passed the last preflight", skipped
    return True, f"preflight OK at {data['timestamp']}", skipped
