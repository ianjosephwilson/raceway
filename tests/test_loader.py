from dataclasses import dataclass
import re
from typing import Protocol

import pytest

from raceway.loader import (
    configure_loader,
    feed_loader,
    configure_as_service,
)
from raceway.extractor import configure_extractor
from raceway.planner import configure_planner
from raceway.starter import startup
from raceway.protocols import ITask
from raceway.loader import LoaderError


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


@pytest.fixture
def custom_feed_maker():
    CUSTOM_CATEGORY = "custom_category"

    def _attach(service_factory, callback, category=None):
        assert category == CUSTOM_CATEGORY, "Make sure this comes through."
        service_factory.__raceway_cb__ = callback

    def _feed_maker(proto_factory_pairs, scope):
        def feed():
            """
            Simulate a custom feed function:
            -   manually attach a single callback to a fixed class attribute
            -   immediately run that callback
            -   cleanup the class attribute (@NOTE: This could affect other tests!!!)
            """
            for proto, factory in proto_factory_pairs:
                # Execute the decorator as if it was applied with @.
                configure_as_service(
                    proto, attach=_attach, scope=scope, category=CUSTOM_CATEGORY
                )(factory)
                # Immdiately execute the callback as if it was scanned.
                factory.__raceway_cb__(None, None, None)
                del factory.__raceway_cb__

        return feed

    return _feed_maker


@pytest.fixture
def custom_loader_api():
    extractor = configure_extractor()
    planner = configure_planner(task_proto=ITask, extractor_api=extractor)
    return configure_loader(planner=planner)


def test_feed_loader_callback(custom_loader_api, custom_feed_maker):
    """
    Closer to a full run of the loader.

    - setup all the loader "stuff"
    - get feeding...
    - make a container
    - add 2 integers and check the answer!!!
    """
    feed = custom_feed_maker(
        [(IMath, MathService), (ICalculator, CalculatorService)], scope="startup"
    )
    feed_loader(custom_loader_api, feed)
    container = startup(planner=custom_loader_api.get_planner())
    calculator_api = container.find_service(ICalculator)
    # Hoping for a miracle here
    assert calculator_api.add(1, 1) == 2


def test_feed_loader_callback_error(custom_loader_api, custom_feed_maker):
    feed = custom_feed_maker(
        [(IMath, MathService), (ICalculator, CalculatorService)], scope="startup"
    )
    with pytest.raises(
        LoaderError, match=re.compile(".* context variable must be set")
    ):
        feed()
