import shutil

import pydantic
import pytest
import yaml

from app.corpus import repository as repo
from app.corpus.models import Clause
from app.fixtures.builders import safe_name
from app.fixtures.gold_ids import GOLD_DIR, load_units
from app.rulepack import cli
from app.rulepack.loader import RULEPACK_DIR, RulepackError, load_rulepack, scope_from_ids
from app.rulepack.models import Manifest

V0 = RULEPACK_DIR / "v0"


def gold_path(unit_id):
    return GOLD_DIR / f"{safe_name(unit_id)}.ids"


def test_v0_rulepack_loads_with_expected_scopes():
    pack = load_rulepack(V0)
    rules = {r.unit_id: r for r in pack.manifest.rules}
    rules = {u: r for u, r in rules.items() if r.tier == "ids"}  # the geometric rules are covered separately
    assert set(rules) == {"MBBL2016-5.4.2#1", "MBBL2016-5.4.1#b", "MBBL2016-5.4.1#c"}
    for r in rules.values():
        assert r.human_reviewed is False and r.tier == "ids" and r.severity == "error"
        assert r.scope.ifc_class == "IfcDoor"
        assert (r.scope.selector.pset, r.scope.selector.property, r.scope.selector.value) == (
            "Pset_DoorCommon", "FireExit", True)
        assert " ".join(r.rule_text.split()) in " ".join(r.clause_text.split())  # verbatim up to line breaks
    data = {u: [d.key for d in r.scope.required_data] for u, r in rules.items()}
    assert data == {
        "MBBL2016-5.4.2#1": ["pset:Pset_DoorCommon.FireExit", "attribute:OperationType"],
        "MBBL2016-5.4.1#b": ["pset:Pset_DoorCommon.FireExit", "qto:Qto_DoorBaseQuantities.Width"],
        "MBBL2016-5.4.1#c": ["pset:Pset_DoorCommon.FireExit", "attribute:OperationType"],
    }


def test_scope_is_derived_from_the_ids_applicability_and_requirements():
    scope = scope_from_ids(gold_path("MBBL2016-5.4.1#b").read_text(encoding="utf-8"))
    assert scope.ifc_class == "IfcDoor"
    assert scope.selector.value is True
    assert [d.key for d in scope.required_data] == ["pset:Pset_DoorCommon.FireExit", "qto:Qto_DoorBaseQuantities.Width"]


def _manifest_dict():
    return yaml.safe_load((V0 / "manifest.yaml").read_text(encoding="utf-8"))


def test_manifest_rejects_duplicate_unit_ids():
    data = _manifest_dict()
    data["rules"].append(dict(data["rules"][0]))
    with pytest.raises(pydantic.ValidationError, match="duplicate"):
        Manifest(**data)


def test_manifest_rejects_unknown_fields_and_bad_required_data():
    data = _manifest_dict()
    data["rules"][0]["scope"]["required_data"].append({"pset": "X", "qto": "Y", "name": "Z"})
    with pytest.raises(pydantic.ValidationError, match="exactly one"):
        Manifest(**data)


def _copy_pack(tmp_path):
    dst = tmp_path / "v0"
    shutil.copytree(V0, dst)
    return dst


def test_loader_rejects_missing_ids_file(tmp_path):
    pack = _copy_pack(tmp_path)
    next((pack / "ids").glob("*.ids")).unlink()
    with pytest.raises(RulepackError, match="missing"):
        load_rulepack(pack)


def test_loader_rejects_ids_that_fails_static_gate_stages(tmp_path):
    pack = _copy_pack(tmp_path)
    target = pack / "ids" / f"{safe_name('MBBL2016-5.4.1#b')}.ids"
    xml = target.read_text(encoding="utf-8")
    start = xml.index('<property dataType="IFCLENGTHMEASURE"')
    end = xml.index("</property>", start) + len("</property>")
    target.write_text(xml[:start] + "<attribute><name><simpleValue>OverallWidth</simpleValue></name><value>"
                      '<xs:restriction base="xs:double"><xs:minInclusive value="1.0"/></xs:restriction>'
                      "</value></attribute>" + xml[end:], encoding="utf-8")
    with pytest.raises(RulepackError, match="unit_safe_bounds"):
        load_rulepack(pack)


# --- CLI ----------------------------------------------------------------------


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "corpus.db"
    conn = repo.connect(path)
    repo.init_db(conn)
    unit = load_units()["MBBL2016-5.4.1#b"]
    repo.upsert_clause(conn, Clause(
        id=unit.clause_id, source_doc="MBBL-2016", clause_number="5.4.1", page=100,
        text="5.4.1 Doorways\nb. No exit doorway shall be less than 1m in width. Doorways shall be not less\n"
             "than 2 m in height.", section_path=["Chapter 5"]))
    repo.upsert_unit(conn, unit)
    conn.close()
    return path


def test_cli_add_accepts_gold_and_writes_manifest_entry(tmp_path, db, capsys):
    pack = tmp_path / "pack"
    code = cli.main(["--db", str(db), "--pack", str(pack), "add", "MBBL2016-5.4.1#b",
                     str(gold_path("MBBL2016-5.4.1#b")), "--gate"])
    assert code == 0
    [rule] = load_rulepack(pack).manifest.rules
    assert rule.unit_id == "MBBL2016-5.4.1#b" and rule.page == 100 and rule.human_reviewed is False
    assert rule.clause_text.startswith("5.4.1 Doorways")
    assert (pack / rule.ids_file).read_text(encoding="utf-8") == gold_path("MBBL2016-5.4.1#b").read_text(encoding="utf-8")


def test_cli_add_rejects_ids_that_fails_the_gate(tmp_path, db, capsys):
    pack = tmp_path / "pack"
    lenient = tmp_path / "lenient.ids"
    lenient.write_text(gold_path("MBBL2016-5.4.1#b").read_text(encoding="utf-8").replace(
        '<xs:minInclusive value="1.0"', '<xs:minInclusive value="0.75"'), encoding="utf-8")
    code = cli.main(["--db", str(db), "--pack", str(pack), "add", "MBBL2016-5.4.1#b", str(lenient), "--gate"])
    assert code == 1
    assert "verdict_fail_fixture" in capsys.readouterr().out
    assert not (pack / "manifest.yaml").exists()


def test_cli_add_requires_gate_flag(tmp_path, db):
    with pytest.raises(SystemExit, match="--gate"):
        cli.main(["--db", str(db), "--pack", str(tmp_path / "p"), "add", "MBBL2016-5.4.1#b",
                  str(gold_path("MBBL2016-5.4.1#b"))])


def test_cli_list_and_validate(capsys):
    assert cli.main(["--pack", str(V0), "list"]) == 0
    out = capsys.readouterr().out
    assert "MBBL2016-5.4.2#1" in out and "reviewed=False" in out
    assert cli.main(["--pack", str(V0), "validate"]) == 0
    assert "6 rule(s) valid" in capsys.readouterr().out
