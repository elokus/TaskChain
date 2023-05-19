from __future__ import annotations

import asyncio
from typing import Sequence, Tuple

from taskchain.decompose.base import BaseTaskDecomposer
from taskchain.decompose.utilities import (
    update_relation, break_down_objective, abreak_down_objective, aassign_agents_to_tasks, assign_agents_to_tasks
)
from taskchain.schema import TaskRelations, TaskType
from taskchain.storage.storage_context import TaskContextStore
from taskchain.task.task_node import Task


class SimplePipelineDecomposer(BaseTaskDecomposer):
    def __init__(
            self,
            storage_context: TaskContextStore,
            agents: list[dict] = None,
    ):
        super().__init__(storage_context, root_type=TaskType.PIPELINE, agents=agents)

    def create_tasks(self, objective: str, verbose: bool = True, run_async: bool = False) -> Tuple[Task, Sequence[Task]]:
        """Breaks down the objective into tasks and stores them in the storage context."""
        if run_async:
            parent, children = asyncio.run(abreak_down_objective(objective, parent_type=self.root_type, verbose=verbose))
        else:
            parent, children = break_down_objective(objective, parent_type=self.root_type, verbose=verbose)
        children = [update_relation(child, TaskRelations.ROOT, parent.id) for child in children]
        if self.agents:
            children = self.assign_tasks(children, run_async=run_async)

        return self.store_tasks(parent, children)

    def assign_tasks(
            self,
            tasks: Sequence[Task],
            run_async: bool = True,
            verbose: bool = True) -> Sequence[Task]:
        """Assigns agents to tasks."""
        if run_async:
            return asyncio.run(aassign_agents_to_tasks(tasks, self.agents, verbose=verbose))
        return assign_agents_to_tasks(tasks, self.agents, verbose=verbose)

    def store_tasks(self, parent, children) -> Tuple[Task, Sequence[Task]]:
        self.storage_context.add_tasks(parent, children)
        return parent, children