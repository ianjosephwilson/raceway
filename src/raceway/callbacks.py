"""
This module provides decorators that attach callbacks that venusian can find.
"""

from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, is_dataclass
from inspect import isclass
from typing import cast

from .exc import RacewayError
from .protocols import ILoader, IPlanner, IExtractor, ScopeType
from .registration import Registration

DEFAULT_CATEGORY = "raceway.service"


# @TODO: Make sure this the latest and greatest pattern for doing this.
# We don't want to raise unless someone tries to use the actual
# decorators without another attach.
try:
    import venusian

    venusian_attach = venusian.attach
except ImportError:
    venusian_attach = None


LoaderCtx: ContextVar[ILoader | None] = ContextVar("LoaderCtx")
"""ContextVar that holds the loader during scanning for callbacks."""


class CallbackError(RacewayError):
    pass


@dataclass
class Loader(ILoader):
    planner: IPlanner
    extractor: IExtractor


def configure_loader(planner: IPlanner, extractor: IExtractor) -> ILoader:
    return Loader(planner=planner, extractor=extractor)


def feed_loader(
    loader: ILoader,
    feed: Callable[[], None],
    cv: ContextVar[ILoader | None] = LoaderCtx,
):
    """Setup the loader context and then call feed."""
    with cv.set(loader):
        feed()


def configure_as_service(
    proto: object | None = None,
    cv: ContextVar[ILoader | None] = LoaderCtx,
    attach: Callable | None = venusian_attach,
    scope: ScopeType = "task",
    wrap_in_dataclass: bool = True,
    category: str = DEFAULT_CATEGORY,
) -> Callable:
    """
    Decorate a service factory with a callback that can be executed to feed
    its registration to a loader.

    @NOTE: The `cv` must be set with a loader during callback's execution. This
    can be done by passing a `feed()` function into `feed_loader` along with
    a configured loader.
    """
    if attach is None:
        raise CallbackError("Venusian must be installed to use callbacks.")

    def wrapper(service_factory):
        # Use the service factory as the registration proto
        # if there is no proto
        if proto is None:
            register_proto = service_factory
        else:
            register_proto = proto
        # Wrap the service class in a dataclass here in case it is needed
        # at anypoint in the future.  This is almost just for convenience
        # and maybe it should be moved to an extended decorator.
        if (
            wrap_in_dataclass
            and isclass(service_factory)
            and not is_dataclass(service_factory)
        ):
            service_factory = dataclass(service_factory)

        def callback(*_):
            """Callback for venusian scan."""
            loader = cv.get()
            if loader is None:
                raise CallbackError(
                    f"{cv} context variable must be set when callback fires."
                )
            dep_specs = loader.extractor.extract(service_factory)
            loader.planner.queue_registration(
                register_proto, Registration(service_factory, dep_specs, scope=scope)
            )

        attach(service_factory, callback, category=category)
        return service_factory

    return wrapper
