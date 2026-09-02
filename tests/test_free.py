"""
Setup a simple task run to see if this thing works at all.
"""
from contextvars import ContextVar
from dataclasses import dataclass
import gc
from typing import Protocol

from raceway.starter import Starter
from raceway.planner import Planner
from raceway.registration import Registration, DepSpec


#
# Interfaces.
#
class ITask(Protocol):
    def get_job_id(self) -> int: ...
class IStrategy(Protocol):
    def calculate(self) -> int: ...
class IConfig(Protocol):
    def get_multiplier(self) -> int: ...
class ITaskRunner(Protocol):
    def run(self) -> int: ...
#
# Services.
#
@dataclass
class TaskRunner(ITaskRunner):
    strategy_api: IStrategy
    config_api: IConfig
    def run(self):
        return self.strategy_api.calculate(self.config_api.get_multiplier())

@dataclass
class Strategy(IStrategy):
    # @NOTE: This is poor design but we do it to force this dep.
    task_api: ITask

    # @NOTE: This is also poor design, we should just depend on config.
    def calculate(self, multiplier: int) -> int:
        return self.task_api.get_job_id() * multiplier

@dataclass
class Config(IConfig):
    def get_multiplier(self) -> int:
        return 2

@dataclass
class Task(ITask):
    def __hash__(self):
        return id(self)
    def __eq__(self, other):
        return self is other

    def get_job_id(self) -> int:
        return id(self)



CurrentTask: ITask | None = ContextVar('CurrentTask', default=None)


def test_free():
    """ Simple recursive test, no concurrency at all. """
    def get_current_task() -> ITask:
        task = CurrentTask.get()
        if task is None:
            raise AssertionError('Task is not set!')
        return task

    planner = Planner(reg_queue={})
    planner.queue_registration(
        ITaskRunner,
        Registration(
            TaskRunner,
            (
                ('strategy_api', DepSpec(proto=IStrategy)),
                ('config_api', DepSpec(proto=IConfig)),
            ),
            scope='task',  # because we depend on something that needs task we must be on-task
        ),
    )
    planner.queue_registration(
        IStrategy,
        Registration(
            Strategy,
            (('task_api', DepSpec(proto=ITask)),),
            scope='task', # because we depend on task we must be on-task
        ),
    )
    planner.queue_registration(
        IConfig,
        Registration(
            Config,
            (),
            scope='startup', # we have no deps so we can be on-startup
        ),
    )
    planner.queue_registration(
        ITask,
        Registration(
            get_current_task,
            (),
            scope='task', # we ARE the task that is on-task
        ),
    )

    container = Starter().start(planner=planner)
    config = container.find_service(IConfig) # Save off to keep cached.
    results = [handle_task(container), handle_task(container), handle_task(container), handle_task(container)]
    gc.collect()
    print (f'{results=}')
    print (f'{container.cache=}')
    print (f'{([(k, list(v.items())) for k, v in container.cache.items()])=}')

    assert len(list(container.cache.items())) == 1, "Only startup cache should exist."
    assert len(list(list(container.cache.items())[0][1].items())) == 1, "Only config should be in it."
    assert config

def handle_task(container) -> int:
    with CurrentTask.set(Task()): # Set this for the duration
        runner = container.find_service(ITaskRunner, task=CurrentTask.get())
        return runner.run()
