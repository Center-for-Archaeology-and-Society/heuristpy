"""Tests for session creation and configuration."""

import pytest

from heuristpy import HeuristSession, heurist_session


def test_heurist_session_creates_expected_structure():
    session = heurist_session(
        "https://heurist.huma-num.fr/heurist", "jalli_coalbed"
    )
    assert isinstance(session, HeuristSession)
    assert session.database == "jalli_coalbed"
    assert session.authenticated is False


def test_heurist_session_strips_trailing_slash():
    session = heurist_session("https://heurist.huma-num.fr/heurist/", "mydb")
    assert session.base_url == "https://heurist.huma-num.fr/heurist"


def test_heurist_session_strips_multiple_trailing_slashes():
    session = heurist_session("https://heurist.huma-num.fr/heurist///", "mydb")
    assert session.base_url == "https://heurist.huma-num.fr/heurist"


def test_heurist_session_default_timeout():
    session = heurist_session("https://heurist.huma-num.fr/heurist", "mydb")
    assert session.timeout == 30.0


def test_heurist_session_custom_timeout():
    session = heurist_session("https://heurist.huma-num.fr/heurist", "mydb", timeout=60)
    assert session.timeout == 60.0


def test_heurist_session_requires_base_url():
    with pytest.raises((ValueError, TypeError)):
        heurist_session("", "mydb")


def test_heurist_session_requires_database():
    with pytest.raises((ValueError, TypeError)):
        heurist_session("https://heurist.huma-num.fr/heurist", "")


def test_heurist_session_requires_positive_timeout():
    with pytest.raises((ValueError, TypeError)):
        heurist_session("https://heurist.huma-num.fr/heurist", "mydb", timeout=-1)


def test_heurist_session_repr():
    session = heurist_session("https://heurist.huma-num.fr/heurist", "mydb")
    assert "mydb" in repr(session)
    assert "unauthenticated" in repr(session)
