from dataclasses import dataclass
from typing import Protocol

import pytest

from raceway.extractor import configure_extractor
from raceway.registration import Registration
from raceway.planner import configure_planner
from raceway.starter import startup
from raceway.injector import configure_injector
from raceway.protocols import IContainer, ITask, IInjector, IExtractor


class IJobTask(ITask, Protocol):

    def get_color(self) -> str: ...


@dataclass
class JobTask(IJobTask):

    def __hash__(self):
        return id(self)

    def __eq__(self, other: object):
        return self is other

    id: int

    color: str

    def get_color(self) -> str:
        return self.color


class IPainter(Protocol):

    def paint(self, thing: str) -> str: ...


@dataclass
class PainterService(IPainter):

    job_api: IJobTask

    def paint(self, thing: str) -> str:
        return f"{thing} is now {self.job_api.get_color()}."


class TestWrapInInject:

    @pytest.fixture
    def extractor_api(self):
        return configure_extractor()

    @pytest.fixture
    def injector_api(self, extractor_api: IExtractor):
        return configure_injector(extractor=extractor_api, task_proto=IJobTask)

    @pytest.fixture
    def container_api(self, extractor_api):
        planner = configure_planner(task_proto=IJobTask)
        planner.queue_registration(
            IPainter,
            Registration(
                PainterService, extractor_api.extract(PainterService), scope="task"
            ),
        )
        yield startup(planner=planner)

    def test_wrap_no_overrides(
        self, container_api: IContainer, injector_api: IInjector
    ):
        task = JobTask(id=100, color="blue")

        def paint_house(
            painter_api: IPainter,
            task: IJobTask,
        ) -> str:
            return painter_api.paint("My house")

        text = injector_api.wrap_in_inject(paint_house)(container_api, task=task)
        assert text == "My house is now blue."

    def test_wrap_override_args(
        self, container_api: IContainer, injector_api: IInjector
    ):
        task = JobTask(id=101, color="green")

        def paint_house(
            painter_api: IPainter,
            whose: str,  # This should not be injected.
        ) -> str:
            return painter_api.paint(f"{whose} house")

        text = injector_api.wrap_in_inject(paint_house)(
            container_api, task=task, whose="Their"
        )
        assert text == "Their house is now green."
