from collections.abc import Hashable, Callable
from typing import Protocol, Literal


type IMarker = object #Hashable # @TODO: I'm not sure this makes sense.


type IService = object


type ITask = object


type ScopeType = Literal['task']|Literal['startup']|Literal['call']


class IDepSpec(Protocol):
    proto: IMarker


class IRegistration(Protocol):
    factory: Callable[..., IService]
    dep_specs: tuple[tuple[str, IDepSpec], ...]
    scope: ScopeType = 'startup'


class IRegistry(Protocol):
    def find(self, proto: IMarker) -> IRegistration | None: ...


class IContainer(Protocol):
    def make_service(self, proto: IMarker, reg: IRegistration, task: ITask | None=None) -> IService: ...
    def find_service(self, proto: IMarker, task: ITask | None = None) -> IService: ...


class IPlanner(Protocol):
    def queue_registration(self, proto: IMarker, reg: IRegistration) -> None: ...
    def create_registry(self) -> IRegistry: ...


class IStarter(Protocol):

    def start(self, planner: IPlanner) -> IContainer: ...
