import shutil

import pydantic
import pytest
import yaml

from app.audit.engine import audit
from app.corpus import repository as repo
from app.corpus.models import Clause
from app.fixtures import geo_builders as gb
from app.fixtures.builders import REPO_ROOT, fixture_pair, safe_name
from app.fixtures.gold_ids import load_units
from app.rulepack import cli
from app.rulepack.loader import RULEPACK_DIR, RulepackError, load_rulepack, scope_from_check
from app.rulepack.models import Manifest
from app.verifier import sandbox

V0 = RULEPACK_DIR / "v0"
CHECKS = REPO_ROOT / "fixtures" / "checks"
AREA, HEIGHT, STAIR = gb.UNITS


def gold(unit_id):
    return (CHECKS / f"{safe_name(unit_id)}.py").read_text(encoding="utf-8")


# --- scope derived from the check's code -----------------------------------------------------------------------


@pytest.mark.parametrize("unit_id, ifc_class, measure, data", [
    (AREA, "IfcSpace", "space_floor_area_m2", ["pset:Pset_SpaceCommon.Category"]),
    (HEIGHT, "IfcSpace", "element_height_m", ["pset:Pset_SpaceCommon.Category"]),
    (STAIR, "IfcStairFlight", "stair_flight_width_m", ["pset:Pset_BuildingCommon.OccupancyType"]),
])
def test_scope_is_read_from_the_check_code(unit_id, ifc_class, measure, data):
    scope = scope_from_check(gold(unit_id))
    assert (scope.ifc_class, scope.selector, scope.measures) == (ifc_class, None, [measure])
    assert [d.key for d in scope.required_data] == data


def test_scope_needs_exactly_one_class():
    with pytest.raises(RulepackError, match="exactly one"):
        scope_from_check("def check(model, helpers):\n    return []\n")


# --- manifest ---------------------------------------------------------------------------------------------------


def _manifest_dict():
    return yaml.safe_load((V0 / "manifest.yaml").read_text(encoding="utf-8"))


def test_manifest_requires_the_artifact_matching_the_tier():
    data = _manifest_dict()
    geo = next(r for r in data["rules"] if r["tier"] == "geometric")
    for broken in ({**geo, "check_file": None}, {**geo, "ids_file": "ids/x.ids"}):
        bad = _manifest_dict()
        bad["rules"] = [{k: v for k, v in broken.items() if v is not None}]
        with pytest.raises(pydantic.ValidationError):
            Manifest(**bad)
    ids = dict(next(r for r in data["rules"] if r["tier"] == "ids"))
    ids.pop("ids_file")
    with pytest.raises(pydantic.ValidationError):
        Manifest(**{"version": "v", "rules": [ids]})


def test_v0_contains_the_three_geometric_rules_as_draft():
    pack = load_rulepack(V0)
    geo = {r.unit_id: r for r in pack.manifest.rules if r.tier == "geometric"}
    assert set(geo) == set(gb.UNITS)
    for unit_id, rule in geo.items():
        assert rule.human_reviewed is False and rule.check_file == f"checks/{safe_name(unit_id)}.py"
        assert (V0 / rule.check_file).read_text(encoding="utf-8") == gold(unit_id)
        assert " ".join(rule.rule_text.split()) in " ".join(rule.clause_text.split())
    assert {r.unit_id for r in pack.manifest.rules if r.tier == "ids"} == {
        "MBBL2016-5.4.2#1", "MBBL2016-5.4.1#b", "MBBL2016-5.4.1#c"}


def test_loading_a_pack_revalidates_the_check_code(tmp_path):
    pack = tmp_path / "pack"
    shutil.copytree(V0, pack)
    path = pack / f"checks/{safe_name(AREA)}.py"
    path.write_text(path.read_text(encoding="utf-8").replace("import math", "import os"), encoding="utf-8")
    with pytest.raises(RulepackError, match="ast_allowlist.*import os"):
        load_rulepack(pack)


# --- rulepack add --gate dispatches by tier ---------------------------------------------------------------------


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "corpus.db"
    conn = repo.connect(path)
    repo.init_db(conn)
    units = load_units()
    for unit_id in gb.UNITS:
        unit = units[unit_id]
        clause = Clause(id=unit.clause_id, source_doc="MBBL-2016", clause_number=unit.clause_id.split("-")[1],
                        text=f"{unit.clause_id}\n{unit.text}", page=70, section_path=["Chapter 4"])
        repo.upsert_clause(conn, clause)
        repo.upsert_unit(conn, unit)
    conn.close()
    return path


def test_add_gate_accepts_a_good_check_and_copies_it(db, tmp_path, capsys):
    pack = tmp_path / "pack"
    code = cli.main(["--db", str(db), "--pack", str(pack), "add", AREA, str(CHECKS / f"{safe_name(AREA)}.py"), "--gate"])
    assert code == 0 and "ACCEPTED" in capsys.readouterr().out
    pack_rules = load_rulepack(pack).manifest.rules
    [rule] = pack_rules
    assert (rule.tier, rule.check_file, rule.scope.ifc_class, rule.human_reviewed) == (
        "geometric", f"checks/{safe_name(AREA)}.py", "IfcSpace", False)
    assert (pack / rule.check_file).read_text(encoding="utf-8") == gold(AREA)


def test_add_gate_rejects_a_bad_check_and_leaves_the_pack_alone(db, tmp_path, capsys):
    pack = tmp_path / "pack"
    bad = tmp_path / "bad.py"
    bad.write_text(gold(AREA).replace("import math", "import os"), encoding="utf-8")
    code = cli.main(["--db", str(db), "--pack", str(pack), "add", AREA, str(bad), "--gate"])
    assert code == 1 and "REJECTED at ast_allowlist" in capsys.readouterr().out
    assert not (pack / "checks").exists() and not (pack / "manifest.yaml").exists()


# --- the audit runs geometric rules through the sandbox ---------------------------------------------------------


def rule_of(report, unit_id):
    [r] = [r for r in report.rules if r.unit_id == unit_id]
    return r


@pytest.mark.parametrize("length_unit", ["mm", "m"])
def test_audit_maps_findings_with_measured_and_required_values(length_unit):
    pair = fixture_pair(AREA, length_unit=length_unit)
    report = audit(pair.fail_path, load_rulepack(V0))
    result = rule_of(report, AREA)
    verdicts = {e.name: e.verdict for e in result.elements}
    assert verdicts == {"space_under_test": "failed", "control_store": "out_of_scope"}
    [failed] = [e for e in result.elements if e.verdict == "failed"]
    assert failed.reason_plain == "Computed floor area is 1.68 m2; this rule requires at least 1.8 m2."
    assert failed.reason_raw and failed.express_id > 0
    assert report.status == "noncompliant"
    assert rule_of(report, HEIGHT).elements and rule_of(report, STAIR).elements == []  # no flights: nothing to check


def test_sandbox_is_not_started_for_rules_with_no_elements_in_the_model(monkeypatch):
    monkeypatch.setattr(sandbox, "run_check", lambda *a, **k: pytest.fail("no element is in scope"))
    report = audit(REPO_ROOT / "fixtures" / "samples" / "sample_a_mm.ifc", load_rulepack(V0))
    assert [rule_of(report, u).status for u in gb.UNITS] == ["nothing_checked"] * 3


def test_a_timeout_is_an_error_not_a_pass():
    pair = fixture_pair(STAIR)
    report = audit(pair.pass_path, load_rulepack(V0), geometric_timeout_s=0.05)
    result = rule_of(report, STAIR)
    assert result.status == "error" and "timed out" in result.error and result.elements == []
    assert report.status != "compliant"
    assert report.summary.rules_with_errors == 3 - 2  # only the stair rule has elements in this model


def test_a_crashing_check_is_an_error_and_other_rules_still_run(tmp_path):
    pack = tmp_path / "pack"
    shutil.copytree(V0, pack)
    (pack / f"checks/{safe_name(AREA)}.py").write_text(
        "def check(model, helpers):\n    return 1 / 0\n", encoding="utf-8")
    manifest = yaml.safe_load((pack / "manifest.yaml").read_text(encoding="utf-8"))
    for r in manifest["rules"]:
        if r["unit_id"] == AREA:  # the scope is only a hint for geometric rules; the class still has to exist
            r["scope"]["ifc_class"] = "IfcSpace"
    (pack / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    report = audit(fixture_pair(AREA).pass_path, load_rulepack(pack))
    broken = rule_of(report, AREA)
    assert broken.status == "error" and "ZeroDivisionError" in broken.error
    assert rule_of(report, HEIGHT).status != "error"  # the other rules were not dropped
    assert report.status != "compliant"


def test_error_rules_show_up_in_the_html_report():
    from app.audit.report_html import render_html

    report = audit(fixture_pair(STAIR).pass_path, load_rulepack(V0), geometric_timeout_s=0.05)
    html = render_html(report)
    assert "timed out" in html and "error" in html
