import csv
import shutil

import pytest

from app.corpus import cli, review
from app.eval.metrics import review_share
from app.fixtures.builders import REPO_ROOT
from app.rulepack.loader import DEFAULT_PACK, load_rulepack

UNITS_YAML = REPO_ROOT / "rules" / "corpus" / "rule-units.yaml"


@pytest.fixture
def work(tmp_path):
    units = tmp_path / "rule-units.yaml"
    shutil.copy(UNITS_YAML, units)
    pack = tmp_path / "pack"
    shutil.copytree(DEFAULT_PACK, pack)
    sheet = tmp_path / "sheet.csv"
    review.export_sheet(units, pack, sheet, tmp_path / "sheet.md")
    return units, pack, sheet


def rows_of(sheet):
    with open(sheet, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def fill(sheet, decisions: dict[str, dict]):
    rows = rows_of(sheet)
    for r in rows:
        r.update(decisions.get(r["unit_id"], {}))
    with open(sheet, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=review.COLUMNS)
        w.writeheader()
        w.writerows(rows)


def test_export_is_excel_friendly_with_empty_reviewer_columns(work):
    units, pack, sheet = work
    assert sheet.read_bytes().startswith(b"\xef\xbb\xbf")  # UTF-8 BOM for Excel
    rows = rows_of(sheet)
    ids = [u.id for u in review.load_units_yaml(units)]
    first = list(review.READING_DEPENDENT)  # reading-dependent units lead; the rest keep the units.yaml order
    assert [r["unit_id"] for r in rows] == first + [i for i in ids if i not in first]
    assert list(rows[0]) == review.COLUMNS
    assert all(r[c] == "" for r in rows for c in review.REVIEW_COLUMNS)
    by_id = {r["unit_id"]: r for r in rows}
    assert by_id["MBBL2016-4.5.2#1"]["threshold"].startswith("at least 1.8 m2")
    assert by_id["MBBL2016-5.4.1#b"]["threshold"] == "at least 1.0 m"
    assert by_id["MBBL2016-5.4.2#1"]["threshold"] == "none"
    assert by_id["MBBL2016-5.4.1#b"]["scope"].startswith("IfcDoor where Pset_DoorCommon.FireExit is TRUE")
    assert "5.4.1 Doorways" in by_id["MBBL2016-5.4.1#b"]["clause_text"]
    assert (sheet.parent / "sheet.md").read_text(encoding="utf-8").startswith("# NIYAM rule review sheet")


def test_round_trip_accept_modify_reject_updates_units_and_manifest(work):
    units, pack, sheet = work
    fill(sheet, {
        "MBBL2016-4.5.2#1": {"decision": "accept", "reviewer_name": "A. Reviewer", "reviewed_on": "2026-11-05"},
        "MBBL2016-5.4.1#b": {"decision": "Modify", "reviewer_name": "A. Reviewer", "reviewed_on": "2026-11-05",
                             "corrected_threshold": "1.0 m clear width", "comments": "use clear width"},
        "MBBL2016-5.4.2#1": {"decision": "reject", "reviewer_name": "A. Reviewer", "comments": "out of scope"},
    })
    result = review.import_sheet(sheet, units, pack, today="2026-11-06")
    assert sorted(result.changed) == ["MBBL2016-4.5.2#1", "MBBL2016-5.4.1#b", "MBBL2016-5.4.2#1"]
    u = {x.id: x for x in review.load_units_yaml(units)}
    assert (u["MBBL2016-4.5.2#1"].human_reviewed, u["MBBL2016-4.5.2#1"].reviewer,
            u["MBBL2016-4.5.2#1"].reviewed_on) == (True, "A. Reviewer", "2026-11-05")
    assert u["MBBL2016-5.4.1#b"].status == "needs_rework" and not u["MBBL2016-5.4.1#b"].human_reviewed
    assert "REVIEW modify (A. Reviewer, 2026-11-05): corrected_threshold=1.0 m clear width; comments=use clear " \
           "width" in u["MBBL2016-5.4.1#b"].notes
    assert u["MBBL2016-5.4.2#1"].status == "rejected" and u["MBBL2016-5.4.2#1"].reviewed_on == "2026-11-06"
    rules = {r.unit_id: r for r in load_rulepack(pack).manifest.rules}
    assert (rules["MBBL2016-4.5.2#1"].human_reviewed, rules["MBBL2016-4.5.2#1"].reviewer) == (True, "A. Reviewer")
    assert rules["MBBL2016-5.4.1#b"].human_reviewed is False and rules["MBBL2016-5.4.1#b"].reviewer is None
    # the modified rule itself is untouched: same scope, same artifact
    original = {r.unit_id: r for r in load_rulepack(DEFAULT_PACK).manifest.rules}
    assert rules["MBBL2016-5.4.1#b"].scope == original["MBBL2016-5.4.1#b"].scope
    assert review_share(review.load_units_yaml(units)).k == 2 and review_share(review.load_units_yaml(units)).n == 3


def test_import_is_idempotent(work):
    units, pack, sheet = work
    fill(sheet, {"MBBL2016-4.5.2#1": {"decision": "accept", "reviewer_name": "R", "reviewed_on": "2026-11-05"}})
    review.import_sheet(sheet, units, pack)
    before = (units.read_text(encoding="utf-8"), (pack / "manifest.yaml").read_text(encoding="utf-8"))
    again = review.import_sheet(sheet, units, pack)
    assert again.changed == [] and again.unchanged == ["MBBL2016-4.5.2#1"]
    assert (units.read_text(encoding="utf-8"), (pack / "manifest.yaml").read_text(encoding="utf-8")) == before


def test_a_different_decision_needs_force(work):
    units, pack, sheet = work
    fill(sheet, {"MBBL2016-4.5.2#1": {"decision": "accept", "reviewer_name": "R", "reviewed_on": "2026-11-05"}})
    review.import_sheet(sheet, units, pack)
    fill(sheet, {"MBBL2016-4.5.2#1": {"decision": "reject", "reviewer_name": "S", "reviewed_on": "2026-11-07"}})
    with pytest.raises(review.ReviewImportError, match="already has decision 'accept' by 'R'; use --force"):
        review.import_sheet(sheet, units, pack)
    review.import_sheet(sheet, units, pack, force=True)
    [u] = [x for x in review.load_units_yaml(units) if x.id == "MBBL2016-4.5.2#1"]
    assert (u.status, u.reviewer, u.human_reviewed) == ("rejected", "S", False)


def test_validation_errors_name_the_line_and_change_nothing(work, capsys):
    units, pack, sheet = work
    rows = rows_of(sheet)
    rows[0].update(decision="maybe", reviewer_name="R")
    rows[1].update(decision="accept", reviewer_name="")
    rows[2].update(decision="accept", reviewer_name="R", reviewed_on="5/11/2026")
    rows.append({**rows[3], "unit_id": "MBBL2016-9.9#z", "decision": "accept", "reviewer_name": "R"})
    with open(sheet, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=review.COLUMNS)
        w.writeheader()
        w.writerows(rows)
    before = units.read_text(encoding="utf-8")
    with pytest.raises(review.ReviewImportError) as e:
        review.import_sheet(sheet, units, pack)
    joined = "\n".join(e.value.errors)
    assert "decision 'maybe'" in joined and "has no reviewer_name" in joined and "must be YYYY-MM-DD" in joined
    assert "unknown unit_id 'MBBL2016-9.9#z'" in joined and all(err.startswith("row ") for err in e.value.errors)
    assert units.read_text(encoding="utf-8") == before
    with pytest.raises(SystemExit):
        cli.main(["review-import", str(sheet), "--units-yaml", str(units), "--pack", str(pack)])
    assert "nothing changed" in capsys.readouterr().out


def test_committed_review_sheet_is_current():
    rows = rows_of(REPO_ROOT / "docs" / "review" / "review-sheet.csv")
    assert len(rows) == 27 and all(r["decision"] == "" for r in rows)  # 6 hand-written + 19 MBBL spec + 2 TGBR spec units


def test_review_import_reminds_that_the_corpus_db_needs_unit_import(work, capsys):
    units, pack, sheet = work
    fill(sheet, {"MBBL2016-4.8.1#1": {"decision": "modify", "reviewer_name": "R", "reviewed_on": "2026-11-05",
                                      "comments": "store rooms in non-residential buildings too?"}})
    cli.main(["review-import", str(sheet), "--units-yaml", str(units), "--pack", str(pack)])
    out = capsys.readouterr().out
    assert "changed: MBBL2016-4.8.1#1" in out and "run `python -m app.corpus.cli unit-import`" in out


def test_spec_units_appear_in_the_sheet_with_their_clause_and_threshold(work):
    rows = {r["unit_id"]: r for r in rows_of(work[2])}
    store = rows["MBBL2016-4.8.2#1"]
    assert (store["page"], store["threshold"]) == ("72", "at least 3 m2 (computed: space_floor_area_m2)")
    assert "4.8.2 Size" in store["clause_text"] and "not in a rulepack" in store["scope"]
    assert "residential building" in store["machine_reading"]


def test_reviewer_guide_names_every_known_concern():
    guide = (REPO_ROOT / "docs" / "review" / "REVIEWER_GUIDE.md").read_text(encoding="utf-8")
    for unit_id in ("4.24.7.2#b", "4.8.2#1", "4.10.4#a", "4.5.2#2", "4.24.7.2#c", "4.24.7.2#f", "5.4.2#1"):
        assert unit_id in guide
    assert len(guide.split()) < 1300  # about two pages


def test_reading_dependent_units_come_first_with_a_note(work):
    rows = rows_of(work[2])
    assert [r["unit_id"] for r in rows[:2]] == ["MBBL2016-4.8.2#1", "MBBL2016-5.4.1#b2"]
    assert "residential" in rows[0]["reading_dependent"] and "FireExit" in rows[1]["reading_dependent"]
    assert all(r["reading_dependent"] == "" for r in rows[2:])
    md = (work[2].with_suffix(".md")).read_text(encoding="utf-8") if work[2].with_suffix(".md").exists() else ""
    assert not md or "Reading-dependent" in md


def test_committed_sheet_lists_reading_dependent_units_first():
    rows = rows_of(REPO_ROOT / "docs" / "review" / "review-sheet.csv")
    assert [r["unit_id"] for r in rows[:2]] == ["MBBL2016-4.8.2#1", "MBBL2016-5.4.1#b2"]


def test_sheet_has_a_source_column(work):
    rows = rows_of(work[2])
    assert {r["source"] for r in rows} == {"MoHUA Model Building Bye-Laws 2016",
                                           "Telangana Building Rules 2012 (G.O.Ms.No.168, original text, amendments not applied)"}
    assert list(rows[0])[:2] == ["unit_id", "source"]
