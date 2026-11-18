from app.corpus import cli
from app.corpus.extract_tgbr import SOURCE_DOC, segment

PAGES = [
    "1\nGOVERNMENT OF ANDHRA PRADESH\nA B S T R A C T\nG.O. preamble text.",
    "2\n1. SHORT TITLE, APPLICABILITY & COMMENCEMENT:\n(a) These rules may be called the Building Rules, 2012.\n"
    "2. DEFINITIONS: In these rules,\n(a) 'Building' means any structure.",
    "3\n(b) 'Floor' means the lower surface.\n3. RESTRICTION OF BUILDING ACTIVITY IN THE VICINITY OF CERTAIN\nAREAS:\n"
    "(a) No building activity within 1. and 2. cross-references shall split this.",
    "4 (c) Stilt Floor meant for parking is excluded. Height of stilt floor shall not be less than 2.5m.\n"
    "5. A LINE THAT IS NOT THE NEXT RULE\n4. REQUIREMENT OF APPROACH ROAD FOR BUILDING SITES / PLOTS:\n(a) Text.",
    "5\nGREATER HYDERABAD MUNICIPAL CORPORATION\nANNEXURE-I\n(See Rule-4)\n1 Ward 1 Locality A",
    "6\nGADWAL\nANNEXURE-I\n(See Rule-4)\n2 Ward 2 Locality B",
    "7\nANNEXURE-II\n(See Rule-4)\nList of Areas Prohibited",
    "8\nANNEXURE \ufffd IV\n7. REQUIREMENTS INSIDE AN ANNEXURE ARE NOT RULES\nDefinitions 2. In these rules",
    "9\nAPPENDIX - I\nForm text.",
]


def by_id():
    return {c.id: c for c in segment(PAGES)}


def test_rules_are_numbered_in_order_with_pages_and_titles():
    clauses = by_id()
    assert [i for i in clauses if not i.startswith("TGBR2012-Annex") and not i.startswith("TGBR2012-Append")] == \
        ["TGBR2012-1", "TGBR2012-2", "TGBR2012-3", "TGBR2012-4"]
    rule3 = clauses["TGBR2012-3"]
    assert rule3.page == 3 and rule3.title.startswith("RESTRICTION OF BUILDING ACTIVITY")
    assert rule3.source_doc == SOURCE_DOC and rule3.clause_number == "3"
    assert "G.O. preamble" not in " ".join(c.text for c in clauses.values())  # the order before rule 1 is skipped


def test_page_numbers_do_not_leak_into_clause_text():
    rule3 = by_id()["TGBR2012-3"]
    assert "Height of stilt floor shall not be less than 2.5m." in rule3.text
    assert not any(line.strip() in {"3", "4", "5"} for line in rule3.text.splitlines())
    assert "(c) Stilt Floor" in rule3.text and "4 (c)" not in rule3.text
    assert "5. A LINE THAT IS NOT THE NEXT RULE" in rule3.text  # out of order: stays text


def test_annexures_merge_repeated_headings_and_hold_their_numbered_lines():
    clauses = by_id()
    annex1 = clauses["TGBR2012-AnnexureI"]
    assert annex1.page == 5 and "Locality A" in annex1.text and "Locality B" in annex1.text
    assert "GADWAL" in annex1.text and "6" not in annex1.text.splitlines()  # the town name above a repeated heading stays with the annexure
    assert clauses["TGBR2012-AnnexureIV"].page == 8 and "REQUIREMENTS INSIDE" in clauses["TGBR2012-AnnexureIV"].text
    assert clauses["TGBR2012-AppendixI"].section_path == ["Appendices"]
    assert "TGBR2012-7" not in clauses


def test_ingest_cli_has_a_tgbr_source(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(cli, "cmd_ingest", lambda conn, args: seen.update(vars(args)))
    cli.main(["--db", str(tmp_path / "c.sqlite"), "ingest", "--source", "tgbr"])
    assert seen["source"] == "tgbr"
