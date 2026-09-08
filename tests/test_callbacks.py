from dataclasses import dataclass
from typing import Protocol

from raceway.callbacks import (
    configure_loader,
    feed_loader,
    configure_as_service,
    LoaderCtx,
)
from raceway.extractor import configure_extractor
from raceway.planner import configure_planner
from raceway.starter import Starter


def test_feed_loader_with_mock():
    """
    Simulate feed_loader but with a noop

    @TODO: We might just remove this test eventually. I think its redundant.
    """

    extractor = configure_extractor()
    planner = configure_planner()
    loader = configure_loader(planner=planner, extractor=extractor)
    status = {"fed": False}

    def feed():
        # Noop that just checks we got the right thing and then actually ran.
        status["fed"] = True
        assert LoaderCtx.get() == loader

    feed_loader(loader, feed)
    assert status["fed"]


class IMath(Protocol):
    def add(self, a: int, b: int) -> int: ...


class ICalculator(Protocol):
    def add(self, a: int, b: int) -> int: ...


@dataclass
class MathService(IMath):

    def add(self, a: int, b: int) -> int:
        return a + b


@dataclass
class CalculatorService(ICalculator):

    math_api: IMath

    def add(self, a: int, b: int) -> int:
        return self.math_api.add(a, b)


def test_feed_loader_callback():
    """
    Closer to a full run of the loader.

    - setup all the loader "stuff"
    - get feeding...
    -   manually attach a single callback to a fixed class attribute
    -   immediately run that callback
    -   cleanup the class attribute (@NOTE: This could affect other tests!!!)
    - make a container
    - add 2 integers and check the answer!!!
    """
    extractor = configure_extractor()
    planner = configure_planner()
    loader = configure_loader(planner=planner, extractor=extractor)

    def our_attach(service_factory, callback, category=None):
        service_factory.__raceway_cb__ = callback

    def feed():
        for iface, cls in [(IMath, MathService), (ICalculator, CalculatorService)]:
            # Execute the decorator as if it was applied with @.
            configure_as_service(iface, attach=our_attach, scope="startup")(cls)
            # Immdiately execute the callback as if it was scanned.
            cls.__raceway_cb__(None, None, None)
            del cls.__raceway_cb__

    feed_loader(loader, feed)
    container = Starter().start(planner=planner)
    calculator_api = container.find_service(ICalculator)
    # Hoping for a miracle here
    assert calculator_api.add(1, 1) == 2
