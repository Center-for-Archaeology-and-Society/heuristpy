"""Metadata helpers for heuristpy."""

from __future__ import annotations

from .session import HeuristSession


def heurist_rectypes(session: HeuristSession) -> dict:
    """List Heurist record types.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.

    Returns
    -------
    dict
        Heurist record type metadata.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    resp = session._get(f"/api/{session.database}/rectypes")
    return resp.json()


def heurist_fields(session: HeuristSession) -> dict:
    """List Heurist fields.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.

    Returns
    -------
    dict
        Heurist field metadata.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    resp = session._get(f"/api/{session.database}/fields")
    return resp.json()


def heurist_structure(session: HeuristSession, entity: str = "all") -> dict:
    """Get Heurist structure definitions.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    entity:
        Structure entity name. Defaults to ``"all"``.

    Returns
    -------
    dict
        Parsed Heurist structure payload.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if not isinstance(entity, str) or not entity:
        raise ValueError("entity must be a non-empty string")

    from .records import heurist_raw_entity

    return heurist_raw_entity(session, action="structure", entity=entity)
