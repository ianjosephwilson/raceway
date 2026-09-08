"""
@TODO: The Cabled/DepSpec redundancy is kind of growing, not sure if it matters.
Maybe they are really meant to be independent and will grow further apart?
"""

from annotationlib import Format, call_evaluate_function
from collections.abc import Callable
from dataclasses import dataclass, replace
from inspect import isclass
from typing import (
    get_origin,
    get_args,
    Annotated,
    get_type_hints,
    TypeAliasType,
    is_protocol,
)

from .exc import RacewayError
from .registration import DepSpec
from .protocols import IExtractor, IDepSpec


class ExtractionError(RacewayError):
    pass


@dataclass
class Cabled[S]:
    """
    Mark a dependency as "Cabled" to have it injected.
    """

    proto: type[S] | None = None
    """Protocol that should be used. If None then try to use type hint as protocol."""

    attr: str | None = None
    key: str | None = None
    call_args: tuple | None = None
    call_kwargs: tuple[tuple[str, object], ...] | None = None

    def to_dep_spec(self) -> IDepSpec:
        if self.proto is None:
            raise ExtractionError("Cannot generate DepSpec without protocol.")
        call_args = validate_call_args(self.call_args)
        call_kwargs = validate_call_kwargs(self.call_kwargs)
        return DepSpec(
            proto=self.proto,
            attr=self.attr,
            key=self.key,
            call_args=call_args,
            call_kwargs=call_kwargs,
        )


def validate_call_args(call_args) -> tuple | None:
    """
    Validate call args.

    @NOTE: This is only meant to be run at "startup" so it can be sloOOOow.

    Also this is mainly because this is so easier to paren-soup into a weird bug.
    """
    if call_args is not None and not isinstance(call_args, tuple):
        raise ExtractionError("Call args must be None|tuple")
    return call_args


def validate_call_kwargs(call_kwargs) -> tuple[tuple[str, object], ...] | None:
    """
    Validate call kwargs.

    @NOTE: This is only meant to be run at "startup" so it can be sloOOOow.

    Also this is mainly because this is so easier to paren-soup into a weird bug.
    """
    type_error_msg = "Call kwargs must be None|tuple[tuple[str, object], ...]."
    if call_kwargs is not None:
        if not isinstance(call_kwargs, tuple):
            raise ExtractionError(type_error_msg)
        for arg in call_kwargs:
            if (
                not isinstance(arg, tuple)
                or len(arg) != 2
                or not isinstance(arg[0], str)
            ):
                raise ExtractionError(
                    "Call kwargs must be None|tuple[tuple[str, object], ...]."
                )
    return call_kwargs


def default_can_resolve_without_spec(proto: object | type):
    return isinstance(proto, type) and is_protocol(proto)


def configure_extractor(
    can_resolve_without_spec: Callable[[object | type], bool] | None = None,
) -> IExtractor:
    if can_resolve_without_spec is None:
        can_resolve_without_spec = default_can_resolve_without_spec
    return Extractor(can_resolve_without_spec=can_resolve_without_spec)


@dataclass
class Extractor(IExtractor):
    """Extractor dependency specs from annotations."""

    can_resolve_without_spec: Callable[[object | type], bool] | None = None
    """ User could provide this as a factory kwargs during decoration. """

    def _can_resolve_without_spec(self, proto: object | type) -> bool:
        """We only resolve protocols "automatically" right now."""
        if self.can_resolve_without_spec is not None:
            return self.can_resolve_without_spec(proto)
        else:
            return isinstance(proto, type) and is_protocol(proto)  # for pyright

    def extract(
        self,
        service_factory: Callable,
    ) -> tuple[tuple[str, IDepSpec], ...]:
        """
        Extract any dependency specifications we find.
        """
        cables = []
        hints = get_type_hints(service_factory, include_extras=True)
        for k, hint in hints.items():

            # type MyCabledProto = Annotated[Proto, Cabled]
            if isinstance(hint, TypeAliasType):
                hint = call_evaluate_function(hint.evaluate_value, Format.VALUE)

            origin = get_origin(hint)
            if origin is Annotated:
                a_args = get_args(hint)
                proto = a_args[0]
                for a_arg in a_args[1:]:
                    spec: Cabled | None = None
                    if isinstance(a_arg, Cabled):
                        # ie. Annotated[Proto, Cabled(...)] or Annotated[Proto, Cabled()]
                        spec = a_arg
                    elif isclass(a_arg) and issubclass(a_arg, Cabled):
                        # ie. Annotated[Proto, Cabled]
                        spec = Cabled()

                    if spec is not None:
                        if spec.proto is None:
                            # Use hint type if spec does not define one.
                            spec = replace(spec, proto=proto)
                        cables.append((k, spec))
                    elif self._can_resolve_without_spec(proto):
                        cables.append((k, Cabled(proto=proto)))
            # @TODO: I don't think this check is completely accurate.
            else:
                proto = hint
                if proto and self._can_resolve_without_spec(proto):
                    cables.append((k, Cabled(proto=proto)))
        return tuple(
            (name, cable.to_dep_spec())
            for name, cable in cables
            if cable.proto is not None
        )
