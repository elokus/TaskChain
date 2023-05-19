from __future__ import annotations
import asyncio
from typing import Sequence, Tuple

from task_chain.schema import TaskType
from task_chain.task.task_node import Task
from task_chain.storage.storage_context import TaskContextStore
from task_chain.decompose.utilities import (
    break_down_project, aassign_agents_to_tasks, assign_agents_to_tasks
)
from task_chain.decompose.base import BaseTaskDecomposer


class SimpleProjectDecomposer(BaseTaskDecomposer):
    def __init__(
            self,
            storage_context: TaskContextStore = TaskContextStore(),
            agents: list[dict] = None,
    ):
        """Decomposes a project into tasks and stores them in the storage context."""
        super().__init__(storage_context, root_type=TaskType.PROJECT)
        self.agents = agents

    def assign_tasks(self, tasks: Sequence[Sequence[Task]], run_async: bool = True, verbose: bool = True) -> Sequence[Sequence[Task]]:
        if run_async:
            return asyncio.run(aassign_agents_to_tasks(tasks, self.agents, verbose=verbose))
        return assign_agents_to_tasks(tasks, self.agents, verbose=verbose)

    def create_tasks(
            self, objective: str, verbose: bool = True, run_async: bool = True
    ) -> Tuple[Task, Sequence[Task], Sequence[Sequence[Task]]]:
        """Create a task pipelines and sequence of subtasks from an input string.
        Update the relations of the tasks to reflect the project as the root.
        Attributes:
            objective: The objective of the project.
        """

        project, pipelines, tasks = break_down_project(objective, verbose=verbose, run_async=run_async)

        if self.agents:
            tasks = self.assign_tasks(tasks, run_async=run_async)

        return self.store_tasks(project, pipelines, tasks)

    def store_tasks(
            self,
            project: Task,
            pipelines: Sequence[Task],
            tasks: Sequence[Sequence[Task]]
    ) -> Tuple[Task, Sequence[Task], Sequence[Sequence[Task]]]:
        """populate decomposed project into storage_context"""
        try:
            self.storage_context.add_tasks(project, pipelines)
            for pipeline, pipeline_tasks in zip(pipelines, tasks):
                self.storage_context.add_tasks(pipeline, pipeline_tasks, insert_parent=False)
        except Exception as e:
            print(e)
        return project, pipelines, tasks
