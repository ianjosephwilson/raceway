from collections.abc import Hashable
from dataclasses import dataclass
from weakref import WeakKeyDictionary, WeakValueDictionary

from .exc import RacewayError
from .protocols import (
    IContainer,
    IRegistry,
    ITask,
    IService,
    IMarker,
    IRegistration,
)


class ContainerError(RacewayError):
    """ General error during container operations. """
    pass


class NotSet:
    pass


NOT_SET = NotSet() # @TODO: Sentinel in python 3.15+


def create_task_cache() -> WeakValueDictionary[ITask, IService]:
    return WeakValueDictionary()


def create_container_cache() -> WeakKeyDictionary[IMarker, WeakValueDictionary[ITask, IService]]:
    return WeakKeyDictionary()


def configure_container(registry: IRegistry, startup_task: ITask) -> IContainer:
    cache = create_container_cache()
    return Container(cache=cache, registry=registry, startup_task=startup_task)


@dataclass
class Container(IContainer):

    cache: WeakKeyDictionary

    registry: IRegistry

    startup_task: ITask

    def make_service(self, proto: IMarker, reg: IRegistration, task: ITask|None=None) -> IService:
        deps = {}
        for dep_name, dep_spec in reg.dep_specs:
            deps[dep_name] = self.find_service(dep_spec.proto, task=task)
        return reg.factory(**deps)


    def find_service(self, proto: IMarker, task: ITask|None=None) -> IService:
        reg = self.registry.find(proto)
        if reg is None:
            raise ContainerError(f'Cannot find registration for given protocol: {proto}')
        if reg.scope == 'startup':
            # @TODO: (1/2) This seems like "THE" race condition spelled out.
            if self.startup_task in self.cache:
                task_cache = self.cache[self.startup_task]
            else:
                maybe_cache = create_task_cache()
                # We use the *result* of setdefault to try to avoid the race condition.
                task_cache = self.cache.setdefault(self.startup_task, maybe_cache)
            # @TODO: (1/2) This seems like "THE OTHER" race condition
            # in this case we should have just made these before hand but if we didn't
            # then there could be a "stampede" to make these which might be solvable but
            # ... kind of a waste of effort, maybe just force these to be preconstructed
            # and fail if they aren't for now?
            v = task_cache.get(proto, NOT_SET)
            if v is NOT_SET:
                v = self.make_service(proto, reg, task=task)
                task_cache[proto] = v
            return v
        elif reg.scope == 'task':
            if task is None:
                raise ContainerError('Cannot access task cache without providing a task!')
            # @TODO: (2/2) This seems like "THE" race condition spelled out.
            if task in self.cache:
                task_cache = self.cache[task]
            else:
                # We use the *result* of setdefault to try to avoid the race condition.
                maybe_cache = create_task_cache()
                task_cache = self.cache.setdefault(task, maybe_cache)
            # @TODO: (2/2) This seems like "THE OTHER" race condition
            # This probably isn't a big deal compared to the startup scope
            # stampede situation.
            v = task_cache.get(proto, NOT_SET)
            if v is NOT_SET:
                v = self.make_service(proto, reg, task=task)
                task_cache[proto] = v
            return v
        else:
            return self.make_service(proto, reg, task=task)






