from collections import defaultdict
from dataclasses import dataclass

from .exc import RacewayError
from .registry import configure_registry
from .protocols import (
    IRegistry,
    IPlanner,
    IRegistration,
)
from .rules import can_depend_on


class PlannerError(RacewayError):
    """General error during planner operations."""

    pass


def configure_planner(task_proto) -> IPlanner:
    return Planner(reg_queue={}, task_proto=task_proto)


@dataclass
class Planner[V](IPlanner):
    """
    Build a registry from a cohesive set of registrations.
    """

    reg_queue: dict

    task_proto: type[V]

    def get_task_proto(self) -> type[V]:
        return self.task_proto

    def queue_registration[T](self, proto: type[T], reg: IRegistration[T]) -> None:
        if proto in self.reg_queue:
            raise PlannerError("Each protocol can only be registered once.")
        self.reg_queue[proto] = reg

    def validate_reg_queue(self) -> None:
        """
        Validate the registrations make sense.... no mistaks.

        - Check if dependencies are resolvable.
        - Check that scopes make sense.
        - Check for cycles.

        """
        dep_lookup = defaultdict(list)
        for proto, reg in self.reg_queue.items():
            for dep_name, dep_spec in reg.dep_specs:
                dep_lookup[proto].append(dep_spec.proto)
                # Special handling for the actual task protocol.
                if dep_spec.proto is self.task_proto:
                    dep_scope = "task"
                else:
                    dep_reg = self.reg_queue.get(dep_spec.proto)
                    if dep_reg is None:
                        raise PlannerError(
                            f"Missing dependency: {dep_name}: {dep_spec.proto}"
                        )
                    dep_scope = dep_reg.scope

                if not can_depend_on(reg.scope, dep_scope):
                    raise PlannerError(
                        f"Scope mismatch: {proto}:{reg.scope} cannot depend on {dep_spec.proto}:{dep_scope}"  # noqa B950
                    )
        for proto in self.reg_queue:
            self._validate_registration(proto, dep_lookup)

    def _validate_registration[T](
        self, proto: type[T], dep_lookup: dict[type, list]
    ) -> None:
        """Validate registration, mostly just checks for cycles."""
        last_idx = 0
        topo = {proto: last_idx}
        resolve = [proto]
        while resolve:
            start = resolve.pop()
            start_idx = topo[start]
            for end in dep_lookup.get(start, ()):
                end_idx = topo.get(end, None)
                if end_idx is not None:
                    if start_idx > end_idx:
                        raise PlannerError(
                            f"Dependency cycle: {start} depends on {end} but {end} required before {start}."  # noqa B950
                        )
                    elif start_idx == end_idx:
                        raise PlannerError(
                            f"Dependency cycle: {start} depends on itself."
                        )
                else:
                    last_idx += 1
                    topo[end] = last_idx
                    resolve.append(end)

    def create_registry(self) -> IRegistry:
        self.validate_reg_queue()
        return configure_registry(
            registrations=tuple(
                [(proto, reg) for (proto, reg) in self.reg_queue.items()]
            )
        )
