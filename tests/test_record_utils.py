"""Tests for record utility functions (normalisation, merging, WKT extraction)."""

import pytest

from heuristpy._utils import (
    _normalize_existing_details,
    _merge_details,
    _normalize_record,
    _extract_wkt,
    _payload_has_spatial,
    _next_detail_index,
    _normalize_new_detail_entries,
    _normalize_detail_entries,
)


# ---------------------------------------------------------------------------
# Detail normalisation
# ---------------------------------------------------------------------------


def test_existing_details_normalize_safely():
    details = {
        "1": {"3": "42SA920"},
        "238": {
            "834266": {
                "id": "53501",
                "type": "12",
                "title": "Montezuma Canyon",
            }
        },
    }
    normalized = _normalize_existing_details(details)
    assert normalized["1"]["3"] == "42SA920"
    assert normalized["238"]["834266"] == "53501"


def test_geospatial_details_normalize_to_wkt():
    details = {
        "28": {
            "1576558": {
                "geo": {
                    "type": "p",
                    "wkt": "POINT(-107.9618 36.06054)",
                }
            }
        }
    }
    normalized = _normalize_existing_details(details)
    assert normalized["28"]["1576558"] == "POINT(-107.9618 36.06054)"


def test_normalize_detail_entries_scalar():
    entries = {"0": "hello", "1": "world"}
    result = _normalize_detail_entries(entries, "1")
    assert result["0"] == "hello"
    assert result["1"] == "world"


def test_normalize_detail_entries_empty():
    assert _normalize_detail_entries({}, "1") == {}
    assert _normalize_detail_entries(None, "1") == {}


def test_normalize_detail_entries_unsupported_shape_raises():
    entries = {"0": {"nested": "dict", "no_id": True}}
    with pytest.raises(ValueError, match="Unsupported"):
        _normalize_detail_entries(entries, "99")


# ---------------------------------------------------------------------------
# Detail merging
# ---------------------------------------------------------------------------


def test_detail_merge_replaces():
    existing = {
        "1": {"3": "42SA920"},
        "238": {"834266": "53501"},
    }
    replaced = _merge_details(
        existing,
        {"238": {"0": "777"}},
        mode="replace",
    )
    assert replaced["238"]["0"] == "777"
    assert "834266" not in replaced["238"]


def test_detail_merge_appends():
    existing = {
        "1": {"3": "42SA920"},
        "238": {"834266": "53501"},
    }
    appended = _merge_details(
        existing,
        {"238": {"0": "777"}},
        mode="append",
    )
    assert appended["238"]["834266"] == "53501"
    assert appended["238"]["834267"] == "777"


def test_detail_merge_invalid_mode():
    with pytest.raises(ValueError):
        _merge_details({}, {}, mode="invalid")


def test_detail_merge_preserves_unrelated_fields():
    existing = {"1": {"3": "42SA920"}, "238": {"834266": "53501"}}
    merged = _merge_details(existing, {"238": {"0": "999"}}, mode="replace")
    assert merged["1"]["3"] == "42SA920"


def test_detail_merge_adds_new_field():
    existing = {"1": {"3": "old"}}
    merged = _merge_details(existing, {"999": {"0": "new"}}, mode="replace")
    assert merged["999"]["0"] == "new"


# ---------------------------------------------------------------------------
# Next detail index
# ---------------------------------------------------------------------------


def test_next_detail_index_empty():
    assert _next_detail_index({}) == 0


def test_next_detail_index_with_numeric_keys():
    assert _next_detail_index({"3": "x", "7": "y"}) == 8


def test_next_detail_index_with_large_key():
    assert _next_detail_index({"834266": "x"}) == 834267


# ---------------------------------------------------------------------------
# New detail entry normalisation
# ---------------------------------------------------------------------------


def test_normalize_new_detail_entries_scalar():
    result = _normalize_new_detail_entries({"0": "hello"})
    assert result["0"] == "hello"


def test_normalize_new_detail_entries_pointer():
    result = _normalize_new_detail_entries({"0": {"id": "42"}})
    assert result["0"] == "42"


def test_normalize_new_detail_entries_non_dict():
    result = _normalize_new_detail_entries("hello")
    assert result["0"] == "hello"


def test_normalize_new_detail_entries_none():
    assert _normalize_new_detail_entries(None) == {}


def test_normalize_new_detail_entries_unsupported_raises():
    with pytest.raises(ValueError):
        _normalize_new_detail_entries({"0": {"nested": "no_id"}})


# ---------------------------------------------------------------------------
# Record normalisation
# ---------------------------------------------------------------------------


def test_record_normalization_keeps_header_and_details():
    record = {
        "rec_ID": "3",
        "rec_RecTypeID": "91",
        "rec_OwnerUGrpID": "0",
        "rec_NonOwnerVisibility": "viewable",
        "rec_URL": None,
        "rec_ScratchPad": "",
        "details": {"1": {"3": "42SA920"}},
    }
    normalized = _normalize_record(record)
    assert normalized["record_id"] == "3"
    assert normalized["rectype_id"] == "91"
    assert normalized["details"]["1"]["3"] == "42SA920"


def test_record_normalization_nullable_url():
    record = {
        "rec_ID": "1",
        "rec_RecTypeID": "10",
        "rec_OwnerUGrpID": "0",
        "rec_NonOwnerVisibility": "viewable",
        "rec_URL": None,
        "rec_ScratchPad": None,
        "details": {},
    }
    normalized = _normalize_record(record)
    assert normalized["url"] is None
    assert normalized["scratch_pad"] is None


# ---------------------------------------------------------------------------
# WKT extraction
# ---------------------------------------------------------------------------


def test_wkt_extracted_from_geo_detail():
    record = {
        "rec_ID": "1",
        "details": {
            "1096": {
                "0": {
                    "geo": {
                        "type": "p",
                        "wkt": "POINT(-110.1 35.2)",
                    }
                }
            }
        },
    }
    assert _extract_wkt(record) == "POINT(-110.1 35.2)"


def test_wkt_extracted_from_lon_lat_fields():
    record = {
        "rec_ID": "2",
        "details": {
            "1094": {"0": "-110.1"},
            "1095": {"0": "35.2"},
        },
    }
    wkt = _extract_wkt(record)
    assert wkt == "POINT(-110.1 35.2)"


def test_wkt_returns_none_when_absent():
    record = {"rec_ID": "3", "details": {"1": {"0": "text value"}}}
    assert _extract_wkt(record) is None


# ---------------------------------------------------------------------------
# Payload spatial detection
# ---------------------------------------------------------------------------


def test_payload_spatial_detection_true():
    payload = {
        "records": [
            {
                "rec_ID": "1",
                "details": {
                    "1096": {
                        "0": {
                            "geo": {
                                "type": "p",
                                "wkt": "POINT(-110.1 35.2)",
                            }
                        }
                    }
                },
            }
        ]
    }
    assert _payload_has_spatial(payload) is True


def test_payload_spatial_detection_false():
    payload = {
        "records": [
            {"rec_ID": "2", "details": {"1": {"0": "test value"}}}
        ]
    }
    assert _payload_has_spatial(payload) is False


def test_payload_spatial_detection_empty():
    assert _payload_has_spatial({"records": []}) is False
