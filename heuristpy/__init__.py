"""heuristpy - Python client for Heurist databases.

Provides a session-oriented Python client for working with Heurist databases.
Wraps Heurist authentication, metadata, and record retrieval endpoints and
establishes a foundation for safe record creation and update workflows.

Basic usage::

    from heuristpy import heurist_session, heurist_login, heurist_rectypes

    session = heurist_session(
        base_url="https://heurist.huma-num.fr/heurist",
        database="my_database",
    )
    session = heurist_login(session, username="user", password="pass")

    rectypes = heurist_rectypes(session)
"""

from .session import HeuristSession, heurist_session, heurist_login, heurist_logout
from .metadata import heurist_rectypes, heurist_fields, heurist_structure
from .records import (
    heurist_get_record,
    heurist_find_records,
    heurist_raw_record_output,
    heurist_raw_record_edit,
    heurist_raw_entity,
    heurist_create_record,
    heurist_replace_record,
    heurist_patch_record,
    heurist_link_record,
    heurist_restore_change,
    heurist_rollback,
    heurist_rollback_change,
)
from .schema_write import (
    heurist_raw_entity_edit,
    heurist_create_vocabulary_group,
    heurist_create_vocabulary,
    heurist_create_term,
    heurist_create_rectype,
    heurist_create_detail_type,
    heurist_attach_detail_type,
    heurist_save_entity_create_only,
)
from ._utils import HeuristChange

__all__ = [
    "HeuristSession",
    "HeuristChange",
    # Session
    "heurist_session",
    "heurist_login",
    "heurist_logout",
    # Metadata
    "heurist_rectypes",
    "heurist_fields",
    "heurist_structure",
    # Records – read
    "heurist_get_record",
    "heurist_find_records",
    "heurist_raw_record_output",
    "heurist_raw_entity",
    # Records – write
    "heurist_raw_record_edit",
    "heurist_create_record",
    "heurist_replace_record",
    "heurist_patch_record",
    "heurist_link_record",
    "heurist_restore_change",
    "heurist_rollback",
    "heurist_rollback_change",
    # Schema
    "heurist_raw_entity_edit",
    "heurist_create_vocabulary_group",
    "heurist_create_vocabulary",
    "heurist_create_term",
    "heurist_create_rectype",
    "heurist_create_detail_type",
    "heurist_attach_detail_type",
    "heurist_save_entity_create_only",
]
