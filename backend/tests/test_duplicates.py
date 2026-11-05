import json

import pytest

from app.corpus import review
from app.corpus.models import RuleUnit
from app.eval import report
from app.eval.metrics import distinct_only
from app.fixtures.builders import REPO_ROOT
from app.fixtures.gold_ids import check_duplicates, load_units
from app.specgen.models import load_all

DUPLICATES = {"MBBL2016-4.24.7.2#b": "MBBL2016-5.4.1#b", "MBBL2016-4.24.7.2#c": "MBBL2016-5.4.1#c",
              "MBBL2016-4.24.7.2#f": "MBBL2016-5.4.2#1"}


def unit(uid, dup=None):
    return RuleUnit(id=uid, clause_id=uid.split("#")[0], text="t", tier="ids", duplicate_of=dup)


def test_the_three_known_duplicates_are_tagged_in_units_and_specs():
    units = load_units()
    assert {u.id: u.duplicate_of for u in units.values() if u.duplicate_of} == DUPLICATES
    assert {s.unit_id: s.duplicate_of for s in load_all() if s.duplicate_of} == DUPLICATES


@pytest.mark.parametrize("units, message", [
    ([unit("A#1", "Z#9")], "does not exist"),
    ([unit("A#1", "A#1")], "itself"),
    ([unit("A#1", "B#1"), unit("B#1", "C#1"), unit("C#1")], "chain"),
])
def test_duplicate_of_is_validated(units, message):
    with pytest.raises(ValueError, match=message):
        check_duplicates(units)
    check_duplicates([unit("A#1", "B#1"), unit("B#1")])  # a plain duplicate is fine


def item(uid, mode, shipped, held, model="m"):
    return {"model": model, "mode": mode, "unit_id": uid, "tier": "ids", "template": "t", "repeat": 0,
            "outcome": "accepted" if shipped else "needs_human", "shipped": shipped, "repair_rounds": 0,
            "total_tokens": 1, "wall_time_s": 0.1, "score": {"valid": True, "dev_correct": held, "heldout_correct": held}}


def test_distinct_view_drops_duplicate_units():
    items = [item("A#1", "gated", True, True), item("B#1", "gated", True, False),  # B duplicates A
             item("C#1", "gated", True, False), item("A#1", "ungated", True, True),
             item("B#1", "ungated", True, True), item("C#1", "ungated", True, False)]
    kept = distinct_only(items, {"B#1": "A#1"})
    assert [i["unit_id"] for i in kept] == ["A#1", "C#1", "A#1", "C#1"]


def test_report_shows_both_views_with_hand_computed_counts(tmp_path, monkeypatch):
    items = [item(u, mode, True, held) for u, held in
             (("MBBL2016-5.4.1#b", True), ("MBBL2016-4.24.7.2#b", False), ("MBBL2016-4.8.1#1", False))
             for mode in ("gated",)]
    meta = {"run_id": "dryrun-x", "date": "d", "dry_run": True, "git_commit": "c", "rulepack_hash": "h" * 12,
            "temperature": 0.0, "max_repairs": 1, "repeats": 1, "provider_classes": {}, "stopped_early": None}
    results = tmp_path / "results.json"
    results.write_text(json.dumps({"meta": meta, "items": items}), encoding="utf-8")
    [md, csv_path] = report.write_report(results, tmp_path / "out")
    text = md.read_text(encoding="utf-8")
    # all units: 3 shipped, 2 wrong (4.24.7.2#b and 4.8.1#1); distinct: 2 shipped, 1 wrong (4.8.1#1)
    assert "| m | gated | 3 |" in text and "2/3 = 67%" in text
    assert "## Distinct rules only" in text and "| m | gated | 2 |" in text and "1/2 = 50%" in text
    assert "Excluded from the distinct view: MBBL2016-4.24.7.2#b (duplicate of MBBL2016-5.4.1#b)" in text
    assert "view" in csv_path.read_text(encoding="utf-8").splitlines()[1]


def test_review_sheet_has_a_duplicate_of_column():
    rows = review.sheet_rows(list(load_units().values()), REPO_ROOT / "rules" / "rulepack" / "v0")
    by_id = {r["unit_id"]: r["duplicate_of"] for r in rows}
    assert {k: v for k, v in by_id.items() if v} == DUPLICATES
    assert "duplicate_of" in review.COLUMNS
    header = (REPO_ROOT / "docs" / "review" / "review-sheet.csv").read_bytes()
    assert header.startswith(b"\xef\xbb\xbf") and b"duplicate_of" in header.splitlines()[0]
