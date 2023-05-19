from __future__ import annotations
import json
import os

from typing import Dict, Optional, Sequence

from task_chain.schema import TaskRelations, TaskStatus, TaskType
from task_chain.singleton import AbstractSingleton
from task_chain.storage.base import BaseTaskStore, BaseProjectBoard, BaseStore, BaseTaskNetwork
from task_chain.storage.network_graph import TaskGraph
from task_chain.task.task_node import Task
from task_chain.storage.task_store import TaskStore
from task_chain.storage.utilities.project_board_loader import load_project_board
from task_chain.task.utilities import update_relation


DEFAULT_PERSIST_FNAME = "taskstore.json"
DEFAULT_PERSIST_DIR = "./storage"
DEFAULT_PERSIST_PATH = os.path.join(DEFAULT_PERSIST_DIR, DEFAULT_PERSIST_FNAME)


class TaskContextStore(AbstractSingleton, BaseTaskStore):
    """Task store that uses a key-value store as backend, a task graph
    to store tasks and their relationships into a graph and a project board integration
    to mirror tasks to a project board.
    """

    def __init__(
            self,
            task_store: BaseStore = None,
            index_graph: BaseTaskNetwork = None,
            project_board: BaseProjectBoard = None
    ):
        """Initialize the task context storage.
        Attributes:
            task_store: Key-value store to store tasks.
            index_graph: Graph to store task relationships.
            project_board: Project board integration.
        """
        self.task_store: TaskStore = task_store or TaskStore()
        self.task_network: TaskGraph = index_graph or TaskGraph()
        self.project_board: Optional[BaseProjectBoard] = project_board

    # ===== Persistence =====

    def persist(self, persist_path: str = DEFAULT_PERSIST_PATH) -> None:
        """Persist the task store."""
        data = dict(
            task_store={k: v.dict() for k, v in self.task_store.get_all().items()},
            task_network=self.task_network.dict(),
            project_board={
                "type": self.project_board.type,
                "project_id": self.project_board.project_id} if self.project_board is not None else "None"
        )
        if not os.path.exists(os.path.dirname(persist_path)):
            print(f"Directory {os.path.dirname(persist_path)} does not exist.")
            # create directory
            os.makedirs(os.path.dirname(persist_path))
        # save to file
        with open(persist_path, "w") as f:
            json.dump(data, f)
        print(f"Persisted task store to {persist_path}")

    def load_from_file(self, filepath: str = DEFAULT_PERSIST_PATH):
        """Load the task store from file."""
        if not os.path.exists(filepath):
            print(f"File {filepath} does not exist.")
            return
        with open(filepath, "r") as f:
            data = json.load(f)
        self.task_store.load(data["task_store"])
        self.task_network.load(data["task_network"])
        if data["project_board"] != "None":
            self.project_board = load_project_board(data["project_board"])

    # ===== Main interface =====
    @property
    def tasks(self) -> Dict[str, Task]:
        return self.task_store.get_all()

    def add_tasks(
            self,
            parent: Task,
            tasks: Sequence[Task],
            insert_parent: bool = True
    ):
        """Add a sequence of tasks with a parent task to the store."""
        if insert_parent:
            self.task_store.put(parent.id, parent.dict())
            self.task_network.insert(parent)
            if self.project_board is not None:
                self.project_board.add_task(parent)
        for task in tasks:
            self.task_store.put(task.id, task.dict())
            self.task_network.insert_under_parent(task, parent)
            if self.project_board is not None:
                self.project_board.add_task(task)

    def add_task(
            self, task: Task
    ) -> None:
        """Add a task to the store."""
        self.task_store.put(task.id, task.dict())
        self.task_network.insert(task)
        if self.project_board:
            self.project_board.add_task(task)

    # TODO: check if task relations have changed and update graph accordingly
    def update_task(self, task: Task) -> None:
        """update task in task_store and project_board."""
        self.task_store.put(task.id, task.dict())

        if task.status == TaskStatus.ISSUE:
            self.task_network.insert_under_issue(task)

        if self.project_board is not None:
            self.project_board.update_task(task)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task from the store."""
        return self.task_store.get_task(task_id)

    def get_tasks(self, task_ids: Sequence[str]) -> Sequence[Task]:
        """Get a sequence of tasks from the store."""
        return [self.get_task(task_id) for task_id in task_ids]

    def delete_task(self, task_id: str, raise_error: bool = True) -> None:
        """Delete a task from the store."""
        task = self.task_store.get_task(task_id)
        if task.prev_id is not None:
            prev_task = self.task_store.get_task(task.prev_id)
            prev_task = update_relation(
                prev_task,
                key=TaskRelations.NEXT,
                value=task.next_id
            )
            self.task_store.put(prev_task.id, prev_task.dict())
        if task.next_id is not None:
            next_task = self.task_store.get_task(task.next_id)
            next_task = update_relation(
                next_task,
                key=TaskRelations.PREV,
                value=task.prev_id
            )
            self.task_store.put(next_task.id, next_task.dict())

        self.task_store.delete_task(task.id)
        self.task_network.delete_task(task)
        if self.project_board is not None:
            self.project_board.delete_task(task)

    def task_exists(self, task_id: str) -> bool:
        return self.tasks.get(task_id) is not None

    def repr_current_context(self, task_id):
        str_tree = self.task_network.print_list_tree_from(task_id)
        for task_id in self.task_network.all_tasks.values():
            str_tree = str_tree.replace(task_id, self.task_store.get_task(task_id).name)
        return str_tree

    def repr_tree(self):
        str_tree = self.task_network.print_list_tree()
        for task_id in self.task_network.all_tasks.values():
            str_tree = str_tree.replace(task_id, self.task_store.get_task(task_id).name)
        return str_tree

    @property
    def root_id(self) -> str:
        if len(self.task_network.root_tasks) > 1:
            raise ValueError("More than one root task found.")

        return list(self.task_network.root_tasks.values())[0]

    @property
    def root_ids(self) -> list[str]:
        return list(self.task_network.root_tasks.values())

    def get_children(self, task_id: str) -> list[Task]:
        return [self.get_task(child_id) for child_id in self.task_network.get_children(task_id)]

    @property
    def issue_tasks(self):
        return [task for task in self.task_store.get_all().values() if task.type == TaskType.ISSUE]


