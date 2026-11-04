import pydantic
import pytest

from app.corpus import repository as repo
from app.corpus.extract_mbbl import extract_pages, segment
from app.corpus.models import Clause
from app.corpus.suggest import propose_tier, suggest


def make_clause(number="4.1.1", **overrides):
    data = dict(
        id=f"MBBL2016-{number}",
        source_doc="MBBL-2016",
        clause_number=number,
        text=f"{number} Every exit door shall be not less than 1.0 m wide.",
        page=2,
        section_path=["Chapter 4", "General Requirements"],
    )
    return Clause(**{**data, **overrides})


# --- models ---------------------------------------------------------------


def test_clause_defaults():
    c = make_clause()
    assert (c.tier, c.status, c.topic, c.title, c.notes) == ("unclassified", "candidate", None, None, None)


def test_invalid_tier_and_status_rejected():
    with pytest.raises(pydantic.ValidationError):
        make_clause(tier="structural")
    with pytest.raises(pydantic.ValidationError):
        make_clause(status="approved")


# --- repository -----------------------------------------------------------


@pytest.fixture
def conn(tmp_path):
    c = repo.connect(tmp_path / "corpus.db")
    repo.init_db(c)
    yield c
    c.close()


def test_upsert_is_idempotent_and_updates_in_place(conn):
    clause = make_clause()
    repo.upsert_clause(conn, clause)
    repo.upsert_clause(conn, clause)
    assert repo.count(conn) == 1
    repo.upsert_clause(conn, clause.model_copy(update={"tier": "geometric"}))
    assert repo.count(conn) == 1
    assert repo.get_clause(conn, clause.id) == clause.model_copy(update={"tier": "geometric"})


def test_get_missing_clause_returns_none(conn):
    assert repo.get_clause(conn, "MBBL2016-99.9") is None


def test_list_filters_and_counts(conn):
    repo.upsert_clause(conn, make_clause("4.1.1", tier="geometric", topic="doors", status="selected"))
    repo.upsert_clause(conn, make_clause("4.1.2", tier="ids", topic="doors", text="4.1.2 Fire doors required."))
    repo.upsert_clause(conn, make_clause("4.2.1", tier="geometric", topic="stairs", text="4.2.1 Stair width 1.5 m."))

    assert [c.clause_number for c in repo.list_clauses(conn, tier="geometric")] == ["4.1.1", "4.2.1"]
    assert [c.clause_number for c in repo.list_clauses(conn, topic="doors", tier="ids")] == ["4.1.2"]
    assert [c.clause_number for c in repo.list_clauses(conn, status="selected")] == ["4.1.1"]
    assert [c.clause_number for c in repo.list_clauses(conn, search="stair width")] == ["4.2.1"]
    assert repo.count(conn) == 3
    assert repo.count(conn, by="tier") == {"geometric": 2, "ids": 1}
    assert repo.count(conn, by="status") == {"candidate": 2, "selected": 1}
    with pytest.raises(ValueError):
        repo.count(conn, by="text; DROP TABLE clauses")


def test_yaml_export_import_round_trip(conn, tmp_path):
    selected = make_clause("4.1.1", status="selected", tier="geometric", topic="doors", notes="width check")
    repo.upsert_clause(conn, selected)
    repo.upsert_clause(conn, make_clause("4.1.2"))  # candidate: must not be exported
    yaml_path = tmp_path / "corpus" / "selected.yaml"

    assert repo.export_selected(conn, yaml_path) == 1

    fresh = repo.connect(tmp_path / "fresh.db")
    repo.init_db(fresh)
    assert repo.import_selected(fresh, yaml_path) == 1
    assert repo.list_clauses(fresh) == [selected]
    fresh.close()


# --- segmentation (synthetic PDF, never real source data) ------------------


def _write_synthetic_pdf(path, pages: list[list[str]]):
    """Minimal hand-built PDF: one Helvetica text line per entry, top to bottom."""
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for lines in pages:
        escaped = [ln.replace("(", "\\(").replace(")", "\\)") for ln in lines]
        ops = ["BT /F1 10 Tf 14 TL 50 780 Td"] + [f"({ln}) Tj T*" for ln in escaped] + ["ET"]
        stream = "\n".join(ops)
        objects.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
        content_id = len(objects)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        )
        kids.append(f"{len(objects)} 0 R")
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"

    out, offsets = "%PDF-1.4\n", []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{obj}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    path.write_bytes(out.encode("latin-1"))


SYNTHETIC_PAGES = [
    ["Contents", "4.1 Doors .............................. 2", "4.2 Stairs ............................. 3"],
    [
        "General Requirements 4",
        "4.1 Doors",
        "4.1.1 Every exit door shall be not less than 1.0 m wide.",
        "4.1.2 a) Revolving doors shall not be used as exits",
        "Model Building Bye-Law, 2016, TCPO Page 2",
    ],
    [
        "4 General Requirements",
        "and shall open outward.",
        "4.2 Stairs",
        "4.2.1 Minimum width of stair shall be 1.5 m.",
        "4.1 abutting on such space.",
        "4.2.2Requirements for handrails",
        "Page 3 Model Building Bye-Law, 2016, TCPO",
    ],
]


def test_segmentation_on_synthetic_pdf(tmp_path):
    pdf = tmp_path / "synthetic_mbbl_sample.pdf"
    _write_synthetic_pdf(pdf, SYNTHETIC_PAGES)

    clauses = segment(extract_pages(pdf))

    assert [(c.id, c.page) for c in clauses] == [
        ("MBBL2016-4.1", 2),
        ("MBBL2016-4.1.1", 2),
        ("MBBL2016-4.1.2", 2),
        ("MBBL2016-4.2", 3),
        ("MBBL2016-4.2.1", 3),
        ("MBBL2016-4.2.2", 3),
    ]
    by_number = {c.clause_number: c for c in clauses}
    assert by_number["4.1"].title == "Doors"
    assert by_number["4.1"].text == "4.1 Doors"
    assert by_number["4.1.1"].text == "4.1.1 Every exit door shall be not less than 1.0 m wide."
    assert by_number["4.1.1"].title is None
    # continues across the page break; header and footer are stripped
    assert by_number["4.1.2"].text == "4.1.2 a) Revolving doors shall not be used as exits\nand shall open outward."
    # an out-of-order number is a wrapped cross-reference, not a new clause
    assert by_number["4.2.1"].text == "4.2.1 Minimum width of stair shall be 1.5 m.\n4.1 abutting on such space."
    # no space after the number, and the reversed even-page footer is stripped
    assert by_number["4.2.2"].text == "4.2.2Requirements for handrails"
    assert all(c.source_doc == "MBBL-2016" for c in clauses)
    assert all(c.section_path == ["Chapter 4", "General Requirements"] for c in clauses)


# --- suggest heuristic ------------------------------------------------------


def test_suggest_keeps_ids_candidates_despite_unit_heavy_clauses():
    geometric = [make_clause(f"4.{i}", text="Minimum width 1.5 m, height 2.1 m, area 9 sq.m.") for i in range(1, 10)]
    ids_clause = make_clause("4.20", text="Fire door shall be provided with fire resistance rating.")
    picked = suggest(geometric + [ids_clause], limit=4)
    assert len(picked) == 4
    assert ("MBBL2016-4.20", "ids") in [(c.id, tier) for c, _, tier in picked]


def test_propose_tier():
    assert propose_tier("Minimum width of stair shall be 1.5 m.") == "geometric"
    assert propose_tier("Doors shall have a fire resistance rating of 2 hours.") == "ids"
    assert propose_tier("The Authority may grant sanction.") == "unclassified"
