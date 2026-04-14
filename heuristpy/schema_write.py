"""Schema write helpers for heuristpy."""

from __future__ import annotations

from typing import Any, Optional

from .session import HeuristSession
from ._utils import (
    _assert_ok,
    _assert_create_only_fields,
    _bool_string,
    _entity_primary_field,
    _id_csv,
)
from .records import heurist_raw_entity


def heurist_raw_entity_edit(
    session: HeuristSession,
    action: str,
    entity: str,
    body: Optional[dict] = None,
) -> dict:
    """Low-level wrapper around ``entityScrud.php`` (write).

    This helper is intentionally explicit because schema edits in Heurist can
    be destructive if underspecified.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    action:
        Entity action such as ``"save"``, ``"delete"``, or ``"batch"``.
    entity:
        Entity name such as ``"defRecTypes"`` or ``"defTerms"``.
    body:
        Additional form body parameters.

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

    payload: dict = {
        "db": session.database,
        "a": action,
        "entity": entity,
    }
    if body:
        payload.update(body)

    resp = session._post("/hserv/controller/entityScrud.php", data=payload)
    return resp.json()


def heurist_create_vocabulary_group(
    session: HeuristSession,
    name: str,
    description: Optional[str] = None,
    domain: str = "enum",
    order: Any = None,
) -> dict:
    """Create a new Heurist vocabulary group.

    Safely creates a new ``defVocabularyGroups`` entry. This helper only
    permits creation of new rows and will refuse positive existing IDs.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    name:
        Vocabulary group name.
    description:
        Optional description.
    domain:
        Either ``"enum"`` or ``"relation"``.
    order:
        Optional display order.

    Returns
    -------
    dict
        Parsed JSON response from Heurist.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if not isinstance(name, str) or not name:
        raise ValueError("name must be a non-empty string")
    if domain not in ("enum", "relation"):
        raise ValueError("domain must be 'enum' or 'relation'")

    fields: dict = {
        "vcg_ID": "0",
        "vcg_Name": name,
        "vcg_Domain": domain,
    }
    if description is not None:
        fields["vcg_Description"] = description
    if order is not None:
        fields["vcg_Order"] = str(order)

    return heurist_save_entity_create_only(
        session=session,
        entity="defVocabularyGroups",
        fields=fields,
    )


def heurist_create_vocabulary(
    session: HeuristSession,
    label: str,
    domain: str = "enum",
    vocabulary_group_id: Any = None,
    description: Optional[str] = None,
    code: Optional[str] = None,
    semantic_reference_url: Optional[str] = None,
    status: str = "open",
) -> dict:
    """Create a new top-level Heurist vocabulary.

    Safely creates a new top-level vocabulary as a root ``defTerms`` record.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    label:
        Vocabulary label.
    domain:
        Either ``"enum"`` or ``"relation"``.
    vocabulary_group_id:
        Optional vocabulary group ID.
    description:
        Optional description.
    code:
        Optional code.
    semantic_reference_url:
        Optional semantic URI.
    status:
        Optional status. Defaults to ``"open"``.

    Returns
    -------
    dict
        Parsed JSON response from Heurist.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if not isinstance(label, str) or not label:
        raise ValueError("label must be a non-empty string")
    if domain not in ("enum", "relation"):
        raise ValueError("domain must be 'enum' or 'relation'")

    fields: dict = {
        "trm_ID": "0",
        "trm_Label": label,
        "trm_Domain": domain,
        "trm_ParentTermID": "0",
        "trm_Status": status,
    }
    if vocabulary_group_id is not None:
        fields["trm_VocabularyGroupID"] = str(vocabulary_group_id)
    if description is not None:
        fields["trm_Description"] = description
    if code is not None:
        fields["trm_Code"] = code
    if semantic_reference_url is not None:
        fields["trm_SemanticReferenceURL"] = semantic_reference_url

    return heurist_save_entity_create_only(
        session=session,
        entity="defTerms",
        fields=fields,
    )


def heurist_create_term(
    session: HeuristSession,
    label: str,
    parent_term_id: Any,
    description: Optional[str] = None,
    code: Optional[str] = None,
    inverse_term_id: Any = None,
    domain: Optional[str] = None,
    status: str = "open",
) -> dict:
    """Create a new term under an existing vocabulary or parent term.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    label:
        Term label.
    parent_term_id:
        Parent term or vocabulary ID.
    description:
        Optional description.
    code:
        Optional code.
    inverse_term_id:
        Optional inverse term ID.
    domain:
        Optional domain override. Use only when creating relation terms.
    status:
        Optional status. Defaults to ``"open"``.

    Returns
    -------
    dict
        Parsed JSON response from Heurist.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if not isinstance(label, str) or not label:
        raise ValueError("label must be a non-empty string")
    if parent_term_id is None:
        raise ValueError("parent_term_id is required")

    fields: dict = {
        "trm_ID": "0",
        "trm_Label": label,
        "trm_ParentTermID": str(parent_term_id),
        "trm_Status": status,
    }
    if description is not None:
        fields["trm_Description"] = description
    if code is not None:
        fields["trm_Code"] = code
    if inverse_term_id is not None:
        fields["trm_InverseTermID"] = str(inverse_term_id)
    if domain is not None:
        fields["trm_Domain"] = domain

    return heurist_save_entity_create_only(
        session=session,
        entity="defTerms",
        fields=fields,
    )


def heurist_create_rectype(
    session: HeuristSession,
    name: str,
    description: str,
    title_mask: str,
    rectype_group_id: Any,
    plural: Optional[str] = None,
    reference_url: Optional[str] = None,
    status: str = "open",
    show_in_lists: bool = True,
    show_description_on_edit_form: bool = True,
) -> dict:
    """Create a new Heurist record type.

    Safely creates a new ``defRecTypes`` entry. This helper is create-only and
    does not expose broad update semantics.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    name:
        Record type name.
    description:
        Record type description.
    title_mask:
        Human-readable title mask.
    rectype_group_id:
        Record type group ID.
    plural:
        Optional plural label.
    reference_url:
        Optional semantic/reference URI.
    status:
        Optional status. Defaults to ``"open"``.
    show_in_lists:
        Whether to show in lists. Defaults to ``True``.
    show_description_on_edit_form:
        Whether to show description on edit form. Defaults to ``True``.

    Returns
    -------
    dict
        Parsed JSON response from Heurist.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if not isinstance(name, str) or not name:
        raise ValueError("name must be a non-empty string")
    if not isinstance(description, str) or not description:
        raise ValueError("description must be a non-empty string")
    if not isinstance(title_mask, str) or not title_mask:
        raise ValueError("title_mask must be a non-empty string")
    if rectype_group_id is None:
        raise ValueError("rectype_group_id is required")

    fields: dict = {
        "rty_ID": "0",
        "rty_Name": name,
        "rty_Description": description,
        "rty_TitleMask": title_mask,
        "rty_RecTypeGroupID": str(rectype_group_id),
        "rty_Status": status,
        "rty_ShowInLists": _bool_string(show_in_lists),
        "rty_ShowDescriptionOnEditForm": _bool_string(show_description_on_edit_form),
    }
    if plural is not None:
        fields["rty_Plural"] = plural
    if reference_url is not None:
        fields["rty_ReferenceURL"] = reference_url

    return heurist_save_entity_create_only(
        session=session,
        entity="defRecTypes",
        fields=fields,
    )


def heurist_create_detail_type(
    session: HeuristSession,
    name: str,
    help_text: str,
    type: str,
    detail_type_group_id: Any,
    vocabulary_id: Any = None,
    target_rectype_ids: Any = None,
    extended_description: Optional[str] = None,
    semantic_reference_url: Optional[str] = None,
    status: str = "open",
    non_owner_visibility: str = "viewable",
    show_in_lists: bool = True,
) -> dict:
    """Create a new Heurist detail type (field type).

    Safely creates a new ``defDetailTypes`` entry. This helper is create-only
    and requires explicit vocabulary or pointer constraints when the field type
    needs them.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    name:
        Field name.
    help_text:
        Default help text.
    type:
        One of ``"enum"``, ``"float"``, ``"freetext"``, ``"blocktext"``,
        ``"date"``, ``"geo"``, ``"file"``, ``"resource"``, or ``"relmarker"``.
    detail_type_group_id:
        Detail type group ID.
    vocabulary_id:
        Required for ``"enum"`` and ``"relmarker"`` field types.
    target_rectype_ids:
        Optional target record type IDs for ``"resource"`` and ``"relmarker"``
        fields. May be a scalar, list, or comma-separated string.
    extended_description:
        Optional extended description.
    semantic_reference_url:
        Optional semantic/reference URI.
    status:
        Optional status. Defaults to ``"open"``.
    non_owner_visibility:
        Optional visibility. Defaults to ``"viewable"``.
    show_in_lists:
        Whether to show in lists. Defaults to ``True``.

    Returns
    -------
    dict
        Parsed JSON response from Heurist.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if not isinstance(name, str) or not name:
        raise ValueError("name must be a non-empty string")
    if not isinstance(help_text, str) or not help_text:
        raise ValueError("help_text must be a non-empty string")
    if not isinstance(type, str) or not type:
        raise ValueError("type must be a non-empty string")
    if detail_type_group_id is None:
        raise ValueError("detail_type_group_id is required")

    valid_types = (
        "enum", "float", "freetext", "blocktext", "date",
        "geo", "file", "resource", "relmarker",
    )
    if type not in valid_types:
        raise ValueError(f"type must be one of {valid_types}")

    if type in ("enum", "relmarker") and vocabulary_id is None:
        raise ValueError(
            f"Vocabulary-backed detail types require an explicit vocabulary_id. "
            f"Supply vocabulary_id when creating '{type}' fields."
        )

    fields: dict = {
        "dty_ID": "0",
        "dty_Name": name,
        "dty_HelpText": help_text,
        "dty_Type": type,
        "dty_DetailTypeGroupID": str(detail_type_group_id),
        "dty_Status": status,
        "dty_NonOwnerVisibility": non_owner_visibility,
        "dty_ShowInLists": _bool_string(show_in_lists),
    }
    if vocabulary_id is not None:
        fields["dty_JsonTermIDTree"] = str(vocabulary_id)
    if target_rectype_ids is not None:
        fields["dty_PtrTargetRectypeIDs"] = _id_csv(target_rectype_ids)
    if extended_description is not None:
        fields["dty_ExtendedDescription"] = extended_description
    if semantic_reference_url is not None:
        fields["dty_SemanticReferenceURL"] = semantic_reference_url

    return heurist_save_entity_create_only(
        session=session,
        entity="defDetailTypes",
        fields=fields,
    )


def heurist_attach_detail_type(
    session: HeuristSession,
    rectype_id: Any,
    detail_type_id: Any,
    display_name: Optional[str] = None,
    requirement: str = "optional",
    max_values: int = 1,
    display_width: Any = None,
    display_help_text: Optional[str] = None,
) -> dict:
    """Attach a detail type to a record type.

    Safely creates a new ``defRecStructure`` row linking an existing base
    field to a record type. This helper refuses to overwrite an existing
    structure row.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    rectype_id:
        Record type ID.
    detail_type_id:
        Detail type ID.
    display_name:
        Optional record-type-specific display name.
    requirement:
        Requirement type. Defaults to ``"optional"``.
    max_values:
        Repeatability flag. Defaults to ``1``.
    display_width:
        Optional display width.
    display_help_text:
        Optional record-type-specific help text.

    Returns
    -------
    dict
        Parsed JSON response from Heurist.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if rectype_id is None:
        raise ValueError("rectype_id is required")
    if detail_type_id is None:
        raise ValueError("detail_type_id is required")

    valid_requirements = ("required", "recommended", "optional", "forbidden")
    if requirement not in valid_requirements:
        raise ValueError(f"requirement must be one of {valid_requirements}")

    existing = heurist_raw_entity(
        session,
        action="search",
        entity="defRecStructure",
        query={
            "rst_RecTypeID": str(rectype_id),
            "rst_DetailTypeID": str(detail_type_id),
            "details": "full",
        },
    )

    reccount = 0
    if isinstance(existing, dict) and existing.get("status") == "ok":
        data = existing.get("data") or {}
        reccount = data.get("reccount", 0) if isinstance(data, dict) else 0

    if reccount > 0:
        raise ValueError(
            f"A record-structure row already exists for "
            f"rectype_id={rectype_id} and detail_type_id={detail_type_id}. "
            "This helper only creates new structure rows and refuses to "
            "overwrite an existing one."
        )

    fields: dict = {
        "rst_ID": "0",
        "rst_RecTypeID": str(rectype_id),
        "rst_DetailTypeID": str(detail_type_id),
        "rst_RequirementType": requirement,
        "rst_MaxValues": str(max_values),
    }
    if display_name is not None:
        fields["rst_DisplayName"] = display_name
    if display_width is not None:
        fields["rst_DisplayWidth"] = str(display_width)
    if display_help_text is not None:
        fields["rst_DisplayHelpText"] = display_help_text

    return heurist_save_entity_create_only(
        session=session,
        entity="defRecStructure",
        fields=fields,
    )


def heurist_save_entity_create_only(
    session: HeuristSession,
    entity: str,
    fields: dict,
    isfull: bool = True,
) -> dict:
    """Save a new entity definition (create-only guard).

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.
    entity:
        Entity name.
    fields:
        Entity fields dict.
    isfull:
        Whether to send a full payload. Defaults to ``True``.

    Returns
    -------
    dict
        Parsed JSON response from Heurist.
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if not isinstance(entity, str) or not entity:
        raise ValueError("entity must be a non-empty string")
    if not isinstance(fields, dict) or not fields:
        raise ValueError("fields must be a non-empty dict")

    primary_field = _entity_primary_field(entity)
    if primary_field is None:
        raise ValueError(
            f"No create-only schema mapping is defined for entity: {entity}"
        )

    fields = _assert_create_only_fields(fields, primary_field)

    response = heurist_raw_entity_edit(
        session=session,
        action="save",
        entity=entity,
        body={
            "fields": fields,
            "isfull": "1" if isfull else "0",
        },
    )

    _assert_ok(response, f"Heurist schema create failed for entity {entity}.")
    return response
