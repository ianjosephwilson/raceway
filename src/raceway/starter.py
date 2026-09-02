from dataclasses import dataclass

from .container import configure_container
from .protocols import IPlanner, IStarter, IContainer


@dataclass
class StartupTask:
    """
    Special task to use to track objects cached from container startup until shutdown.
    """

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other


@dataclass
class Starter(IStarter):
    """
    Layers and layers and layers...
    """

    def start(self, planner: IPlanner) -> IContainer:
        registry = planner.create_registry()
        startup_task = StartupTask()
        return configure_container(registry=registry, startup_task=startup_task)

