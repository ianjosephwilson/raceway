"""
Helpers for wrapping callables so that the container can inject services.
"""

from collections.abc import Callable
from dataclasses import dataclass

from .protocols import IExtractor, IInjector, IContainer
from .exc import RacewayError


class InjectionError(RacewayError):
    pass


def configure_injector[V](extractor: IExtractor, task_proto: type[V]) -> Injector[V]:
    return Injector(extractor=extractor, task_proto=task_proto)


@dataclass()
class Injector[V](IInjector):

    extractor: IExtractor

    task_proto: type[V]

    def wrap_in_inject(
        self, func: Callable, validate_with_container: IContainer | None = None
    ) -> Callable:
        """Wrap a function call in a function that first resolves any
        dependencies, any remaining kwargs must be passed when executed.

        This is assumed to be in the "call" scope so a task must always be
        provided.

        The result is not cached but the dependency specifications
        are held in the closure until the closure is removed.
        """
        # Extract the deps now...
        dep_specs = self.extractor.extract(func)

        # We will just do the simplest checks possible for now and assume
        # the configuration is complete otherwise just fail at runtime.
        if validate_with_container is not None:
            validate_with_container.validate_dep_specs(dep_specs, scope="call")

        def inject_then_call(
            container: IContainer,
            task: V,
            **overrides: dict[str, object],
        ) -> Callable:
            if not task:
                raise InjectionError("Task must be provided when 'func' is called.")
            # ... resolve the deps later when called.
            deps = container.resolve_deps(dep_specs, task=task)
            return func(**dict(deps, **overrides))

        return inject_then_call
