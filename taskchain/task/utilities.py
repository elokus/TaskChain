from __future__ import annotations

from typing import Sequence

from taskchain.schema import TaskType, TaskRelations
from taskchain.schema.base import Issue
from taskchain.storage.base import BaseTaskStore
from taskchain.task.task_node import Task


def generate_issue_task(issue: Issue, ref_task: Task) -> Task:
    """Generates a task from a reported issue."""
    return Task(
        name=f"[ISSUE]: {issue.type} in task {ref_task.name}",
        description=str(issue),
        task_type=TaskType.ISSUE,
        relations={TaskRelations.PARENT: ref_task.id},
    )


def get_branch_tasks_by_id(task_id: str, task_storage: BaseTaskStore) -> Sequence[Task]:
    """Get the Task object and its child tasks by a given id.
    Attributes:
        task_id: The id of the task.
        task_storage: The task storage context.
    Returns:
        Sequence[Task]: The task and its child tasks.
    """
    task = task_storage.get_task(task_id)
    branch = [task]
    branch.extend(get_child_tasks(task, task_storage))
    return branch


def get_child_tasks(task: Task, task_storage: BaseTaskStore) -> Sequence[Task]:
    """Gets the child tasks of a task."""
    child_ids = task_storage.task_network.id_to_children[task.id]
    return [task_storage.get_task(child_id) for child_id in child_ids]


def filter_tasks_by_inputs(tasks: Sequence[Task], input_keys: Sequence[str]) -> Sequence[Task]:
    """Filters tasks by their input names."""
    filtered_tasks = []
    for task in tasks:
        req_inputs = set(task.inputs)
        difference = req_inputs.difference(set(input_keys))
        if len(difference) == 0:
            filtered_tasks.append(task)
    return filtered_tasks



def update_relations(tasks: Sequence[Task], **kwargs) -> Sequence[Task]:
    """Update relations for a sequence of tasks."""
    updated_tasks = []
    for key, value in kwargs.items():
        key: TaskRelations
        for task in tasks:
            task.relations[key] = value
            updated_tasks.append(task)

    return updated_tasks


def update_relation(task: Task, key: TaskRelations, value: str) -> Task:
    """Update a relation for a task."""
    task.relations[key] = value
    return task
