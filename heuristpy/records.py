"""Record read/write helpers for heuristpy."""

from __future__ import annotations

from typing import Any, Optional

from .session import HeuristSession
from ._utils import (
    HeuristChange,
    _assert_ok,
    _assert_status,
    _encode_details,
    _make_change,
    _merge_details,
    _normalize_record,
    _require_record,
)


def heurist_get_record(session: HeuristSession, record_id: Any) -> dict:
    """Fetch one record by record ID.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    record_id:
        Numeric or string record ID.

    Returns
    -------
    dict
        Parsed Heurist record payload.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    return heurist_raw_record_output(
        session,
        query={
            "recID": str(record_id),
            "format": "json",
            "restapi": 1,
        },
    )


def heurist_find_records(
    session: HeuristSession,
    q: str,
    format: str = "json",
) -> dict:
    """Find records using a Heurist query string.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    q:
        Heurist query string, such as ``"t:Site sortby:-m"``.
    format:
        Response format. Defaults to ``"json"``.

    Returns
    -------
    dict
        Parsed Heurist record payload.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if not isinstance(q, str) or not q:
        raise ValueError("q must be a non-empty string")
    return heurist_raw_record_output(
        session,
        query={
            "q": q,
            "format": format,
            "restapi": 1,
        },
    )


def heurist_raw_record_output(
    session: HeuristSession, query: Optional[dict] = None
) -> dict:
    """Low-level wrapper around ``record_output.php``.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    query:
        Query parameters passed to the endpoint.

    Returns
    -------
    dict
        Parsed JSON response.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    params: dict = {"db": session.database}
    if query:
        params.update(query)
    resp = session._get("/hserv/controller/record_output.php", params=params)
    return resp.json()


def heurist_raw_record_edit(
    session: HeuristSession, body: Optional[dict] = None
) -> dict:
    """Low-level wrapper around ``record_edit.php``.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    body:
        Form body sent to the endpoint.

    Returns
    -------
    dict
        Parsed JSON response.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    payload: dict = {"db": session.database}
    if body:
        payload.update(body)
    resp = session._post("/hserv/controller/record_edit.php", data=payload)
    return resp.json()


def heurist_raw_entity(
    session: HeuristSession,
    action: str,
    entity: str,
    query: Optional[dict] = None,
) -> dict:
    """Low-level wrapper around ``entityScrud.php`` (read).

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    action:
        Entity action.
    entity:
        Entity name.
    query:
        Additional query parameters.

    Returns
    -------
    dict
        Parsed JSON response.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if not isinstance(action, str) or not action:
        raise ValueError("action must be a non-empty string")
    if not isinstance(entity, str) or not entity:
        raise ValueError("entity must be a non-empty string")

    params: dict = {
        "db": session.database,
        "a": action,
        "entity": entity,
    }
    if query:
        params.update(query)

    resp = session._get("/hserv/controller/entityScrud.php", params=params)
    return resp.json()


def heurist_create_record(
    session: HeuristSession,
    rectype_id: Any,
    details: dict,
    title: Optional[str] = None,
    owner_ugrp_id: Any = None,
    non_owner_visibility: Optional[str] = None,
) -> HeuristChange:
    """Create a new Heurist record.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    rectype_id:
        Record type ID.
    details:
        Named dict of Heurist detail values.
    title:
        Optional title override.
    owner_ugrp_id:
        Optional owner group ID.
    non_owner_visibility:
        Optional non-owner visibility.

    Returns
    -------
    HeuristChange
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")

    body: dict = {
        "a": "save",
        "ID": "0",
        "RecTypeID": str(rectype_id),
        "details": _encode_details(details),
        "details_encoded": "3",
    }
    if title is not None:
        body["Title"] = title
    if owner_ugrp_id is not None:
        body["OwnerUGrpID"] = str(owner_ugrp_id)
    if non_owner_visibility is not None:
        body["NonOwnerVisibility"] = non_owner_visibility

    response = heurist_raw_record_edit(session, body=body)
    _assert_ok(response, "Heurist create failed.")

    after_id = str(response.get("data") or "")
    after = heurist_get_record(session, after_id) if after_id else None

    return _make_change(
        session=session,
        action="create",
        record_id=after_id,
        before=None,
        after=after,
        response=response,
    )


def heurist_replace_record(
    session: HeuristSession,
    record_id: Any,
    rectype_id: Any,
    details: dict,
    owner_ugrp_id: Any,
    non_owner_visibility: Any,
    url: Optional[str] = None,
    scratch_pad: Optional[str] = None,
    title: Optional[str] = None,
) -> HeuristChange:
    """Replace a Heurist record with a full payload.

    This is a low-level full-save helper and should be used carefully.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    record_id:
        Record ID.
    rectype_id:
        Record type ID.
    details:
        Full Heurist details dict to save.
    owner_ugrp_id:
        Owner group ID.
    non_owner_visibility:
        Non-owner visibility value.
    url:
        Optional URL value.
    scratch_pad:
        Optional scratch pad value.
    title:
        Optional title override.

    Returns
    -------
    HeuristChange
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")

    before = heurist_get_record(session, record_id)

    body: dict = {
        "a": "save",
        "ID": str(record_id),
        "RecTypeID": str(rectype_id),
        "OwnerUGrpID": str(owner_ugrp_id),
        "NonOwnerVisibility": str(non_owner_visibility),
        "details": _encode_details(details),
        "details_encoded": "3",
    }
    if url is not None:
        body["URL"] = url
    if scratch_pad is not None:
        body["ScratchPad"] = scratch_pad
    if title is not None:
        body["Title"] = title

    response = heurist_raw_record_edit(session, body=body)
    _assert_ok(response, "Heurist replace failed.")
    after = heurist_get_record(session, record_id)

    return _make_change(
        session=session,
        action="replace",
        record_id=str(record_id),
        before=before,
        after=after,
        response=response,
    )


def heurist_patch_record(
    session: HeuristSession,
    record_id: Any,
    details: dict,
    mode: str = "replace",
) -> HeuristChange:
    """Patch a Heurist record safely using read-modify-write.

    Existing details are fetched, normalised, merged with the supplied changes,
    and then written back as a full record payload to avoid accidental data loss.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    record_id:
        Record ID.
    details:
        Named dict of detail changes.
    mode:
        Merge mode: ``"replace"`` or ``"append"``.

    Returns
    -------
    HeuristChange
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if mode not in ("replace", "append"):
        raise ValueError("mode must be 'replace' or 'append'")

    current = _require_record(heurist_get_record(session, record_id), record_id)
    normalized = _normalize_record(current)
    merged_details = _merge_details(normalized["details"], details, mode=mode)

    return heurist_replace_record(
        session=session,
        record_id=record_id,
        rectype_id=normalized["rectype_id"],
        details=merged_details,
        owner_ugrp_id=normalized["owner_ugrp_id"],
        non_owner_visibility=normalized["non_owner_visibility"],
        url=normalized.get("url"),
        scratch_pad=normalized.get("scratch_pad"),
    )


def heurist_link_record(
    session: HeuristSession,
    source_record_id: Any,
    detail_type_id: Any,
    target_record_id: Any,
    append: bool = False,
) -> HeuristChange:
    """Safely add or replace a pointer field value on an existing record.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    source_record_id:
        Source record ID.
    detail_type_id:
        Pointer field detail type ID.
    target_record_id:
        Target record ID.
    append:
        If ``True``, append a new value. If ``False``, replace the field.

    Returns
    -------
    HeuristChange
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")

    change_details = {
        str(detail_type_id): {"0": str(target_record_id)}
    }

    return heurist_patch_record(
        session=session,
        record_id=source_record_id,
        details=change_details,
        mode="append" if append else "replace",
    )


def heurist_restore_change(change: HeuristChange) -> HeuristChange:
    """Restore the previous state captured by a :class:`HeuristChange`.

    Parameters
    ----------
    change:
        A :class:`HeuristChange` object.

    Returns
    -------
    HeuristChange
    """
    if not isinstance(change, HeuristChange):
        raise TypeError("change must be a HeuristChange")

    if change.action == "create":
        response = heurist_raw_record_edit(
            change.session,
            body={"a": "delete", "ids": str(change.record_id)},
        )
        _assert_status(
            response, ["ok", "deleted"], "Heurist rollback delete failed."
        )
        return _make_change(
            session=change.session,
            action="rollback_delete",
            record_id=change.record_id,
            before=change.after,
            after=None,
            response=response,
        )

    before_record = _require_record(change.before, change.record_id)
    normalized = _normalize_record(before_record)

    return heurist_replace_record(
        session=change.session,
        record_id=change.record_id,
        rectype_id=normalized["rectype_id"],
        details=normalized["details"],
        owner_ugrp_id=normalized["owner_ugrp_id"],
        non_owner_visibility=normalized["non_owner_visibility"],
        url=normalized.get("url"),
        scratch_pad=normalized.get("scratch_pad"),
    )


def heurist_rollback(change: HeuristChange) -> HeuristChange:
    """Roll back a :class:`HeuristChange`.

    Alias for :func:`heurist_restore_change`.

    Parameters
    ----------
    change:
        A :class:`HeuristChange` object.

    Returns
    -------
    HeuristChange
    """
    return heurist_restore_change(change)


def heurist_rollback_change(change: HeuristChange) -> HeuristChange:
    """Roll back a :class:`HeuristChange`.

    Alias for :func:`heurist_restore_change`.

    Parameters
    ----------
    change:
        A :class:`HeuristChange` object.

    Returns
    -------
    HeuristChange
    """
    return heurist_restore_change(change)
