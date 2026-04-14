"""Session management for heuristpy."""

from __future__ import annotations

import re
from typing import Any, Optional

import requests as _requests

from ._utils import _check_response


class HeuristSession:
    """A Heurist database session.

    Create a session with :func:`heurist_session` and authenticate it with
    :func:`heurist_login`.

    Parameters
    ----------
    base_url:
        Base Heurist URL, such as ``"https://heurist.huma-num.fr/heurist"``.
    database:
        Heurist database name.
    timeout:
        Request timeout in seconds. Defaults to ``30``.
    """

    def __init__(
        self, base_url: str, database: str, timeout: float = 30
    ) -> None:
        if not isinstance(base_url, str) or not base_url:
            raise ValueError("base_url must be a non-empty string")
        if not isinstance(database, str) or not database:
            raise ValueError("database must be a non-empty string")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be a positive number")

        self.base_url = re.sub(r"/+$", "", base_url)
        self.database = database
        self.timeout = float(timeout)
        self.authenticated = False
        self.current_user: Optional[Any] = None
        self._http = _requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _get(self, path: str, params: Optional[dict] = None) -> _requests.Response:
        resp = self._http.get(self._url(path), params=params, timeout=self.timeout)
        return _check_response(resp)

    def _post(self, path: str, data: Optional[dict] = None) -> _requests.Response:
        from ._utils import _encode_form_body

        flat_data = _encode_form_body(data) if data else {}
        resp = self._http.post(self._url(path), data=flat_data, timeout=self.timeout)
        return _check_response(resp)

    def __repr__(self) -> str:
        auth = "authenticated" if self.authenticated else "unauthenticated"
        return f"HeuristSession(database={self.database!r}, {auth})"


def heurist_session(
    base_url: str, database: str, timeout: float = 30
) -> HeuristSession:
    """Create a Heurist session.

    Parameters
    ----------
    base_url:
        Base Heurist URL, such as ``"https://heurist.huma-num.fr/heurist"``.
    database:
        Heurist database name.
    timeout:
        Request timeout in seconds. Defaults to ``30``.

    Returns
    -------
    HeuristSession
    """
    return HeuristSession(base_url=base_url, database=database, timeout=timeout)


def heurist_login(
    session: HeuristSession,
    username: str,
    password: str,
    session_type: str = "remember",
) -> HeuristSession:
    """Log in to Heurist.

    Authenticates a :class:`HeuristSession` and retains the returned session
    cookies for subsequent requests.

    Parameters
    ----------
    session:
        A :class:`HeuristSession`.
    username:
        Heurist username.
    password:
        Heurist password.
    session_type:
        Heurist session type. Defaults to ``"remember"``.

    Returns
    -------
    HeuristSession
        The authenticated session (modified in place and returned).
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")
    if not isinstance(username, str) or not username:
        raise ValueError("username must be a non-empty string")
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")

    resp = session._http.post(
        session._url("/hserv/controller/usr_info.php"),
        data={
            "db": session.database,
            "a": "login",
            "username": username,
            "password": password,
            "session_type": session_type,
        },
        timeout=session.timeout,
    )
    _check_response(resp)
    payload = resp.json()

    if payload.get("status") != "ok":
        msg = payload.get("message") or payload.get("msg") or "Unknown error"
        raise ValueError(f"Heurist login failed: {msg}")

    verify_resp = session._http.get(
        session._url("/hserv/controller/usr_info.php"),
        params={"db": session.database, "a": "verify_credentials"},
        timeout=session.timeout,
    )
    _check_response(verify_resp)
    verified = verify_resp.json()

    if verified.get("status") != "ok" or verified.get("data") is not True:
        raise ValueError(
            "Heurist login did not establish an authenticated session."
        )

    session.authenticated = True
    session.current_user = (payload.get("data") or {}).get("currentUser")
    return session


def heurist_logout(session: HeuristSession) -> HeuristSession:
    """Log out of Heurist.

    Parameters
    ----------
    session:
        An authenticated :class:`HeuristSession`.

    Returns
    -------
    HeuristSession
        The logged-out session (modified in place and returned).
    """
    if not isinstance(session, HeuristSession):
        raise TypeError("session must be a HeuristSession")

    session._http.post(
        session._url("/hserv/controller/usr_info.php"),
        data={"db": session.database, "a": "logout"},
        timeout=session.timeout,
    )
    session.authenticated = False
    session.current_user = None
    return session
