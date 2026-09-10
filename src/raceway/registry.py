from dataclasses import dataclass
from types import MappingProxyType

from .protocols import IServiceMarker, IRegistration, IRegistry


def configure_registry(
    registrations: tuple[tuple[IServiceMarker, IRegistration], ...],
) -> IRegistry:
    return Registry(registrations=MappingProxyType(dict(registrations)))


@dataclass(frozen=True)
class Registry(IRegistry):

    registrations: MappingProxyType[IServiceMarker, IRegistration]

    def find(self, proto: IServiceMarker) -> IRegistration | None:
        return self.registrations.get(proto, None)
