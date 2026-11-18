"""The RD-CDM crosswalk must cover every RD-CDM element and point at real slots."""

import csv
from pathlib import Path

from linkml_runtime.utils.schemaview import SchemaView

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "src" / "rapid_registry_schema" / "schema" / "rapid_registry.yaml"
CROSSWALK = ROOT / "mappings" / "rd_cdm_to_rapid.sssom.tsv"

# RD-CDM v2.1.0 has 79 data elements (rd_cdm instances/data_elements.yaml).
RD_CDM_ELEMENT_COUNT = 79


def _rows():
    with CROSSWALK.open() as f:
        lines = [line for line in f if not line.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


def test_every_rd_cdm_element_is_mapped_once():
    ids = [r["subject_id"] for r in _rows()]
    assert len(ids) == RD_CDM_ELEMENT_COUNT
    assert len(set(ids)) == len(ids)


def test_every_target_is_a_slot_of_its_class():
    sv = SchemaView(str(SCHEMA))
    missing = []
    for r in _rows():
        cls, slot = r["object_id"].removeprefix("rapid:").split(".")
        if cls not in sv.all_classes() or slot not in sv.class_slots(cls):
            missing.append(r["object_id"])
    assert not missing, missing


def test_predicates_are_skos():
    assert {r["predicate_id"] for r in _rows()} <= {
        "skos:exactMatch", "skos:closeMatch", "skos:relatedMatch", "skos:broadMatch", "skos:narrowMatch"}
