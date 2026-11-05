import pytest
import yaml

from app.corpus import repository as repo
from app.corpus.models import Clause
from app.specgen.models import SpecError, load_spec

CLAUSE = Clause(id="MBBL2016-4.8.1", source_doc="MBBL-2016", clause_number="4.8.1", title="Height",
                text="4.8.1 Height\nThe height of a store room shall be not less\nthan 2.2 m.", page=72)
GOOD = {
    "unit_id": "MBBL2016-4.8.1#1", "clause_id": "MBBL2016-4.8.1",
    "unit_text": "The height of a store room shall be not less than 2.2 m.", "topic": "room height",
    "template": "space_height_min", "params": {"categories": ["Store"]},
    "threshold": {"value": 2.2, "text": "2.2", "unit": "m", "inclusive": True},
    "notes_for_reviewer": "Store rooms at least 2.2 m high.",
}


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "corpus.db"
    conn = repo.connect(path)
    repo.init_db(conn)
    repo.upsert_clause(conn, CLAUSE)
    conn.close()
    return path


def write(tmp_path, data, name="MBBL2016-4_8_1_1.yaml"):
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_a_good_spec_loads(tmp_path, db):
    spec = load_spec(write(tmp_path, GOOD), db)
    assert (spec.tier, spec.safe, spec.threshold.inclusive) == ("geometric", "MBBL2016-4_8_1_1", True)


def test_unit_text_must_be_verbatim_up_to_whitespace(tmp_path, db):
    with pytest.raises(SpecError, match="not a verbatim substring"):
        load_spec(write(tmp_path, {**GOOD, "unit_text": "Store rooms shall be at least 2.2 m high."}), db)


def test_threshold_number_must_occur_in_the_text(tmp_path, db):
    data = {**GOOD, "threshold": {"value": 2.4, "text": "2.4", "unit": "m", "inclusive": True}}
    with pytest.raises(SpecError, match="does not occur"):
        load_spec(write(tmp_path, data), db)
    data = {**GOOD, "threshold": {"value": 2.2, "text": "2.20", "unit": "m", "inclusive": True}}
    with pytest.raises(SpecError, match="does not occur"):  # "2.20" is not written in the clause
        load_spec(write(tmp_path, data), db)
    data = {**GOOD, "threshold": {"value": 2.0, "text": "2.2", "unit": "m", "inclusive": True}}
    with pytest.raises(SpecError, match="must be the number"):
        load_spec(write(tmp_path, data), db)


@pytest.mark.parametrize("change, message", [
    ({"surprise": 1}, "Extra inputs"),
    ({"threshold": {"value": 2.2, "text": "2.2", "unit": "cm", "inclusive": True}}, "unit"),
    ({"threshold": {"value": 2.2, "text": "2.2", "unit": "m2", "inclusive": True}}, "must be m"),
    ({"threshold": {"value": 2.2, "text": "2.2", "unit": "m"}}, "inclusive"),
    ({"template": "stair_width_min"}, "template"),
    ({"params": {"categories": []}}, "needs categories"),
    ({"unit_id": "MBBL2016-4.9.1#1"}, "must be MBBL2016-4.8.1#"),
    ({"template": "door_width_min", "params": {"selector": {"pset": "Pset_DoorCommon", "property": "IsExternal",
                                                            "value": True}}}, "selector from the modelling profile"),
])
def test_bad_specs_are_rejected(tmp_path, db, change, message):
    with pytest.raises(SpecError, match=message):
        load_spec(write(tmp_path, {**GOOD, **change}), db)


def test_door_operation_values_are_checked_against_the_ifc_enum(tmp_path, db):
    data = {**GOOD, "template": "door_operation_forbidden", "threshold": None,
            "params": {"selector": {"pset": "Pset_DoorCommon", "property": "FireExit", "value": True},
                       "forbidden_operations": ["SLIDING_SIDEWAYS"]}}
    with pytest.raises(SpecError, match="IfcDoorTypeOperationEnum"):
        load_spec(write(tmp_path, data), db)


def test_file_name_must_match_the_unit(tmp_path, db):
    with pytest.raises(SpecError, match="file name must be"):
        load_spec(write(tmp_path, GOOD, name="store.yaml"), db)
