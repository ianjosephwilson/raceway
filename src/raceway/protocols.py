from collections.abc import Callable
from typing import Protocol, Literal

type IMarker = object


class IService(Protocol):
    pass


class ITask(Protocol):

    def __hash__(self) -> int: ...
    def __eq__(self, other: object) -> bool: ...


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
        proto: type[IService],
    ) -> IRegistration | None: ...


class IContainer(Protocol):
    def find_service[T](
        self,
        proto: type[T],
        task: ITask | None = None,
    ) -> T: ...


class IPlanner(Protocol):

    def get_task_proto(self) -> type[ITask]: ...

    def queue_registration[S: IService](
        self,
        proto: type[S],
        reg: IRegistration[S],
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
