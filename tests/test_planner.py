from dataclasses import dataclass
from typing import Protocol

import pytest

from raceway.extractor import configure_extractor
from raceway.registration import (
    DepSpec,
    Registration,
)
from raceway.planner import (
    configure_planner,
    PlannerError,
)
from raceway.protocols import ITask, IExtractor, IPlanner


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
def extractor_api() -> IExtractor:
    """Create default extractor."""
    return configure_extractor()


@pytest.fixture
def planner_api(extractor_api) -> IPlanner:
    """Create an empty planner."""
    return configure_planner(task_proto=ITask, extractor_api=extractor_api)


class TestCycleCheck:

    def test_transitive_cycle(self, planner_api):
        """
        Check for most common cycle: A needs B, B needs C but C needs A.
        """

        planner_api.queue_registration(
            IServiceA,
            Registration(
                ServiceA, (("b_api", DepSpec(proto=IServiceB)),), scope="startup"
            ),
        )
        planner_api.queue_registration(
            IServiceB,
            Registration(
                ServiceB, (("c_api", DepSpec(proto=IServiceC)),), scope="startup"
            ),
        )
        planner_api.queue_registration(
            IServiceC,
            Registration(
                ServiceC, (("a_api", DepSpec(proto=IServiceA)),), scope="startup"
            ),
        )

        with pytest.raises(PlannerError, match="Dependency cycle: .* required before"):
            planner_api.validate_reg_queue()

    def test_direct_cycle(self, planner_api):
        """
        Check for direct circular: D needs E but E needs D.
        """
        planner_api.queue_registration(
            IServiceD,
            Registration(
                ServiceD, (("e_api", DepSpec(proto=IServiceE)),), scope="startup"
            ),
        )
        planner_api.queue_registration(
            IServiceE,
            Registration(
                ServiceE, (("d_api", DepSpec(proto=IServiceD)),), scope="startup"
            ),
        )
        with pytest.raises(PlannerError, match="Dependency cycle: .* required before"):
            planner_api.validate_reg_queue()

    def test_self_cycle(self, planner_api):
        """
        Check for self reference: A ... but A needs A.
        """
        planner_api.queue_registration(
            IServiceB,
            Registration(
                ServiceB, (("b_api", DepSpec(proto=IServiceB)),), scope="startup"
            ),
        )  # Made up deps
        with pytest.raises(
            PlannerError, match="Dependency cycle: .* depends on itself"
        ):
            planner_api.validate_reg_queue()


def test_duplicate_check(planner_api):
    planner_api.queue_registration(
        IServiceA, Registration(ServiceA, (), scope="startup")
    )
    with pytest.raises(PlannerError, match="Each protocol can only be registered once"):
        _ = planner_api.queue_registration(
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
def test_scope_check(planner_api, dep_scope, parent_scope):
    planner_api.queue_registration(
        IServiceB, Registration(ServiceB, (), scope=dep_scope)
    )
    planner_api.queue_registration(
        IServiceA,
        Registration(
            ServiceA, (("b_api", DepSpec(proto=IServiceB)),), scope=parent_scope
        ),
    )
    with pytest.raises(PlannerError, match="Scope mismatch"):
        planner_api.validate_reg_queue()
