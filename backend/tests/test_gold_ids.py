import pytest
from ifctester import ids
from lxml import etree

from app.fixtures.builders import PILOT_UNITS, safe_name
from app.fixtures.gold_ids import GOLD_DIR, build_all_gold, load_units

IDS_NS = "http://standards.buildingsmart.org/IDS"


@pytest.mark.parametrize("unit_id", PILOT_UNITS)
def test_gold_ids_is_schema_valid_and_traces_to_its_unit(unit_id):
    unit = load_units()[unit_id]
    path = GOLD_DIR / f"{safe_name(unit_id)}.ids"
    gold = ids.open(str(path), validate=True)
    [spec] = gold.specifications
    # ifctester 0.9.0 does not parse @identifier back, so read the trace from the XML itself
    [xml_spec] = etree.parse(str(path)).getroot().iter(f"{{{IDS_NS}}}specification")
    assert xml_spec.get("identifier") == unit_id
    assert spec.description == " ".join(unit.text.split())
    assert unit.clause_id in spec.instructions
    assert "DRAFT" in gold.info["description"]
    assert unit.expected_artifact == f"fixtures/ids/{path.name}"
    assert unit.human_reviewed is False


def test_gold_ids_regenerate_identically(tmp_path):
    build_all_gold(tmp_path)
    for unit_id in PILOT_UNITS:
        name = f"{safe_name(unit_id)}.ids"
        assert (tmp_path / name).read_bytes().splitlines() == (GOLD_DIR / name).read_bytes().splitlines()
