from dataclasses import dataclass
from types import MappingProxyType

from .protocols import IRegistration, IRegistry, ScopeType, RegEntryType


def configure_registry(registrations: tuple[RegEntryType, ...]) -> IRegistry:
    return Registry(registrations=MappingProxyType(dict(registrations)))


@dataclass(frozen=True)
class Registry(IRegistry):

    registrations: MappingProxyType[type, IRegistration]

    def find[T](self, proto: type[T]) -> IRegistration[T] | None:
        return self.registrations.get(proto)

    def get_entries_by_scope(
        self,
        scope: ScopeType,
    ) -> tuple[RegEntryType, ...]:
        return tuple([(k, v) for (k, v) in self.registrations.items() if v.scope == scope])
