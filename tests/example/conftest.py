"""
Try to emulate a more real-world example of a service container surrounding
http requests.
"""

import pytest
from dataclasses import dataclass
from typing import Annotated, Protocol
from uuid import uuid4
from _pytest.fixtures import FixtureRequest

from raceway.protocols import IContainer, IInjector, IExtractor, ITask
from raceway.injector import configure_injector
from raceway.extractor import configure_extractor, Cabled
from raceway.planner import configure_planner
from raceway.registration import Registration
from raceway.starter import startup
from raceway.testing import IConfig, IAuth, IHTTPRequest


def pytest_configure(config) -> None:
    config.addinivalue_line(
        "markers",
        "http_request(session_kv): session key/value to add to http request session",
    )


@dataclass
class ConfigService(IConfig):

    _settings: dict[str, object]

    def __getitem__(self, key: str) -> object:
        return self._settings.get(key, None)


@dataclass
class HTTPRequest(IHTTPRequest):
    def __hash__(self):
        # We use the request id for the hashing function. In case we
        # need the "same" request to exist more than once.
        return id(self.request_id)

    def __eq__(self, other: object):
        # We use the request id as "identity"
        # during equal check instead of `is`.
        return isinstance(other, HTTPRequest) and self.request_id == other.request_id

    request_id: str
    session: dict[str, object]
    path: str


@dataclass
class AuthService(IAuth):

    request: IHTTPRequest

    user_session_key: Annotated[str, Cabled(IConfig, key="auth.session_key")]

    def is_logged_in(self) -> bool:
        user_id = self.request.session.get(self.user_session_key, None)
        return isinstance(user_id, str) and len(user_id) > 0


@pytest.fixture(scope="session")
def setting_kvs() -> tuple[tuple[str, str], ...]:
    return (
        # @NOTE: Not secure.
        ("auth.cookie_secret", f"test_{str(uuid4).replace('-', '')}"),
        ("auth.session_key", "user_id"),
    )


@pytest.fixture(scope="session")
def container_api(extractor_api, setting_kvs):
    def config_service_factory() -> IConfig:
        """A singleton created during startup."""
        return ConfigService(_settings=dict(setting_kvs))

    planner = configure_planner(task_proto=IHTTPRequest)
    planner.queue_registration(
        IConfig,
        Registration(config_service_factory, (), scope="startup"),
    )
    planner.queue_registration(
        IAuth,
        Registration(AuthService, extractor_api.extract(AuthService), scope="task"),
    )
    return startup(planner=planner)


@pytest.fixture(scope="session")
def extractor_api() -> IExtractor:
    return configure_extractor()


@pytest.fixture(scope="session")
def injector_api(extractor_api) -> IInjector:
    return configure_injector(extractor=extractor_api, task_proto=IHTTPRequest)


@pytest.fixture
def config_api(container_api) -> IConfig:
    return container_api.find_service(IConfig, task=None)


@pytest.fixture
def http_request(request: FixtureRequest) -> IHTTPRequest:
    marker = request.node.get_closest_marker("http_request")
    opts = {"path": "/", "session": {}, "request_id": f"request--{str(uuid4())}"}
    if marker is not None:
        session_kv = marker.kwargs.get("session_kv", None)
        if session_kv is not None:
            opts["session"][session_kv[0]] = session_kv[1]
    return HTTPRequest(**opts)


@pytest.fixture
def auth_api(container_api, http_request) -> IAuth:
    return container_api.find_service(IAuth, task=http_request)
