from dataclasses import dataclass
from typing import Protocol

import pytest

from raceway.registration import (
    DepSpec,
    Registration,
)
from raceway.planner import (
    Planner,
    PlannerError,
)


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


@pytest.fixture
def planner():
    """Create an empty planner."""
    return Planner(reg_queue={})


class TestCycleCheck:

    def test_transitive_cycle(self, planner):
        """
        Check for most common cycle: A needs B, B needs C but C needs A.
        """

        planner.queue_registration(
            IServiceA,
            Registration(
                ServiceA, (("b_api", DepSpec(proto=IServiceB)),), scope="startup"
            ),
        )
        planner.queue_registration(
            IServiceB,
            Registration(
                ServiceB, (("c_api", DepSpec(proto=IServiceC)),), scope="startup"
            ),
        )
        planner.queue_registration(
            IServiceC,
            Registration(
                ServiceC, (("a_api", DepSpec(proto=IServiceA)),), scope="startup"
            ),
        )

        with pytest.raises(PlannerError, match="Dependency cycle: .* required before"):
            planner.validate_reg_queue()

    def test_direct_cycle(self, planner):
        """
        Check for direct circular: D needs E but E needs D.
        """
        planner.queue_registration(
            IServiceD,
            Registration(
                ServiceD, (("e_api", DepSpec(proto=IServiceE)),), scope="startup"
            ),
        )
        planner.queue_registration(
            IServiceE,
            Registration(
                ServiceE, (("d_api", DepSpec(proto=IServiceD)),), scope="startup"
            ),
        )
        with pytest.raises(PlannerError, match="Dependency cycle: .* required before"):
            planner.validate_reg_queue()

    def test_self_cycle(self, planner):
        """
        Check for self reference: A ... but A needs A.
        """
        planner.queue_registration(
            IServiceB,
            Registration(
                ServiceB, (("b_api", DepSpec(proto=IServiceB)),), scope="startup"
            ),
        )  # Made up deps
        with pytest.raises(
            PlannerError, match="Dependency cycle: .* depends on itself"
        ):
            planner.validate_reg_queue()


def test_duplicate_check(planner):
    planner.queue_registration(IServiceA, Registration(ServiceA, (), scope="startup"))
    with pytest.raises(PlannerError, match="Each protocol can only be registered once"):
        _ = planner.queue_registration(
            IServiceA, Registration(ServiceA, (), scope="startup")
        )


@pytest.mark.parametrize(
    ("dep_scope", "parent_scope"),
    [
        ("task", "startup"),
        ("call", "startup"),
        ("call", "task"),
    ],
)
def test_scope_check(planner, dep_scope, parent_scope):
    planner.queue_registration(IServiceB, Registration(ServiceB, (), scope=dep_scope))
    planner.queue_registration(
        IServiceA,
        Registration(
            ServiceA, (("b_api", DepSpec(proto=IServiceB)),), scope=parent_scope
        ),
    )
    with pytest.raises(PlannerError, match="Scope mismatch"):
        planner.validate_reg_queue()
