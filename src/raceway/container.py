from dataclasses import dataclass
from weakref import WeakKeyDictionary, WeakValueDictionary

from .exc import RacewayError
from .protocols import (
    IContainer,
    IRegistry,
    IRegistration,
    IDepSpec,
)


class ContainerError(RacewayError):
    """General error during container operations."""

    pass


class NotSet:
    pass


NOT_SET = NotSet()


def create_task_cache() -> WeakValueDictionary:
    return WeakValueDictionary()


def create_container_cache() -> WeakKeyDictionary:
    return WeakKeyDictionary()


def configure_container[V, W](
    registry: IRegistry,
    startup_task: W,
    task_proto: type[V],
) -> IContainer[V, W]:
    cache = create_container_cache()
    return Container(
        cache=cache, registry=registry, startup_task=startup_task, task_proto=task_proto
    )


@dataclass
class Container[V, W](IContainer[V, W]):

    cache: WeakKeyDictionary

    registry: IRegistry

    startup_task: W

    task_proto: type[V]

    def resolve_deps(
        self,
        dep_specs: tuple[tuple[str, IDepSpec], ...],
        task: V | None = None,
    ) -> tuple[tuple[str, object], ...]:
        resolved = []
        for dep_name, dep_spec in dep_specs:
            result = self.find_service(dep_spec.proto, task=task)
            if dep_spec.attr:
                result = getattr(result, dep_spec.attr)
            if dep_spec.key:
                result = result[dep_spec.key]  # type: ignore
            if dep_spec.call_kwargs is not None or dep_spec.call_args is not None:
                call_kwargs = (
                    dict(dep_spec.call_kwargs)
                    if dep_spec.call_kwargs is not None
                    else {}
                )
                call_args = dep_spec.call_args if dep_spec.call_args is not None else ()
                result = result(*call_args, **call_kwargs)  # type: ignore
            resolved.append((dep_name, result))
        return tuple(resolved)

    def make_service[T](
        self,
        reg: IRegistration[T],
        task: V | None = None,
    ) -> T:
        deps = dict(self.resolve_deps(reg.dep_specs, task=task))
        return reg.factory(**deps)

    def find_service[T](
        self,
        proto: type[T],
        task: V | None = None,
    ) -> T:
        if proto is self.task_proto:
            if task is None:
                raise ContainerError("Cannot find task because no task was provided!")
            return task  # type: ignore @TODO: Resolve this when we rewrite all the types.
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
                task_cache = self.cache.setdefault(self.startup_task, maybe_cache)
            v = task_cache.get(proto, NOT_SET)
            if v is NOT_SET:
                maybe_v = self.make_service(reg, task=task)
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
                maybe_v = self.make_service(reg, task=task)
                v = task_cache.setdefault(proto, maybe_v)
            return v
        else:
            return self.make_service(reg, task=task)
