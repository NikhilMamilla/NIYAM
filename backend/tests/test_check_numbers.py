"""scripts/check_numbers.py: the committed text agrees with the committed results, and a wrong number is caught."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("check_numbers", ROOT / "scripts" / "check_numbers.py")
cn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cn)
FACTS = cn.facts(with_tests=False)
RATES = cn.committed_rates()


def test_committed_text_has_no_mismatch():
    bad, checked = cn.check(FACTS)
    assert bad == [] and checked > 0


def test_facts_from_committed_files():
    assert (FACTS["clauses.MBBL2016"], FACTS["clauses.TGBR2012"]) == (445, 55)
    assert (FACTS["run.pilot.calls"], FACTS["run.headline.calls"], FACTS["run.telangana.calls"]) == (143, 415, 31)
    assert (FACTS["rescore.headline.wrong"], FACTS["rescore.headline.shipped"]) == (21, 199)
    assert (FACTS["rescore.telangana.wrong"], FACTS["rescore.telangana.shipped"]) == (6, 22)
    assert (FACTS["rescore.changed"], FACTS["rescore.items"]) == (0, 240)


def test_wrong_numbers_are_caught():
    text = ("The MBBL 2016 PDF becomes 446 clauses.\n"
            "Run 2 used 416 model calls; the Telangana run 31 calls.\n"
            "wrong_shipped 2/68 = 4% [1%, 10%]\n"
            "rulepack v0: 7 rules\n")
    bad, _ = cn.check_text("x.md", text, FACTS, RATES)
    assert len(bad) == 4, bad
    ok = "Run 2 used 415 model calls; the Telangana run 31 calls. wrong_shipped 2/68 = 3% [1%, 10%]\n"
    assert cn.check_text("x.md", ok, FACTS, RATES)[0] == []
