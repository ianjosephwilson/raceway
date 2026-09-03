from dataclasses import dataclass
from types import MappingProxyType

from .protocols import IMarker, IRegistration, IRegistry


def configure_registry(
    registrations: tuple[tuple[IMarker, IRegistration], ...],
) -> IRegistry:
    return Registry(registrations=MappingProxyType(dict(registrations)))


@dataclass(frozen=True)
class Registry(IRegistry):

    registrations: MappingProxyType[IMarker, IRegistration]

    def find(self, proto: IMarker) -> IRegistration | None:
        return self.registrations.get(proto, None)
