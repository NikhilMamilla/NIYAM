import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import yaml

from app.config import Settings
from app.eval import cli, preflight, runner
from app.llm.factory import get_provider

FAKE_KEY = "sk-test-FAKEKEY-0123456789abcdefSECRET"


@pytest.fixture
def stamp(tmp_path, monkeypatch):
    path = tmp_path / ".preflight.json"
    monkeypatch.setattr(preflight, "STAMP", path)
    return path


@pytest.fixture
def config_path(tmp_path):
    data = {"models": [{"name": "hosted-a", "role": "hosted"}, {"name": "open-b", "role": "open"}],
            "budget": {"max_total_calls": 500, "max_total_tokens": 10_000_000}}
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def settings(**kw):
    return Settings(_env_file=None, hosted_llm_provider="anthropic", hosted_llm_model="claude-test",
                    hosted_llm_api_key=FAKE_KEY, **kw)


def factory_with(handler, s):
    """Providers from the real factory, but talking to an httpx.MockTransport instead of the network."""
    def make(spec):
        provider = get_provider(spec.role, s)
        provider._client = httpx.Client(transport=httpx.MockTransport(handler))
        provider._sleep = lambda seconds: None
        return provider
    return make


def ok_anthropic(request):
    assert request.headers["x-api-key"] == FAKE_KEY  # the key is sent, never printed
    return httpx.Response(200, json={"content": [{"type": "text", "text": "OK"}], "model": "claude-test",
                                     "usage": {"input_tokens": 14, "output_tokens": 1}})


def run(config_path, s, handler, capsys):
    code = preflight.run_preflight(runner.load_config(config_path), settings=s,
                                   provider_factory=factory_with(handler, s))
    out = capsys.readouterr()
    return code, out.out + out.err


def assert_no_key(text):
    for fragment in (FAKE_KEY, FAKE_KEY[8:20], "SECRET"):
        assert fragment not in text


def test_success_path_reports_latency_tokens_and_writes_a_stamp(config_path, stamp, capsys):
    code, out = run(config_path, settings(), ok_anthropic, capsys)
    assert code == 0
    assert "hosted-a: OK" in out and "input tokens 14, output tokens 1" in out and "latency" in out
    assert "HOSTED_LLM_API_KEY: set" in out and "AnthropicProvider" in out and "host api.anthropic.com" in out
    assert "open-b: skipped: not configured" in out and "OPEN_MODEL_ENDPOINT: missing" in out
    data = json.loads(stamp.read_text(encoding="utf-8"))
    assert data["results"]["hosted-a"]["ok"] is True and "open-b" not in data["results"]
    assert_no_key(out + stamp.read_text(encoding="utf-8"))


@pytest.mark.parametrize("status, expected", [(401, "authentication failed"), (403, "authentication failed"),
                                              (429, "rate limited"), (404, "not found"), (503, "provider error")])
def test_failures_are_safe_and_exit_non_zero(config_path, stamp, capsys, status, expected):
    def handler(request):  # a hostile server that echoes the key back in its error
        return httpx.Response(status, json={"error": {"message": f"bad key {FAKE_KEY}"}})
    code, out = run(config_path, settings(), handler, capsys)
    assert code != 0 and f"HTTP {status // 100}xx" in out and expected in out
    assert_no_key(out + stamp.read_text(encoding="utf-8"))
    assert json.loads(stamp.read_text(encoding="utf-8"))["results"]["hosted-a"]["ok"] is False


def test_connection_errors_are_reported_without_detail(config_path, stamp, capsys):
    def handler(request):
        raise httpx.ConnectError(f"cannot connect, key {FAKE_KEY}")
    code, out = run(config_path, settings(), handler, capsys)
    assert code != 0 and "connection failed (ConnectError)" in out
    assert_no_key(out)


def test_nothing_configured_is_a_failure(config_path, stamp, capsys):
    code = preflight.run_preflight(runner.load_config(config_path), settings=Settings(_env_file=None))
    out = capsys.readouterr().out
    assert code != 0 and out.count("skipped: not configured") == 2 and "no model is configured" in out


def test_the_cli_preflight_never_compiles(config_path, stamp, capsys, monkeypatch):
    monkeypatch.setattr(runner, "compile_unit", lambda *a, **k: pytest.fail("preflight must not compile"))
    monkeypatch.setattr(preflight, "default_settings", lambda: Settings(_env_file=None))
    assert cli.main(["--config", str(config_path), "preflight"]) != 0


# --- the stamp gates real runs -----------------------------------------------------------------------------------


def write_stamp(stamp, results, hours_ago=1.0):
    when = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    stamp.write_text(json.dumps({"timestamp": when.isoformat(), "results": results}), encoding="utf-8")


def test_run_refuses_without_a_recent_successful_preflight(config_path, stamp, capsys):
    assert cli.main(["--config", str(config_path), "run", "--yes"]) == 2
    assert "no preflight" in capsys.readouterr().out
    write_stamp(stamp, {"hosted-a": {"ok": True}, "open-b": {"ok": True}}, hours_ago=30)
    assert cli.main(["--config", str(config_path), "run", "--yes"]) == 2
    assert "older than 24 hours" in capsys.readouterr().out
    write_stamp(stamp, {"hosted-a": {"ok": True}, "open-b": {"ok": False}})
    assert cli.main(["--config", str(config_path), "run", "--yes"]) == 2
    assert "open-b did not pass" in capsys.readouterr().out
    write_stamp(stamp, {"hosted-a": {"ok": True}})
    assert cli.main(["--config", str(config_path), "run", "--yes"]) == 2
    assert "open-b did not pass" in capsys.readouterr().out


def test_a_good_stamp_lets_the_run_reach_the_provider_check(config_path, stamp, capsys, monkeypatch):
    write_stamp(stamp, {"hosted-a": {"ok": True}, "open-b": {"ok": True}})
    monkeypatch.setattr(cli, "get_provider", lambda role, model=None: (_ for _ in ()).throw(
        cli.ProviderNotConfigured("not configured in this test")))
    assert cli.main(["--config", str(config_path), "run", "--yes"]) == 2
    out = capsys.readouterr().out
    assert "preflight OK at" in out and "is not configured" in out  # passed the gate, stopped at the provider


def test_skip_preflight_prints_a_warning(config_path, stamp, capsys, monkeypatch):
    monkeypatch.setattr(cli, "get_provider", lambda role, model=None: (_ for _ in ()).throw(
        cli.ProviderNotConfigured("not configured in this test")))
    cli.main(["--config", str(config_path), "run", "--yes", "--skip-preflight"])
    assert "WARNING: skipping the preflight" in capsys.readouterr().out


def test_dry_runs_need_no_preflight(config_path, stamp, capsys, monkeypatch, tmp_path):
    from app.fixtures.gold_ids import load_units
    monkeypatch.setattr(runner, "select_units", lambda c: [load_units()["MBBL2016-5.4.2#1"]])
    assert cli.main(["--config", str(config_path), "run", "--yes", "--dry-run", "--runs-dir", str(tmp_path / "r"),
                     "--no-report"]) == 0


# --- token estimate ----------------------------------------------------------------------------------------------


def test_token_estimate_on_known_strings():
    assert preflight.estimate_tokens("") == 0
    assert preflight.estimate_tokens("a" * 40) == 10
    assert preflight.estimate_tokens("abcde") == 2  # rounded up


def test_worst_case_tokens_include_growing_repair_history():
    # base 100 tokens, answers up to 10 tokens, repair text 5 tokens, 2 repairs:
    # call 0: 100; call 1: 100 + (10 + 10 + 5); call 2: 100 + 2 * 25  -> input 375, output 3 * 10
    assert preflight.worst_case_tokens(100, max_tokens=10, repairs=2, repair_overhead=5) == (375, 30)
    assert preflight.worst_case_tokens(100, max_tokens=10, repairs=0, repair_overhead=5) == (100, 10)


def test_plan_shows_estimates_caps_and_prices(config_path, capsys):
    data = yaml.safe_load(config_path.read_text())
    data["models"][0].update(price_per_million_input=3.0, price_per_million_output=15.0)
    config_path.write_text(yaml.safe_dump(data))
    assert cli.main(["--config", str(config_path), "plan"]) == 0
    out = capsys.readouterr().out
    assert "rough estimate: characters / 4" in out
    assert "hosted-a: worst case" in out and "estimated worst-case cost" in out
    assert "open-b: worst case" in out and "no price configured" in out
    assert "max_total_tokens" in out


# --- per-model ids and optional models (Phase 12) -----------------------------------------------------------


def test_a_config_model_id_overrides_the_slot_model_on_the_same_endpoint():
    s = Settings(_env_file=None, open_model_endpoint="http://h/v1", open_model_name="big", open_model_api_key=FAKE_KEY)
    small = get_provider("open", s, model="small")
    assert small.model == "small" and small.base_url == "http://h/v1" and small._api_key == FAKE_KEY
    assert get_provider("open", s).model == "big"
    assert get_provider("open", Settings(_env_file=None, open_model_endpoint="http://h/v1"), model="only").model == "only"


def optional_config(path):
    data = yaml.safe_load(path.read_text())
    data["models"][0]["optional"] = True  # hosted-a
    path.write_text(yaml.safe_dump(data))
    return runner.load_config(path)


def test_a_failed_optional_model_is_skipped_not_blocking(config_path, stamp):
    config = optional_config(config_path)
    write_stamp(stamp, {"hosted-a": {"ok": False}, "open-b": {"ok": True}})
    ok, reason, skipped = preflight.check_stamp(config)
    assert ok and list(skipped) == ["hosted-a"] and "preflight" in skipped["hosted-a"]
    write_stamp(stamp, {"hosted-a": {"ok": True}, "open-b": {"ok": False}})  # a required model still blocks
    ok, reason, _ = preflight.check_stamp(config)
    assert not ok and "open-b did not pass" in reason


def test_no_model_left_after_skipping_is_a_refusal(config_path, stamp):
    data = yaml.safe_load(config_path.read_text())
    for m in data["models"]:
        m["optional"] = True
    config_path.write_text(yaml.safe_dump(data))
    write_stamp(stamp, {"hosted-a": {"ok": False}, "open-b": {"ok": False}})
    ok, reason, _ = preflight.check_stamp(runner.load_config(config_path))
    assert not ok and "no model passed" in reason


def test_preflight_exit_code_ignores_a_failed_optional_model(config_path, stamp, capsys):
    optional_config(config_path)
    s = settings(open_model_endpoint="http://h/v1", open_model_name="qwen")

    def handler(request):
        if "anthropic" in str(request.url):
            return httpx.Response(429, json={"error": {"message": "overloaded"}})
        return httpx.Response(200, json={"choices": [{"message": {"content": "OK"}}], "usage": {}})
    code, out = run(config_path, s, handler, capsys)
    assert code == 0 and "optional, will be skipped: hosted-a" in out


def test_the_run_executes_only_passed_models_and_records_the_skipped(config_path, stamp, capsys, monkeypatch, tmp_path):
    from app.eval.dryrun import DryRunProvider
    from app.fixtures.gold_ids import load_units

    optional_config(config_path)
    write_stamp(stamp, {"hosted-a": {"ok": False}, "open-b": {"ok": True}})
    monkeypatch.setattr(runner, "select_units", lambda c: [load_units()["MBBL2016-5.4.2#1"]])
    built = []
    monkeypatch.setattr(cli, "get_provider", lambda role, model=None: built.append(role) or DryRunProvider("x"))
    assert cli.main(["--config", str(config_path), "run", "--yes", "--runs-dir", str(tmp_path / "r"), "--no-report"]) == 0
    [results] = (tmp_path / "r").glob("*/results.json")
    data = json.loads(results.read_text())
    assert built == ["open"] and {i["model"] for i in data["items"]} == {"open-b"}
    assert list(data["meta"]["skipped_models"]) == ["hosted-a"]
    assert "skipping optional model hosted-a" in capsys.readouterr().out
