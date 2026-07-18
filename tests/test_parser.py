import pytest
from drawings_ai.parser import DrawingsParser
from drawings_ai.schemas import ConfidenceLevel

def test_parser_initialization():
    parser = DrawingsParser()
    assert parser.pymupdf_available is True or parser.pymupdf_available is False
    assert "footing" in parser.entity_rules
    assert "slab" in parser.entity_rules

def test_custom_rule_registration():
    parser = DrawingsParser()
    parser.register_rule(
        entity_type="ups_system",
        regex_pattern=r'\b(UPS)\b',
        default_material="Electrical Equipment",
        default_reliability=ConfidenceLevel.HIGH
    )
    assert "ups_system" in parser.entity_rules
    rule = parser.entity_rules["ups_system"]
    assert rule["material"] == "Electrical Equipment"
    assert rule["reliability"] == ConfidenceLevel.HIGH

def test_mock_parsing_fallback():
    parser = DrawingsParser()
    # Force mock parse
    res = parser._mock_parse()
    assert len(res.drawing_sheets) == 3
    assert len(res.entities) == 3
    assert res.entities[0].entity_type == "slab"
    assert res.entities[1].entity_type == "footing"
