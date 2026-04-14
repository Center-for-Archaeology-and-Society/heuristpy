"""Tests for schema utility functions (form body encoding, create-only guard)."""

import pytest

from heuristpy._utils import (
    _encode_form_body,
    _assert_create_only_fields,
    _entity_primary_field,
    _bool_string,
    _id_csv,
)


# ---------------------------------------------------------------------------
# Form body encoder
# ---------------------------------------------------------------------------


def test_form_body_encoder_flattens_nested_schema_fields():
    encoded = _encode_form_body(
        {
            "a": "save",
            "entity": "defRecTypes",
            "fields": {
                "rty_ID": "0",
                "rty_Name": "Example Type",
            },
            "isfull": "1",
        }
    )
    assert encoded["a"] == "save"
    assert encoded["entity"] == "defRecTypes"
    assert encoded["fields[rty_ID]"] == "0"
    assert encoded["fields[rty_Name]"] == "Example Type"
    assert encoded["isfull"] == "1"


def test_form_body_encoder_simple_flat_dict():
    encoded = _encode_form_body({"db": "mydb", "a": "login"})
    assert encoded["db"] == "mydb"
    assert encoded["a"] == "login"


def test_form_body_encoder_none_returns_empty():
    assert _encode_form_body(None) == {}


def test_form_body_encoder_scalar_requires_prefix():
    with pytest.raises((ValueError, Exception)):
        _encode_form_body("scalar_value")


def test_form_body_encoder_scalar_with_prefix():
    result = _encode_form_body("hello", prefix="key")
    assert result == {"key": "hello"}


def test_form_body_encoder_deeply_nested():
    encoded = _encode_form_body(
        {"outer": {"inner": {"deep": "value"}}}
    )
    assert encoded["outer[inner][deep]"] == "value"


def test_form_body_encoder_integer_values():
    encoded = _encode_form_body({"count": 42, "flag": True})
    assert encoded["count"] == "42"
    assert encoded["flag"] == "True"


# ---------------------------------------------------------------------------
# Create-only guard
# ---------------------------------------------------------------------------


def test_create_only_guard_forces_zero_id_when_missing():
    result = _assert_create_only_fields({"rty_Name": "Example"}, "rty_ID")
    assert result["rty_ID"] == "0"


def test_create_only_guard_forces_zero_id_when_empty_string():
    result = _assert_create_only_fields(
        {"rty_ID": "", "rty_Name": "Example"}, "rty_ID"
    )
    assert result["rty_ID"] == "0"


def test_create_only_guard_forces_zero_id_when_zero():
    result = _assert_create_only_fields(
        {"rty_ID": "0", "rty_Name": "Example"}, "rty_ID"
    )
    assert result["rty_ID"] == "0"


def test_create_only_guard_blocks_positive_ids():
    with pytest.raises(ValueError, match="refuse"):
        _assert_create_only_fields(
            {"rty_ID": "12", "rty_Name": "Example"}, "rty_ID"
        )


def test_create_only_guard_blocks_large_positive_ids():
    with pytest.raises(ValueError, match="refuse"):
        _assert_create_only_fields({"trm_ID": "9999"}, "trm_ID")


def test_create_only_guard_preserves_other_fields():
    result = _assert_create_only_fields(
        {"rty_ID": "0", "rty_Name": "Test", "rty_Status": "open"}, "rty_ID"
    )
    assert result["rty_Name"] == "Test"
    assert result["rty_Status"] == "open"


# ---------------------------------------------------------------------------
# Entity primary field mapping
# ---------------------------------------------------------------------------


def test_entity_primary_field_known_entities():
    assert _entity_primary_field("defVocabularyGroups") == "vcg_ID"
    assert _entity_primary_field("defTerms") == "trm_ID"
    assert _entity_primary_field("defRecTypes") == "rty_ID"
    assert _entity_primary_field("defDetailTypes") == "dty_ID"
    assert _entity_primary_field("defRecStructure") == "rst_ID"


def test_entity_primary_field_unknown_returns_none():
    assert _entity_primary_field("unknownEntity") is None


# ---------------------------------------------------------------------------
# Bool string helper
# ---------------------------------------------------------------------------


def test_bool_string_true():
    assert _bool_string(True) == "1"


def test_bool_string_false():
    assert _bool_string(False) == "0"


def test_bool_string_non_bool():
    assert _bool_string("1") == "1"
    assert _bool_string(42) == "42"


# ---------------------------------------------------------------------------
# ID CSV helper
# ---------------------------------------------------------------------------


def test_id_csv_scalar():
    assert _id_csv("42") == "42"
    assert _id_csv(42) == "42"


def test_id_csv_list():
    assert _id_csv([1, 2, 3]) == "1,2,3"
    assert _id_csv(["10", "20"]) == "10,20"


def test_id_csv_already_csv_string():
    assert _id_csv("1,2,3") == "1,2,3"
