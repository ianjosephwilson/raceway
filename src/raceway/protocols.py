from collections.abc import Callable
from typing import Protocol, Literal


type IMarker = object


type IService = object


type ITask = object


type ScopeType = Literal["task"] | Literal["startup"] | Literal["call"]


class IDepSpec[T](Protocol):
    proto: type[T]
    attr: str | None
    key: str | None
    call_args: tuple | None = None
    call_kwargs: tuple[tuple[str, object], ...] | None = None


class IRegistration[T](Protocol):
    factory: Callable[..., T]
    dep_specs: tuple[tuple[str, IDepSpec], ...]
    scope: ScopeType = "startup"


class IRegistry(Protocol):
    def find(
        self,
        proto: IMarker,
    ) -> IRegistration | None: ...


class IContainer(Protocol):
    """def make_service[T](
        self,
        proto: type[T],
        reg: IRegistration,
        task: ITask | None = None,
    ) -> T: ..."""

    def find_service[T](
        self,
        proto: type[T],
        task: ITask | None = None,
    ) -> T: ...


class IPlanner(Protocol):
    def queue_registration(
        self,
        proto: IMarker,
        reg: IRegistration,
    ) -> None: ...

    def create_registry(self) -> IRegistry: ...


class IStarter(Protocol):
    def start(
        self,
        planner: IPlanner,
    ) -> IContainer: ...


class IExtractor(Protocol):
    def extract(
        self,
        service_factory: Callable,
    ) -> tuple[tuple[str, IDepSpec], ...]: ...


class ILoader(Protocol):
    planner: IPlanner
    extractor: IExtractor
