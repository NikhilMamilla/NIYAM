import pydantic
import pytest

from app.corpus import cli
from app.corpus import repository as repo
from app.corpus.models import Clause, RuleUnit

CLAUSE_TEXT = (
    "5.4.1 Doorways\n"
    "b. No exit doorway shall be less than 1m in width. Doorways shall be not less than 2\n"
    "m in height."
)


@pytest.fixture
def conn(tmp_path):
    c = repo.connect(tmp_path / "corpus.db")
    repo.init_db(c)
    repo.upsert_clause(
        c,
        Clause(
            id="MBBL2016-5.4.1", source_doc="MBBL-2016", clause_number="5.4.1",
            text=CLAUSE_TEXT, page=100, section_path=["Chapter 5"],
        ),
    )
    yield c
    c.close()


def unit(text="No exit doorway shall be less than 1m in width.", **overrides):
    data = dict(id="MBBL2016-5.4.1#b", clause_id="MBBL2016-5.4.1", text=text, tier="ids", status="pilot")
    return RuleUnit(**{**data, **overrides})


def test_rule_unit_defaults_and_literals():
    u = unit()
    assert (u.human_reviewed, u.reviewer, u.expected_artifact, u.notes) == (False, None, None, None)
    with pytest.raises(pydantic.ValidationError):
        unit(status="candidate")
    with pytest.raises(pydantic.ValidationError):
        unit(tier="structural")


def test_unit_text_must_be_verbatim_substring_of_clause(conn):
    with pytest.raises(ValueError, match="verbatim"):
        repo.upsert_unit(conn, unit(text="No exit doorway shall be narrower than 1m."))
    assert repo.list_units(conn) == []


def test_verbatim_check_ignores_pdf_line_breaks_only(conn):
    repo.upsert_unit(conn, unit(id="MBBL2016-5.4.1#b2", text="Doorways shall be not less than 2 m in height."))
    with pytest.raises(ValueError, match="verbatim"):
        repo.upsert_unit(conn, unit(id="MBBL2016-5.4.1#b3", text="doorways shall be not less than 2 m in height."))


def test_unit_requires_existing_parent_clause(conn):
    with pytest.raises(ValueError, match="no clause"):
        repo.upsert_unit(conn, unit(clause_id="MBBL2016-9.9.9"))


def test_upsert_unit_is_idempotent_and_get_list(conn):
    repo.upsert_unit(conn, unit())
    repo.upsert_unit(conn, unit())
    repo.upsert_unit(conn, unit(notes="reviewed later"))
    assert repo.list_units(conn) == [unit(notes="reviewed later")]
    assert repo.get_unit(conn, "MBBL2016-5.4.1#b") == unit(notes="reviewed later")
    assert repo.get_unit(conn, "nope") is None
    assert repo.list_units(conn, status="selected") == []


def test_units_yaml_round_trip(conn, tmp_path):
    original = unit(expected_artifact="fixtures/ids/x.ids", reviewer=None, notes="draft")
    repo.upsert_unit(conn, original)
    path = tmp_path / "rule-units.yaml"
    assert repo.export_units(conn, path) == 1
    repo.init_db(conn)
    conn.execute("DELETE FROM rule_units")
    assert repo.import_units(conn, path) == 1
    assert repo.list_units(conn) == [original]


def test_cli_unit_add_rejects_non_verbatim_text(conn, tmp_path, capsys):
    db = tmp_path / "corpus.db"
    args = ["--db", str(db), "unit-add", "MBBL2016-5.4.1", "--suffix", "b", "--tier", "ids"]
    with pytest.raises(SystemExit):
        cli.main(args + ["--text", "No exit door may be under 1m."])
    cli.main(args + ["--text", "No exit doorway shall be less than 1m in width."])
    cli.main(["--db", str(db), "unit-show", "MBBL2016-5.4.1#b"])
    out = capsys.readouterr().out
    assert "MBBL2016-5.4.1#b" in out and "status: pilot" in out
