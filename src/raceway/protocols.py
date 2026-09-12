from collections.abc import Callable
from typing import Protocol, Literal


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
    def find[T](
        self,
        proto: type[T],
    ) -> IRegistration[T] | None: ...


class IContainer[V, W](Protocol):
    startup_task: W

    task_proto: type[V]

    def find_service[T](
        self,
        proto: type[T],
        task: V | None = None,
    ) -> T: ...


class IPlanner[V](Protocol):

    def get_task_proto(self) -> type[V]: ...

    def queue_registration[S](
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
