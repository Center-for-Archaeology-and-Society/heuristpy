"""Internal utilities for heuristpy."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


class HeuristChange:
    """Represents a change made to a Heurist record.

    Returned by write helpers such as :func:`heurist_create_record`,
    :func:`heurist_patch_record`, and :func:`heurist_replace_record`. Contains
    enough information to support rollback with :func:`heurist_rollback`.
    """

    def __init__(
        self,
        session: Any,
        action: str,
        record_id: str,
        before: Any,
        after: Any,
        response: Any,
    ) -> None:
        self.session = session
        self.action = action
        self.record_id = str(record_id) if record_id is not None else ""
        self.before = before
        self.after = after
        self.response = response

    def __repr__(self) -> str:
        return (
            f"HeuristChange(action={self.action!r}, record_id={self.record_id!r})"
        )


def _make_change(
    session: Any,
    action: str,
    record_id: Any,
    before: Any,
    after: Any,
    response: Any,
) -> HeuristChange:
    """Create a :class:`HeuristChange` object."""
    return HeuristChange(
        session=session,
        action=action,
        record_id=str(record_id) if record_id is not None else "",
        before=before,
        after=after,
        response=response,
    )


def _encode_form_body(data: Any, prefix: Optional[str] = None) -> Dict[str, str]:
    """Flatten a nested dict to form fields with bracket notation.

    Mirrors the R helper ``.heurist_encode_form_body``. Scalar values become
    plain string entries; nested dicts are flattened with ``key[subkey]``
    notation recursively.
    """
    if data is None:
        return {}

    if not isinstance(data, dict):
        if not prefix:
            raise ValueError("prefix required for scalar values")
        return {prefix: str(data)}

    out: Dict[str, str] = {}
    for key, value in data.items():
        next_prefix = str(key) if prefix is None else f"{prefix}[{key}]"
        encoded = _encode_form_body(value, prefix=next_prefix)
        out.update(encoded)

    return out


def _check_response(resp: Any) -> Any:
    """Raise for HTTP 4xx/5xx responses and return the response otherwise."""
    if resp.status_code >= 400:
        try:
            body = resp.text[:500]
        except Exception:
            body = ""
        raise IOError(
            f"Heurist request failed. HTTP {resp.status_code}: {body}"
        )
    return resp


def _get_message(payload: Any) -> str:
    """Extract an error message from a Heurist response payload."""
    if not isinstance(payload, dict):
        return "Unknown Heurist error."
    return (
        payload.get("message")
        or payload.get("msg")
        or "Unknown Heurist error."
    )


def _assert_ok(payload: Any, message: str = "Heurist request failed.") -> None:
    """Assert that the payload has status ``'ok'``."""
    _assert_status(payload, ["ok"], message)


def _assert_status(payload: Any, statuses: list, message: str) -> None:
    """Assert that the payload has one of the given statuses."""
    status = payload.get("status", "") if isinstance(payload, dict) else ""
    if status not in statuses:
        err_msg = _get_message(payload)
        raise ValueError(f"{message}: {err_msg}")


def _require_record(payload: Any, record_id: Any) -> Any:
    """Get the first record from a payload, raising if empty."""
    records = payload.get("records", []) if isinstance(payload, dict) else []
    if isinstance(records, dict):
        records = list(records.values())
    if not records:
        raise ValueError(f"No record found for record ID {record_id}")
    return records[0]


def _nullable_scalar(value: Any) -> Optional[str]:
    """Return a string scalar or ``None``."""
    if value is None:
        return None
    if isinstance(value, (list, dict)) and len(value) == 0:
        return None
    return str(value)


def _normalize_record(record: dict) -> dict:
    """Normalize a Heurist record to a stable dict."""
    details = _normalize_existing_details(record.get("details") or {})
    return {
        "record_id": str(record.get("rec_ID", "")),
        "rectype_id": str(record.get("rec_RecTypeID", "")),
        "owner_ugrp_id": str(record.get("rec_OwnerUGrpID", "")),
        "non_owner_visibility": str(record.get("rec_NonOwnerVisibility", "")),
        "url": _nullable_scalar(record.get("rec_URL")),
        "scratch_pad": _nullable_scalar(record.get("rec_ScratchPad")),
        "details": details,
    }


def _normalize_existing_details(details: dict) -> dict:
    """Normalize existing record details to a stable structure."""
    if not details:
        return {}
    normalized: dict = {}
    for dty_id, entries in details.items():
        normalized[str(dty_id)] = _normalize_detail_entries(entries, dty_id)
    return normalized


def _normalize_detail_entries(entries: Any, dty_id: Any) -> dict:
    """Normalize detail entries for a single field."""
    if entries is None or not entries:
        return {}

    if not isinstance(entries, dict):
        raise ValueError(
            f"Unsupported Heurist detail payload for field {dty_id}"
        )

    normalized: dict = {}
    for entry_name, value in entries.items():
        if isinstance(value, dict) and "id" in value:
            normalized[str(entry_name)] = str(value["id"])
        elif (
            isinstance(value, dict)
            and "geo" in value
            and isinstance(value["geo"], dict)
            and "wkt" in value["geo"]
        ):
            normalized[str(entry_name)] = str(value["geo"]["wkt"])
        elif not isinstance(value, dict):
            normalized[str(entry_name)] = str(value)
        elif isinstance(value, dict) and len(value) == 0:
            normalized[str(entry_name)] = None
        else:
            raise ValueError(
                f"Unsupported Heurist detail shape during safe update. "
                f"Field {dty_id} contains a value shape heuristpy does not "
                f"yet know how to preserve safely."
            )
    return normalized


def _normalize_new_detail_entries(entries: Any) -> dict:
    """Normalize new detail entries to a stable structure."""
    if entries is None:
        return {}

    if not isinstance(entries, dict):
        return {"0": str(entries)}

    if not entries:
        return {}

    normalized: dict = {}
    for entry_name, value in entries.items():
        if value is None:
            continue
        if isinstance(value, dict) and "id" in value:
            normalized[str(entry_name)] = str(value["id"])
        elif not isinstance(value, dict):
            normalized[str(entry_name)] = str(value)
        else:
            raise ValueError(
                "New detail entries must be scalar values or pointer objects "
                "with an 'id' key."
            )
    return normalized


def _next_detail_index(entries: dict) -> int:
    """Get the next available integer index in detail entries."""
    if not entries:
        return 0

    indices = []
    for k in entries:
        try:
            indices.append(int(k))
        except (ValueError, TypeError):
            pass

    if not indices:
        return 0
    return max(indices) + 1


def _merge_details(existing: dict, changes: dict, mode: str = "replace") -> dict:
    """Merge change details into existing details.

    Parameters
    ----------
    existing:
        The current normalised details dict.
    changes:
        Dict of field ID to new entries.
    mode:
        ``'replace'`` overwrites the existing entries for each changed field;
        ``'append'`` adds new entries after the existing ones.
    """
    if mode not in ("replace", "append"):
        raise ValueError("mode must be 'replace' or 'append'")

    merged = dict(existing)

    for dty_id, new_entries_raw in changes.items():
        new_entries = _normalize_new_detail_entries(new_entries_raw)
        dty_id_str = str(dty_id)

        if mode == "replace":
            merged[dty_id_str] = new_entries
        else:
            current = dict(merged.get(dty_id_str, {}))
            next_idx = _next_detail_index(current)
            for value in new_entries.values():
                current[str(next_idx)] = value
                next_idx += 1
            merged[dty_id_str] = current

    return merged


def _encode_details(details: dict) -> str:
    """JSON-encode a details dict for Heurist's form payload."""
    return json.dumps(details)


def _extract_wkt(record: dict) -> Optional[str]:
    """Extract a WKT string from a Heurist record, if present."""
    details = record.get("details") or {}
    for field_entries in details.values():
        if not isinstance(field_entries, dict):
            continue
        for entry in field_entries.values():
            if (
                isinstance(entry, dict)
                and isinstance(entry.get("geo"), dict)
                and entry["geo"].get("wkt")
            ):
                return str(entry["geo"]["wkt"])

    lon = _extract_scalar_detail(record, "1094")
    lat = _extract_scalar_detail(record, "1095")
    if lon is not None and lat is not None:
        try:
            float(lon)
            float(lat)
            return f"POINT({lon} {lat})"
        except ValueError:
            pass

    return None


def _extract_scalar_detail(record: dict, detail_type_id: str) -> Optional[str]:
    """Extract a scalar detail value from a record."""
    entries = (record.get("details") or {}).get(str(detail_type_id))
    if not entries:
        return None
    values = list(entries.values()) if isinstance(entries, dict) else list(entries)
    if values:
        v = values[0]
        if not isinstance(v, dict):
            return str(v)
    return None


def _record_has_spatial(record: dict) -> bool:
    """Check if a record has spatial data."""
    return _extract_wkt(record) is not None


def _payload_has_spatial(payload: dict) -> bool:
    """Check if any record in a payload has spatial data."""
    records = payload.get("records") or []
    if isinstance(records, dict):
        records = list(records.values())
    return any(_record_has_spatial(r) for r in records)


def _bool_string(value: Any) -> str:
    """Convert a bool to ``'1'``/``'0'`` string."""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def _id_csv(value: Any) -> str:
    """Convert a value or list of values to a comma-separated ID string."""
    if isinstance(value, str) and "," in value:
        return value
    if isinstance(value, (list, tuple)):
        return ",".join(str(v) for v in value)
    return str(value)


def _entity_primary_field(entity: str) -> Optional[str]:
    """Return the primary field name for a Heurist entity type."""
    mapping = {
        "defVocabularyGroups": "vcg_ID",
        "defTerms": "trm_ID",
        "defRecTypes": "rty_ID",
        "defDetailTypes": "dty_ID",
        "defRecStructure": "rst_ID",
    }
    return mapping.get(entity)


def _assert_create_only_fields(fields: dict, primary_field: str) -> dict:
    """Guard that the primary field ID is zero (create-only guard).

    Raises :class:`ValueError` if an existing positive ID is supplied, which
    would indicate an attempt to update an existing definition rather than
    create a new one.
    """
    out = dict(fields)
    current_id = out.get(primary_field, "")

    if current_id is None or str(current_id).strip() == "":
        out[primary_field] = "0"
        return out

    try:
        current_id_num = float(str(current_id))
    except ValueError:
        current_id_num = None

    if current_id_num is not None and current_id_num > 0:
        raise ValueError(
            f"Create-only schema helpers refuse to update an existing "
            f"definition. {primary_field} = {current_id}. "
            "Use the raw entity edit helper only when you intend an explicit "
            "low-level schema update."
        )

    out[primary_field] = "0"
    return out
