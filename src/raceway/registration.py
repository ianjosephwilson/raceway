from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from .protocols import IMarker, IService, ScopeType, IDepSpec, IRegistration


@dataclass
class DepSpec(IDepSpec):

    proto: IMarker


@dataclass
class Registration(IRegistration):

    factory: Callable[..., IService]
    """ Callable whose result in the service. """

    dep_specs: tuple[tuple[str, IDepSpec], ...]
    """ Tuple of name/spec pairs that must be resolved to pass to factory. """

    scope: ScopeType = 'startup'
