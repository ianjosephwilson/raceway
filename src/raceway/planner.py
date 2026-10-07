from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from .exc import RacewayError
from .registry import configure_registry
from .protocols import (
    IRegistry,
    IPlanner,
    IRegistration,
    IExtractor,
    ScopeType,
)
from .registration import Registration
from .rules import can_depend_on


class PlannerError(RacewayError):
    """General error during planner operations."""

    pass


def configure_planner(task_proto, extractor_api: IExtractor) -> IPlanner:
    return Planner(reg_queue={}, task_proto=task_proto, extractor_api=extractor_api)


@dataclass
class Planner[V](IPlanner):
    """
    Build a registry from a cohesive set of registrations.
    """

    reg_queue: dict

    task_proto: type[V]

    extractor_api: IExtractor

    def get_task_proto(self) -> type[V]:
        return self.task_proto

    def queue_extracted_registration[T](
        self,
        proto: type[T],
        service_factory: Callable[..., T],
        scope: ScopeType,
        factory_kwargs: tuple[tuple[str, object], ...] = (),
    ) -> None:
        dep_specs = self.extractor_api.extract(service_factory)
        return self.queue_registration(
            proto,
            Registration(
                factory=service_factory,
                dep_specs=dep_specs,
                scope=scope,
                factory_kwargs=factory_kwargs,
            ),
        )

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
                            f"Missing dependency: {proto} depends on {dep_name}={dep_spec.proto}"
                        )
                    dep_scope = dep_reg.scope

                if not can_depend_on(reg.scope, dep_scope):
                    raise PlannerError(
                        f"Scope mismatch: {proto}:{reg.scope} cannot depend on {dep_spec.proto}:{dep_scope}"  # noqa B950
                    )

        self.check_for_cycles(dep_lookup)

    def check_for_cycles(
        self,
        children_lookup: dict[object, list[object]],
    ) -> list[object]:
        """
        Check that the dependency graph is a DAG.

        - Every node must be in `children_lookup` even leaves.
        """
        topo = []
        done = set()  # @NOTE: This set is for optimizing containment check.
        subroots = list(children_lookup.keys())
        for subroot in subroots:
            if subroot in done:
                continue
            # Use this crude command string to track ascending/descending as we
            # traverse the dependency graph depth-first right-to-left.
            moves: list[tuple[str, object]] = [("descend", subroot)]
            while moves:
                direction, node = moves.pop()
                if direction == "ascend":
                    done.add(node)
                    # @NOTE: All dependencies for this node must be in the topo.
                    topo.append(node)
                elif direction == "descend":
                    moves.append(("ascend", node))
                    for child in children_lookup[node]:
                        if child in done:
                            continue
                        elif ("ascend", child) in moves:
                            if node == child:
                                raise PlannerError(
                                    f"Dependency cycle caused by {node} depending on itself."
                                )
                            else:
                                resolution_path = (
                                    "\n <= ".join(
                                        [str(a[1]) for a in moves if a[0] == "ascend"]
                                    )
                                    + f"\n <=> {child}"
                                )
                                e = PlannerError(
                                    f"Dependency cycle occurred resolving dependencies for {subroot}."
                                )
                                e.add_note(resolution_path)
                                raise e
                        else:
                            moves.append(("descend", child))
                else:
                    raise AssertionError(f"Unknown direction {direction=} {node=}")
        return topo

    def create_registry(self) -> IRegistry:
        self.validate_reg_queue()
        return configure_registry(
            registrations=tuple(
                [(proto, reg) for (proto, reg) in self.reg_queue.items()]
            )
        )
