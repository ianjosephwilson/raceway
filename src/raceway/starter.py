from dataclasses import dataclass

from .container import configure_container
from .protocols import IPlanner, IStarter, IContainer


@dataclass
class StartupTask:
    """
    Special task to use to track objects cached from container startup until shutdown.
    """

    def __hash__(self):
        # @NOTE: This hash must be compatible with whatever else is being put
        # into the cache.
        return id(self)

    def __eq__(self, other):
        # @NOTE: As with __hash__, this must also be compatible with whatever
        # else is in the cache.
        return self is other


@dataclass
class Starter(IStarter):
    """
    Layers and layers and layers...
    """

    def start(self, planner: IPlanner) -> IContainer:
        registry = planner.create_registry()
        task_proto = planner.get_task_proto()
        startup_task = StartupTask()
        return configure_container(
            registry=registry,
            startup_task=startup_task,
            task_proto=task_proto)
