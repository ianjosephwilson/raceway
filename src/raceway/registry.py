from dataclasses import dataclass
from types import MappingProxyType

from .protocols import IRegistration, IRegistry

type RegTupleType[T] = tuple[type[T], IRegistration[T]]


def configure_registry(registrations: tuple[RegTupleType, ...]) -> IRegistry:
    return Registry(registrations=MappingProxyType(dict(registrations)))


@dataclass(frozen=True)
class Registry(IRegistry):

    registrations: MappingProxyType[type, IRegistration]

    def find[T](self, proto: type[T]) -> IRegistration[T] | None:
        return self.registrations.get(proto)
