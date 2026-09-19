from dataclasses import dataclass

from .container import configure_container
from .protocols import IPlanner, IContainer, ITask


@dataclass
class StartupTask(ITask):
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


def startup(planner: IPlanner, warm: bool = False) -> IContainer:
    registry = planner.create_registry()
    task_proto = planner.get_task_proto()
    startup_task = StartupTask()
    container = configure_container(
        registry=registry, startup_task=startup_task, task_proto=task_proto
    )
    if warm:
        for entry in registry.get_entries_by_scope('startup'):
            _ = container.find_service(entry[0], task=None)
    return container
