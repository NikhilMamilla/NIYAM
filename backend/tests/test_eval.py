import csv
import json

import pytest
import yaml

from app.eval import cli, report, runner
from app.eval.dryrun import DryRunProvider
from app.eval.metrics import Rate, group_metrics, paired, wilson_interval
from app.fixtures.gold_ids import load_units
from app.llm.base import Message, ProviderNotConfigured

IDS_UNITS = ["MBBL2016-5.4.1#b", "MBBL2016-5.4.2#1"]


# --- Wilson interval ---------------------------------------------------------------------------------------------


def test_wilson_matches_the_hand_computation():
    # p = 0.7, z^2 = 3.8415: denom = 1.38415, centre = 0.89207/1.38415 = 0.64448,
    # half = 1.96 * sqrt(0.021 + 0.0096037) / 1.38415 = 0.24772  ->  [0.3968, 0.8922]
    lo, hi = wilson_interval(7, 10)
    assert lo == pytest.approx(0.3968, abs=1e-4) and hi == pytest.approx(0.8922, abs=1e-4)


def test_wilson_edges():
    assert wilson_interval(0, 0) is None
    lo, hi = wilson_interval(0, 6)
    assert lo == pytest.approx(0.0, abs=1e-12) and hi == pytest.approx(0.3903, abs=1e-4)
    lo, hi = wilson_interval(6, 6)
    assert hi == 1.0 and lo == pytest.approx(0.6097, abs=1e-4)
    assert str(Rate(3, 6)).startswith("3/6 = 50% [")
    assert str(Rate(0, 0)) == "0/0 (n/a)"


# --- metrics -----------------------------------------------------------------------------------------------------


def item(mode, unit, outcome, shipped, valid=True, dev=True, held=True, repairs=0, model="m"):
    return {"model": model, "mode": mode, "unit_id": unit, "repeat": 0, "outcome": outcome, "shipped": shipped,
            "repair_rounds": repairs, "total_tokens": 100, "wall_time_s": 1.0,
            "score": {"valid": valid, "dev_correct": dev, "heldout_correct": held}}


def test_group_metrics_and_wrong_shipped_rate():
    gated = [item("gated", "a", "accepted", True), item("gated", "b", "accepted", True, held=False, repairs=2),
             item("gated", "c", "needs_human", False, dev=False, held=False, repairs=3)]
    m = group_metrics(gated)
    assert (m["n"], m["shipped"].k, m["wrong_shipped"].k, m["wrong_shipped"].n) == (3, 2, 1, 2)
    assert (m["needs_human"].k, m["heldout_correct"].k, m["mean_repairs"]) == (1, 1, 5 / 3)
    ungated = group_metrics([item("ungated", "a", "baseline_scored", True, held=False)])
    assert ungated["needs_human"] is None and ungated["mean_repairs"] is None
    assert (ungated["wrong_shipped"].k, ungated["wrong_shipped"].n) == (1, 1)


def test_paired_comparison_counts_units_not_rows():
    items = [item("gated", "a", "accepted", True), item("ungated", "a", "baseline_scored", True, held=False),
             item("gated", "b", "needs_human", False, held=False), item("ungated", "b", "baseline_scored", True),
             item("gated", "c", "accepted", True), item("ungated", "c", "baseline_scored", True)]
    assert paired(items) == {"m": {"both_correct": 1, "gated_only": 1, "ungated_only": 1, "neither": 0}}


# --- dry-run provider --------------------------------------------------------------------------------------------


def first_prompt(unit_id):
    return [Message("user", f"Rule unit {unit_id}:\n<rule>x</rule>")]


def test_dry_run_provider_is_deterministic_and_fixes_malformed_answers():
    a, b = DryRunProvider("s"), DryRunProvider("s")
    for unit in load_units():
        assert a.complete("sys", first_prompt(unit), temperature=0, max_tokens=10).text == \
            b.complete("sys", first_prompt(unit), temperature=0, max_tokens=10).text
    p = DryRunProvider("x")
    p._last["MBBL2016-5.4.1#b"] = "malformed"
    repair = [*first_prompt("MBBL2016-5.4.1#b"), Message("assistant", "..."),
              Message("user", "The verifier rejected your previous answer.")]
    assert "(correct)" in p.complete("sys", repair, temperature=0, max_tokens=10).text


def test_dry_run_data_is_not_read_from_the_gold_folders():
    import inspect

    from app.eval import dryrun
    source = inspect.getsource(dryrun)
    assert "fixtures/ids" not in source and "fixtures/checks" not in source and "GOLD_DIR" not in source


# --- runner, plan, report ----------------------------------------------------------------------------------------


@pytest.fixture
def config_path(tmp_path):
    data = {"models": [{"name": "dry-a", "role": "hosted"}], "modes": ["gated", "ungated"], "repeats": 1,
            "temperature": 0.0, "max_repairs": 1, "budget": {"max_total_calls": 50, "max_total_tokens": 10_000_000}}
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


@pytest.fixture
def ids_only(monkeypatch):
    units = load_units()
    monkeypatch.setattr(runner, "select_units", lambda config: [units[u] for u in IDS_UNITS])


def test_plan_counts_worst_case_calls_and_refuses_over_budget(config_path, ids_only, capsys):
    assert cli.main(["--config", str(config_path), "plan"]) == 0
    out = capsys.readouterr().out
    assert "LLM calls worst case: 6" in out and "OK: within the call budget" in out  # 2 units x (1+1 + 1)
    data = yaml.safe_load(config_path.read_text())
    data["budget"]["max_total_calls"] = 5
    config_path.write_text(yaml.safe_dump(data))
    assert cli.main(["--config", str(config_path), "plan"]) == 2
    assert "REFUSED" in capsys.readouterr().out
    assert cli.main(["--config", str(config_path), "run", "--yes", "--dry-run"]) == 2


def test_run_requires_yes(config_path, ids_only, capsys):
    assert cli.main(["--config", str(config_path), "run", "--dry-run"]) == 2
    assert "pass --yes" in capsys.readouterr().out


def test_unconfigured_provider_is_a_clear_error(config_path, ids_only, capsys, monkeypatch):
    def boom(role, model=None):
        raise ProviderNotConfigured("hosted LLM not configured: set HOSTED_LLM_PROVIDER in .env")
    monkeypatch.setattr(cli, "get_provider", boom)
    assert cli.main(["--config", str(config_path), "run", "--yes", "--skip-preflight"]) == 2
    assert "dry-a (hosted) is not configured" in capsys.readouterr().out


def test_dry_run_end_to_end_is_bannered_and_never_written_to_docs(config_path, ids_only, tmp_path, capsys):
    runs = tmp_path / "runs"
    assert cli.main(["--config", str(config_path), "run", "--yes", "--dry-run", "--runs-dir", str(runs),
                     "--no-report"]) == 0
    [results] = list(runs.glob("dryrun-*/results.json"))
    data = json.loads(results.read_text())
    meta = data["meta"]
    assert meta["dry_run"] is True and meta["provider_classes"] == {"dry-a": "DryRunProvider"}
    assert {"run_id", "git_commit", "rulepack_hash", "temperature", "system_prompt_hashes"} <= meta.keys()
    assert not [k for k in json.dumps(meta).lower().split('"') if "api_key" in k]
    assert len(data["items"]) == 4 and {i["mode"] for i in data["items"]} == {"gated", "ungated"}
    assert all(set(i["score"]) >= {"valid", "dev_correct", "heldout_correct", "vacuous", "error"} for i in data["items"])
    assert list((results.parent / "attempts").rglob("*.json"))  # per-attempt records

    files = report.write_report(results, tmp_path / "out")
    for f in files:
        assert f.read_text(encoding="utf-8").splitlines()[0].count(report.BANNER) == 1
    assert "n < 30" in files[0].read_text(encoding="utf-8")
    summary = files[0].read_text(encoding="utf-8")
    assert "## Breakdown by tier" in summary and "## Breakdown by template" in summary
    assert "| dry-a | gated | hand-written | 2 |" in summary and {i["template"] for i in data["items"]} == {"hand-written"}
    for target in (report.DOCS_DIR, report.DOCS_DIR / "eval"):
        with pytest.raises(report.RefusedOutput):
            report.write_report(results, target)
    assert cli.main(["report", str(results), "--out", str(report.DOCS_DIR / "x")]) == 2
    assert not (report.DOCS_DIR / "x").exists()


def test_budget_caps_stop_a_run_and_are_recorded(config_path, ids_only, tmp_path):
    data = yaml.safe_load(config_path.read_text())
    data["budget"]["max_total_tokens"] = 1  # the first call already exceeds it
    config_path.write_text(yaml.safe_dump(data))
    run_dir = runner.run(runner.load_config(config_path), None, dry_run=True, runs_dir=tmp_path,
                         provider_factory=lambda name, mode: DryRunProvider(name))
    meta = json.loads((run_dir / "results.json").read_text())["meta"]
    assert meta["stopped_early"].startswith("budget exhausted") and meta["used"]["calls"] == 1


def test_provider_error_stops_the_run_with_partial_results_and_no_skipped_unit(config_path, ids_only, tmp_path):
    from app.llm.base import LLMError

    class FailsSecondCall(DryRunProvider):
        calls = 0

        def complete(self, *a, **kw):
            FailsSecondCall.calls += 1
            if FailsSecondCall.calls == 2:
                raise LLMError("openai_compat request failed after 9 attempt(s): HTTP 429: quota for sk-SECRET")
            return super().complete(*a, **kw)

    data = yaml.safe_load(config_path.read_text())
    data["modes"] = ["ungated"]
    config_path.write_text(yaml.safe_dump(data))
    run_dir = runner.run(runner.load_config(config_path), None, dry_run=True, runs_dir=tmp_path,
                         provider_factory=lambda name, mode: FailsSecondCall(name))
    result = json.loads((run_dir / "results.json").read_text())
    stopped = result["meta"]["stopped_early"]
    assert [i["unit_id"] for i in result["items"]] == [IDS_UNITS[0]]  # nothing after the failure, nothing skipped
    assert IDS_UNITS[1] in stopped and "429" in stopped and "sk-SECRET" not in stopped


@pytest.fixture
def real_like_results(config_path, ids_only, tmp_path):
    """A results.json shaped like a real run (dry-run answers, relabelled): slides must treat it as real."""
    run_dir = runner.run(runner.load_config(config_path), None, dry_run=True, runs_dir=tmp_path / "runs",
                         provider_factory=lambda name, mode: DryRunProvider(name))
    path = run_dir / "results.json"
    data = json.loads(path.read_text())
    data["meta"].update(dry_run=False, git_commit="abc123", run_id="20261118T000000Z-test")
    path.write_text(json.dumps(data))
    return path


def test_slides_refuse_dry_runs_and_dirty_commits(real_like_results, tmp_path, capsys):
    from app.eval import slides

    data = json.loads(real_like_results.read_text())
    for change in ({"dry_run": True}, {"git_commit": "abc123-dirty"}):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({**data, "meta": {**data["meta"], **change}}))
        with pytest.raises(report.RefusedOutput):
            slides.write_slides(bad, tmp_path / "out")
        assert cli.main(["slides", str(bad), "--out", str(tmp_path / "out")]) == 2
    assert not (tmp_path / "out").exists()


def test_slides_data_has_provenance_headline_breakdowns_and_caution(real_like_results, tmp_path):
    from app.eval import slides

    md, csv_path = slides.write_slides(real_like_results, tmp_path / "out")
    text = md.read_text(encoding="utf-8")
    for needle in ("20261118T000000Z-test", "abc123", "Rulepack hash", "dry-a (hosted)", "wrong_shipped",
                   "gated", "ungated", "Paired", "Breakdown by tier", "Breakdown by template", "All units",
                   "Distinct rules only", "Fallback items: 0", "Skipped models: none", "n is small", "no model difference may be claimed"):
        assert needle in text, needle
    assert "[" in text and "%" in text  # Wilson intervals
    rows = list(csv.reader(csv_path.open(encoding="utf-8")))
    assert rows[0][:4] == ["run_id", "view", "model", "mode"]
    assert {r[1] for r in rows[1:]} == {"all_units", "distinct_rules"}
    assert all(r[0] == "20261118T000000Z-test" for r in rows[1:])


# --- unit-level view across repeats (Phase 12b) -------------------------------------------------------------


def rep_item(unit, repeat, shipped, correct, model="m", mode="gated"):
    return {"model": model, "mode": mode, "unit_id": unit, "repeat": repeat, "tier": "ids", "template": "t",
            "shipped": shipped, "outcome": "accepted" if shipped else "needs_human",
            "score": {"valid": True, "dev_correct": True, "heldout_correct": correct}}


def test_unit_metrics_shares_stability_and_unit_wrong_shipped():
    from app.eval.metrics import unit_metrics

    items = [rep_item("a", r, True, True) for r in range(3)]                       # stable, always right
    items += [rep_item("b", 0, True, False), rep_item("b", 1, True, True), rep_item("b", 2, True, True)]  # varied
    items += [rep_item("c", r, False, False) for r in range(3)]                    # stable, never shipped
    m = unit_metrics(items)
    assert m["shares"] == {"a": (3, 3), "b": (2, 3), "c": (0, 3)}
    assert (m["n_units"], m["stable"], m["varied"]) == (3, 2, 1)
    w = m["wrong_shipped_units"]
    assert (w.k, w.n) == (1, 2)  # b shipped a wrong rule once; c never shipped, so it is not in n
    assert w.wilson == wilson_interval(1, 2)


@pytest.fixture
def repeated_results(config_path, ids_only, tmp_path):
    data = yaml.safe_load(config_path.read_text())
    data["repeats"] = 2
    config_path.write_text(yaml.safe_dump(data))
    run_dir = runner.run(runner.load_config(config_path), None, dry_run=True, runs_dir=tmp_path / "runs",
                         provider_factory=lambda name, mode: DryRunProvider(name))
    path = run_dir / "results.json"
    data = json.loads(path.read_text())
    data["meta"].update(dry_run=False, git_commit="abc123", run_id="20261118T000000Z-rep")
    path.write_text(json.dumps(data))
    return path


UNIT_LEVEL_NEEDLES = ("Items, correlated across repeats", "Unit level", "Stability across repeats",
                      "identical in every repeat", "varied", "wrong_shipped per unit", "held-out-correct share per unit")


def test_report_and_slides_have_the_unit_level_view(repeated_results, tmp_path):
    from app.eval import slides

    summary = report.write_report(repeated_results, tmp_path / "r")[0].read_text(encoding="utf-8")
    md, csv_path = slides.write_slides(repeated_results, tmp_path / "s")
    text = md.read_text(encoding="utf-8")
    for needle in UNIT_LEVEL_NEEDLES:
        assert needle in summary and needle in text, needle
    assert f"| {IDS_UNITS[0]} |" in summary  # one row per unit
    rows = list(csv.reader(csv_path.open(encoding="utf-8")))
    assert {"unit_wrong_shipped", "stability"} <= {r[4] for r in rows[1:]}
