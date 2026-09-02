from collections import defaultdict
from collections.abc import Hashable
from dataclasses import dataclass
from weakref import WeakKeyDictionary, WeakValueDictionary

from .exc import RacewayError
from .registry import Registry
from .protocols import ScopeType, IRegistry, IPlanner, IMarker, IRegistration


def can_depend_on(scope: ScopeType, dep_scope: ScopeType):
    if dep_scope == 'startup':
        return scope in ('call', 'task', 'startup')
    elif dep_scope == 'task':
        return scope in ('call', 'task')
    else: # call
        return scope == 'call'


class PlannerError(RacewayError):
    """ General error during planner operations. """
    pass


class PlannerCycleError(PlannerError):
    pass


@dataclass
class Planner(IPlanner):

    """
    Build a registry from a cohesive set of registrations.
    """
    reg_queue: dict[IMarker, IRegistration]

    def queue_registration(self, proto: IMarker, reg: IRegistration):
        if proto in self.reg_queue:
            raise PlannerError('Each protocol can only be registered once.')
        self.reg_queue[proto] = reg

    def validate_reg_queue(self) -> None:
        """
        Validate the registrations make sense.... no mistaks.

        - Check if dependencies are resolvable.
        - Check that scopes make sense.
        - Check for cycles.

        """
        dep_lookup: dict[IMarker, list[IMarker]] = defaultdict(list) # Fast-lookup for cycle checks.
        for proto, reg in self.reg_queue.items():
            for dep_name, dep_spec in reg.dep_specs:
                dep_lookup[proto].append(dep_spec.proto)
                dep_reg = self.reg_queue.get(dep_spec.proto)
                if dep_reg is None:
                    raise PlannerError(f'Missing registration: Cannot find dependency {dep_name} with protocol: {dep_spec.proto}')
                elif not can_depend_on(reg.scope, dep_reg.scope):
                    raise PlannerError(f'Scope mismatch: {proto}:{reg.scope} cannot depend on {dep_spec.proto}:{dep_reg.scope}')
        for proto in self.reg_queue:
            self._validate_registration(proto, dep_lookup)

    def _validate_registration(self, proto: IMarker, dep_lookup: dict[IMarker, list[IMarker]]) -> None:
        """ Validate registration, mostly just checks for cycles. """
        last_idx = 0
        topo = {proto: last_idx}
        resolve = [proto]
        while resolve:
            start = resolve.pop()
            start_idx = topo[start]
            for end in dep_lookup.get(start, ()):
                # A -> B; B -> C; etc. C -> A
                # start in topo and end in topo and
                end_idx = topo.get(end, None)
                if end_idx is not None:
                    if start_idx > end_idx:
                        raise PlannerCycleError(f'Dependency cycle: {start} depends on {end} but {end} required before {start}.')
                    elif start_idx == end_idx:
                        raise PlannerCycleError(f'Dependency cycle: Cannot depend on self.')
                else:
                    last_idx += 1
                    topo[end] = last_idx
                    resolve.append(end)

    def create_registry(self) -> IRegistry:
        self.validate_reg_queue()
        return Registry(registrations=self.reg_queue)

