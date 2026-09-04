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
    """General error during container operations."""

    pass


class NotSet:
    pass


NOT_SET = NotSet()


def create_task_cache() -> WeakValueDictionary[ITask, IService]:
    return WeakValueDictionary()


def create_container_cache() -> (
    WeakKeyDictionary[IMarker, WeakValueDictionary[ITask, IService]]
):
    return WeakKeyDictionary()


def configure_container(
    registry: IRegistry,
    startup_task: ITask,
) -> IContainer:
    cache = create_container_cache()
    return Container(cache=cache, registry=registry, startup_task=startup_task)


@dataclass
class Container(IContainer):

    cache: WeakKeyDictionary

    registry: IRegistry

    startup_task: ITask

    def make_service(
        self,
        proto: IMarker,
        reg: IRegistration,
        task: ITask | None = None,
    ) -> IService:
        deps = {}
        for dep_name, dep_spec in reg.dep_specs:
            result = self.find_service(dep_spec.proto, task=task)
            if dep_spec.attr:
                result = getattr(result, dep_spec.attr)
            if dep_spec.key:
                result = result[dep_spec.key] # type: ignore
            if dep_spec.call_kwargs is not None or dep_spec.call_args is not None:
                call_kwargs = dict(dep_spec.call_kwargs) if dep_spec.call_kwargs else {}
                call_args = dep_spec.call_args if dep_spec.call_args else  ()
                result = result(*call_args, **call_kwargs) # type: ignore
            deps[dep_name] = result
        return reg.factory(**deps)

    def find_service(
        self,
        proto: IMarker,
        task: ITask | None = None,
    ) -> IService:
        reg = self.registry.find(proto)
        if reg is None:
            raise ContainerError(
                f"Cannot find registration for given protocol: {proto}"
            )
        if reg.scope == "startup":
            if self.startup_task in self.cache:
                task_cache = self.cache[self.startup_task]
            else:
                maybe_cache = create_task_cache()
                # We use the *result* of setdefault to try to avoid the race condition.
                task_cache = self.cache.setdefault(
                    self.startup_task, maybe_cache
                )
            v = task_cache.get(proto, NOT_SET)
            if v is NOT_SET:
                maybe_v = self.make_service(proto, reg, task=task)
                v = task_cache.setdefault(proto, maybe_v)
            return v
        elif reg.scope == "task":
            if task is None:
                raise ContainerError(
                    "Cannot access task cache without providing a task!"
                )
            if task in self.cache:
                task_cache = self.cache[task]
            else:
                # We use the *result* of setdefault to try to avoid the race condition.
                maybe_cache = create_task_cache()
                task_cache = self.cache.setdefault(task, maybe_cache)
            v = task_cache.get(proto, NOT_SET)
            if v is NOT_SET:
                maybe_v = self.make_service(proto, reg, task=task)
                v = task_cache.setdefault(proto, maybe_v)
            return v
        else:
            return self.make_service(proto, reg, task=task)
