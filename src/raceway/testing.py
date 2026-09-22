"""
Testing protocols and utilities.

We define these with the source because otherwise they are hard to share between
the tests.
"""

from typing import Protocol

from .protocols import ITask


class IConfig(Protocol):
    """Manages accesses to configuration set at startup."""

    def __getitem__(self, key: str) -> object: ...


class IHTTPRequest(ITask, Protocol):
    """HTTPRequests are the "tasks" that the caching is keyed to."""

    request_id: str
    session: dict[str, object]
    path: str


class IAuth(Protocol):
    """Manages authentication logic for application."""

    def is_logged_in(self) -> bool: ...


class HTTPUnauthorized(Exception):
    """Dummy http exception."""

    pass
