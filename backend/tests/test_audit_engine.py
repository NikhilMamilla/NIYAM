import shutil

import pytest

from app.audit.engine import InvalidIfcError, audit, overall_status
from app.audit.models import Counts
from app.fixtures.builders import add_door, new_model
from app.rulepack.loader import DEFAULT_PACK, load_rulepack
from tests.test_ids_gate import PROHIBITED_SPEC_5_4_2

R542, R541B, R541C = "MBBL2016-5.4.2#1", "MBBL2016-5.4.1#b", "MBBL2016-5.4.1#c"


def model_file(tmp_path, doors, unit="mm", name="m.ifc"):
    f, storey = new_model("audit test", length_unit=unit)
    for door_name, kwargs in doors:
        add_door(f, storey, door_name, **({"height": 2.1 if unit == "m" else 2100.0} | kwargs))
    path = tmp_path / name
    f.write(str(path))
    return path


def verdicts(report):
    return {(r.unit_id, e.name): e.verdict for r in report.rules for e in r.elements}


@pytest.fixture(scope="module")
def pack():
    return load_rulepack(DEFAULT_PACK)


@pytest.mark.parametrize("unit, scale", [("mm", 1000.0), ("m", 1.0)])
def test_verdicts_per_rule_in_mm_and_m(tmp_path, pack, unit, scale):
    path = model_file(tmp_path, [
        ("ok", {"fire_exit": True, "width": 1.0 * scale}),
        ("narrow", {"fire_exit": True, "width": 0.9 * scale}),
        ("revolving", {"fire_exit": True, "width": 1.2 * scale, "operation_type": "REVOLVING"}),
        ("sliding", {"fire_exit": True, "width": 1.2 * scale, "operation_type": "SLIDING_TO_RIGHT"}),
        ("not_exit_revolving_narrow", {"fire_exit": False, "width": 0.7 * scale, "operation_type": "REVOLVING"}),
    ], unit=unit)
    v = verdicts(audit(path, pack))
    assert v[(R542, "ok")] == v[(R541B, "ok")] == v[(R541C, "ok")] == "passed"
    assert (v[(R542, "narrow")], v[(R541B, "narrow")], v[(R541C, "narrow")]) == ("passed", "failed", "passed")
    assert (v[(R542, "revolving")], v[(R541C, "revolving")]) == ("failed", "passed")
    assert (v[(R542, "sliding")], v[(R541C, "sliding")]) == ("passed", "failed")
    assert {v[(r, "not_exit_revolving_narrow")] for r in (R542, R541B, R541C)} == {"out_of_scope"}


def test_failed_element_carries_ids_reason(tmp_path, pack):
    report = audit(model_file(tmp_path, [("narrow", {"fire_exit": True, "width": 900.0})]), pack)
    [rule] = [r for r in report.rules if r.unit_id == R541B]
    [element] = rule.elements
    assert element.verdict == "failed" and element.ifc_class == "IfcDoor" and element.global_id
    assert "0.9" in element.reason or "does not match" in element.reason
    assert rule.status == "noncompliant" and report.status == "noncompliant"


def test_missing_selector_and_required_data_are_unchecked_never_passed(tmp_path, pack):
    report = audit(model_file(tmp_path, [
        ("no_fire_exit", {"fire_exit": None}),
        ("no_width", {"fire_exit": True, "width": None}),
        ("no_operation", {"fire_exit": True, "operation_type": "NOTDEFINED"}),
    ]), pack)
    elements = {(r.unit_id, e.name): e for r in report.rules for e in r.elements}
    for rule in (R542, R541B, R541C):
        e = elements[(rule, "no_fire_exit")]
        assert e.verdict == "unchecked" and "Pset_DoorCommon.FireExit" in e.reason
    assert elements[(R541B, "no_width")].verdict == "unchecked"
    assert "Qto_DoorBaseQuantities.Width" in elements[(R541B, "no_width")].reason
    assert elements[(R542, "no_width")].verdict == "passed"
    assert elements[(R542, "no_operation")].verdict == "unchecked"
    assert "OperationType" in elements[(R542, "no_operation")].reason
    assert elements[(R541B, "no_operation")].verdict == "passed"
    assert report.status == "incomplete"


def test_model_without_fire_exit_data_is_never_compliant(tmp_path, pack):
    report = audit(model_file(tmp_path, [("a", {"fire_exit": None}), ("b", {"fire_exit": None})]), pack)
    assert report.status == "incomplete"
    assert all(r.status == "incomplete" and r.counts.passed == 0 for r in report.rules)


def test_model_without_doors_is_nothing_checked(tmp_path, pack):
    report = audit(model_file(tmp_path, []), pack)
    assert report.status == "nothing_checked"
    assert all(r.status == "nothing_checked" for r in report.rules)


def test_only_out_of_scope_doors_is_nothing_checked(tmp_path, pack):
    report = audit(model_file(tmp_path, [("internal", {"fire_exit": False})]), pack)
    assert report.status == "nothing_checked"


def test_overall_status_rules():
    assert overall_status(Counts(failed=1, unchecked=3, passed=5)) == "noncompliant"
    assert overall_status(Counts(unchecked=1, passed=5)) == "incomplete"
    assert overall_status(Counts(passed=1, out_of_scope=4)) == "compliant"
    assert overall_status(Counts(out_of_scope=4)) == "nothing_checked"
    assert overall_status(Counts()) == "nothing_checked"


def test_prohibited_spec_rules_are_audited(tmp_path):
    pack_dir = tmp_path / "pack"
    shutil.copytree(DEFAULT_PACK, pack_dir)
    (pack_dir / "ids" / "MBBL2016-5_4_2_1.ids").write_text(PROHIBITED_SPEC_5_4_2, encoding="utf-8")
    report = audit(model_file(tmp_path, [
        ("swing", {"fire_exit": True}), ("revolving", {"fire_exit": True, "operation_type": "REVOLVING"}),
    ]), load_rulepack(pack_dir))
    v = verdicts(report)
    assert (v[(R542, "swing")], v[(R542, "revolving")]) == ("passed", "failed")


def test_cli_run_prints_summary_and_writes_report(tmp_path, capsys):
    from app.audit import cli

    path = model_file(tmp_path, [("narrow", {"fire_exit": True, "width": 900.0}), ("x", {"fire_exit": None})])
    code = cli.main(["run", str(path), "--out", str(tmp_path / "out")])
    out = capsys.readouterr().out
    assert code == 0
    assert "MBBL2016-5.4.1#b" in out and "noncompliant" in out and "overall" in out
    for name in ("report.json", "report.html", "issues.bcf"):
        assert (tmp_path / "out" / name).stat().st_size > 0


def test_cli_run_reports_invalid_file(tmp_path, capsys):
    from app.audit import cli

    bad = tmp_path / "bad.ifc"
    bad.write_text("nope")
    assert cli.main(["run", str(bad)]) == 2
    assert "could not read IFC" in capsys.readouterr().out


@pytest.mark.parametrize("content", [b"not an ifc file at all", b"", b"ISO-10303-21;\nHEADER;\n"])
def test_malformed_file_raises_clear_error(tmp_path, pack, content):
    path = tmp_path / "bad.ifc"
    path.write_bytes(content)
    with pytest.raises(InvalidIfcError, match="could not read IFC"):
        audit(path, pack)
