import os
from abc import ABC, abstractmethod
from typing import Dict, Optional, Sequence, Union

from pydantic import BaseModel, Field

from taskchain.task.task_node import Task

DEFAULT_PERSIST_FNAME = "taskstore.json"
DEFAULT_PERSIST_DIR = "./storage"
DEFAULT_PERSIST_PATH = os.path.join(DEFAULT_PERSIST_DIR, DEFAULT_PERSIST_FNAME)


class BaseStore(ABC):
    """Base key-value store."""

    @abstractmethod
    def load(self, data: dict) -> None:
        pass

    @abstractmethod
    def put(self, key: str, value: dict):
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[dict]:
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, dict]:
        pass


class BaseTaskNetwork(BaseModel, ABC):
    all_tasks: dict[int, str] = Field(default_factory=dict)
    root_tasks: dict[int, str] = Field(default_factory=dict)
    id_to_children: dict[str, list[str]] = Field(default_factory=dict)
    issue_to_id: dict[str, str] = Field(default_factory=dict)

    @abstractmethod
    def load(self, data: dict):
        pass

    @abstractmethod
    def get_index(self, task: Task):
        pass

    @abstractmethod
    def insert(
            self,
            task: Task,
            parent: Optional[Union[Task, str]] = None,
            children: Optional[Sequence[Union[Task, str]]] = None
    ):
        pass

    @abstractmethod
    def insert_under_issue(
            self,
            task: Task
    ):
        pass

    @abstractmethod
    def insert_under_parent(
            self,
            task: Task,
            parent: Union[Task, str, None],
            children: Optional[Sequence[Union[Task, str]]] = None
    ):
        pass

    @abstractmethod
    def get_children(self, parent: Optional[Union[Task, str]]) -> list[str]:
        pass

    @abstractmethod
    def get_all_children(self, parent: Optional[Union[Task, str]]) -> list[str]:
        pass

    @abstractmethod
    def delete_task(self, task: Task):
        pass

    @abstractmethod
    def formatted_tree_view(self, task_id: str = None) -> str:
        pass


class BaseProjectBoard(ABC):
    """Base project board."""

    def __init__(self, project_id: str):
        self.project_id = project_id

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get_card(self, id: str):
        pass

    @abstractmethod
    def add_task(self, task: Task):
        pass

    @abstractmethod
    def close_task(self, task: Task):
        pass

    @abstractmethod
    def update_task(self, task: Task, **kwargs):
        pass

    @abstractmethod
    def delete_task(self, task: Task):
        pass

    @abstractmethod
    def set_status(self, task: Task, status: str):
        pass

    @abstractmethod
    def get_status(self, task: Task):
        pass

    @abstractmethod
    def add_comment(self, task: Task, comment: str):
        pass

    @abstractmethod
    def get_comments(self, task: Task):
        pass

    @abstractmethod
    def type(self) -> str:
        ...


class BaseTaskStore(ABC):
    """Base task store."""
    task_store: BaseStore
    task_network: BaseTaskNetwork

    # ===== Save/load =====
    def persist(self, persist_path: str = DEFAULT_PERSIST_PATH) -> None:
        pass

    # ===== Main interface =====
    @property
    @abstractmethod
    def tasks(self) -> Dict[str, Task]:
        ...

    @abstractmethod
    def add_task(
            self, docs: Sequence[Task]
    ) -> None:
        ...

    @abstractmethod
    def get_task(
            self, task_id: str) -> Optional[Task]:
        ...

    @abstractmethod
    def get_tasks(
            self, task_ids: Sequence[str]) -> Dict[str, Task]:
        ...

    @abstractmethod
    def delete_task(self, task_id: str, raise_error: bool = True) -> None:
        """Delete a task from the store."""
        ...

    @abstractmethod
    def task_exists(self, task_id: str) -> bool:
        ...
