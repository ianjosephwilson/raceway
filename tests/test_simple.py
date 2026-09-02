from dataclasses import dataclass
from typing import Protocol

import pytest

from raceway.registration import (
    DepSpec,
    Registration,
)
from raceway.planner import (
    Planner,
    PlannerCycleError,
)
from raceway.starter import Starter


class IService1(Protocol):

    def action1(self) -> str: ...


@dataclass
class Service1:

    def action1(self) -> str:
        return '1 is ok'


class IService2(Protocol):

    def action2(self) -> str: ...


@dataclass
class Service2:

    api1: IService1

    def action2(self):
        return f"""
{self.api1.action1()}
2 is ok, too
"""


@dataclass()
class DummyRequest:

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other


def test_main():
    planner = Planner(reg_queue={})

    planner.queue_registration(
        IService1,
        Registration(Service1, (), scope='startup'))
    planner.queue_registration(
        IService2,
        Registration(factory=Service2, dep_specs=(('api1', DepSpec(proto=IService1)),), scope='task'))


    container = Starter().start(planner=planner)

    task1 = DummyRequest()
    api2 = container.find_service(IService2, task=task1)
    assert '' in api2.action2()
    api2 = container.find_service(IService2, task=task1)
    assert '' in api2.action2()
