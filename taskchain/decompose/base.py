from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Sequence

from taskchain.schema import TaskType
from taskchain.storage.storage_context import TaskContextStore
from taskchain.task.task_node import Task


class BaseTaskDecomposer(ABC):

    def __init__(
            self,
            storage_context: TaskContextStore,
            root_type: TaskType,
            agents: list[dict] = None,
    ):
        """Base Class for decompose an objective into tasks and subtasks.
        Attributes:
            objective: the initial objective or problem description
            storage_context: TaskContextStore creates graph, storage and optional mirrors task to a Project Board
            root_type: one of Project, Pipeline, Task or Subtask
        """
        self.storage_context = storage_context
        self.root_type = root_type
        self.agents = agents

    @abstractmethod
    def create_tasks(self, objective: str, verbose: bool = True, run_async: bool = True):
        """Breaks down the objective into tasks and stores them in the storage context."""
        ...


    @abstractmethod
    def assign_tasks(
            self,
            tasks: Sequence[Sequence[Task]],
            run_async: bool = True,
            verbose: bool = True) -> Sequence[Sequence[Task]]:
        """Assigns agents to tasks."""
        ...

    @abstractmethod
    def store_tasks(self, *args, **kwargs):
        """Stores decomposed tasks into storage_context object"""
        ...

