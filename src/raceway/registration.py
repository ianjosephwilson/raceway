from collections.abc import Callable
from dataclasses import dataclass

from .protocols import ScopeType, IDepSpec, IRegistration


@dataclass
class DepSpec[T](IDepSpec[T]):

    proto: type[T]
    attr: str | None = None
    """ Attribute name to get after resolution. """
    key: str | None = None
    """ Key to index after resolution. """
    call_args: tuple | None = None
    """ Positional arguments to use on callable after resolution. """
    call_kwargs: tuple[tuple[str, object], ...] | None = None
    """ Keyword argument *pairs* to use on callable after resolution. """


@dataclass
class Registration[T](IRegistration):

    factory: Callable[..., T]
    """ Callable whose result in the service. """

    dep_specs: tuple[tuple[str, IDepSpec], ...]
    """ Tuple of name/spec pairs that must be resolved to pass to factory. """

    scope: ScopeType = "startup"
