from dataclasses import dataclass
from typing import Annotated, Protocol

import pytest

from raceway.extractor import Extractor, Cabled
from raceway.registration import Registration
from raceway.planner import Planner
from raceway.starter import Starter
from raceway.protocols import IContainer


class ISettings(Protocol):
    def __getitem__(self, key: str) -> object: ...


@dataclass
class Settings(ISettings):
    def __getitem__(self, key: str) -> object:
        if key == "primary_colors":
            return ("red", "yellow", "blue")
        raise KeyError(key)


class IConfig(Protocol):
    def get_base_path(self, env: str, level: str) -> str: ...

    @property
    def settings(self) -> ISettings: ...


@dataclass
class ConfigService(IConfig):

    def get_base_path(self, env: str, level: str) -> str:
        if env == 'mars':
            return f"/app-mars/{level}"
        else:
            return f"/app-earth/{level}"

    @property
    def settings(self) -> ISettings:
        # This is not in the container because we make it during lookup.
        # This is not cached which I think is what we want...
        return Settings()


class IColorizer(Protocol):

    primary_colors: tuple[str, ...]

    base_path: str

    def colorize_int(self, int_value: int) -> str: ...


@dataclass
class ColorizerService(IColorizer):

    primary_colors: Annotated[
        tuple[str, ...], Cabled(IConfig, attr="settings", key="primary_colors")
    ]

    base_path: Annotated[str, Cabled(IConfig, attr="get_base_path", call_args=('mars',), call_kwargs=(('level', '1'),))]

    def colorize_int(self, int_value: int) -> str:
        return self.primary_colors[abs(int_value % 3)]


class TestMakeService:

    @pytest.fixture
    def container(self):
        ex = Extractor()
        planner = Planner(reg_queue={})
        planner.queue_registration(
            IConfig,
            Registration(ConfigService, ex.extract(ConfigService), scope="startup"),
        )
        planner.queue_registration(
            IColorizer,
            Registration(
                ColorizerService, ex.extract(ColorizerService), scope="startup"
            ),
        )
        yield Starter().start(planner=planner)

    def test_attr_and_key(self, container: IContainer):
        colorizer_api = container.find_service(IColorizer, task=None)
        assert len(colorizer_api.primary_colors) == 3  # check internals
        assert colorizer_api.colorize_int(15) == "red"

    def test_call(self, container: IContainer):
        colorizer_api = container.find_service(IColorizer, task=None)
        assert colorizer_api.base_path == "/app-mars/1"
