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


#
# Protocols
#
class IServiceA(Protocol):
    def a_action(self):
        pass


class IServiceB(Protocol):
    def b_action(self):
        pass


class IServiceC(Protocol):
    def c_action(self):
        pass

class IServiceD(Protocol):
    def d_action(self):
        pass


class IServiceE(Protocol):
    def e_action(self):
        pass


class IServiceF(Protocol):
    def f_action(self):
        pass

#
# Implementations
#
@dataclass
class ServiceA(IServiceA):

    b_api: IServiceB

    def a_action(self):
        pass


@dataclass
class ServiceB(IServiceB):

    c_api: IServiceC

    def b_action(self):
        pass


@dataclass
class ServiceC(IServiceC):

    a_api: IServiceA

    def c_action(self):
        pass


@dataclass
class ServiceD(IServiceD):

    e_api: IServiceE

    def d_action(self):
        pass

@dataclass
class ServiceE(IServiceE):

    d_api: IServiceD

    def e_action(self):
        pass


@dataclass
class ServiceF(IServiceF):

    f_api: IServiceF

    def f_action(self):
        pass


def test_transitive_cycle():
    """
    Check for most common cycle: A needs B, B needs C but C needs A.
    """

    planner = Planner(reg_queue={})
    planner.queue_registration(
        IServiceA,
        Registration(ServiceA, (('b_api', DepSpec(proto=IServiceB)), ), scope='startup'))
    planner.queue_registration(
        IServiceB,
        Registration(ServiceB, (('c_api', DepSpec(proto=IServiceC)), ), scope='startup'))
    planner.queue_registration(
        IServiceC,
        Registration(ServiceC, (('a_api', DepSpec(proto=IServiceA)), ), scope='startup'))

    with pytest.raises(PlannerCycleError):
        _ = Starter().start(planner=planner)


def test_direct_cycle():
    """
    Check for direct circular: D needs E but E needs D.
    """
    planner = Planner(reg_queue={})
    planner.queue_registration(
        IServiceD,
        Registration(ServiceD, (('e_api', DepSpec(proto=IServiceE)), ), scope='startup'))
    planner.queue_registration(
        IServiceE,
        Registration(ServiceE, (('d_api', DepSpec(proto=IServiceD)), ), scope='startup'))
    with pytest.raises(PlannerCycleError, match="Dependency cycle: .* required before"):
        _ = Starter().start(planner=planner)


def test_self_cycle():
    """
    Check for self reference: A ... but A needs A.
    """
    planner = Planner(reg_queue={})
    planner.queue_registration(
        IServiceB,
        Registration(ServiceB, (('b_api', DepSpec(proto=IServiceB)), ), scope='startup')) # Made up deps
    with pytest.raises(PlannerCycleError, match="Dependency cycle: Cannot depend on self"):
        _ = Starter().start(planner=planner)


