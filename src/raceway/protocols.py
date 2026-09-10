from collections.abc import Callable
from typing import Protocol, Literal

type IServiceMarker = object
""" Marker used to track service info.

Usage:
  - Used as a key to map to a cached serviced instance in the container.
  - Used as a key to map to a registration in the registry.
"""


class IService(Protocol):
    pass


class ITask(IService, Protocol):

    def __hash__(self) -> int: ...
    def __eq__(self, other: object) -> bool: ...


type ScopeType = Literal["task"] | Literal["startup"] | Literal["call"]


class IDepSpec(Protocol):
    proto: IServiceMarker
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
        proto: IServiceMarker,
    ) -> IRegistration | None: ...


class IContainer(Protocol):
    def find_service(
        self,
        proto: IServiceMarker,
        task: ITask | None = None,
    ) -> IService: ...


class IPlanner(Protocol):

    def get_task_proto(self) -> IServiceMarker: ...

    def queue_registration(
        self,
        proto: IServiceMarker,
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
