from dataclasses import dataclass
from typing import Literal
from collections.abc import Callable

from .protocols import IMarker, IRegistration, IRegistry


@dataclass
class Registry(IRegistry):

    registrations: dict[IMarker, IRegistration] # @TODO: frozendict
    """ Protocol factory registration lookup. """

    def find(self, proto: IMarker) -> IRegistration | None:
        return self.registrations.get(proto, None)
