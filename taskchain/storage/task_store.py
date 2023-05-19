"""Singleton class for storing task_ids and task nodes."""
from __future__ import annotations

import json
import os
from typing import Optional, Dict

from taskchain.agents.base import logger
from taskchain.storage.base import BaseStore
from taskchain.task.task_node import Task

DEFAULT_PERSIST_FNAME = "taskstore.json"
DEFAULT_PERSIST_DIR = "./storage"
DEFAULT_PERSIST_PATH = os.path.join(DEFAULT_PERSIST_DIR, DEFAULT_PERSIST_FNAME)


VALUE_TYPE = Dict[str, Dict[str, any]]


class TaskStore(BaseStore):
    """Simple key-value store as singleton instance."""

    def __init__(
            self,
            data : VALUE_TYPE = None
    ):
        self._data: VALUE_TYPE = data or {}

    def load(self, data: dict) -> None:
        self._data = data

    def put(self, key: str, value: dict):
        self._data[key] = value

    def get(self, key: str) -> Optional[dict]:
        data = self._data.get(key, None)
        if data is None:
            return None
        return data.copy()

    def get_task(self, key: str) -> Optional[Task]:
        if key is None:
            return None

        data = self._data.get(key, None)
        if data is None:
            return None

        data = data.copy()
        return Task(**data)

    def get_all(self) -> Dict[str, Task]:
        data = self._data
        data = data.copy()
        return {key: Task(**value) for key, value in data.items()}

    def delete_task(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    def persist(self, persist_path: str) -> None:
        """Persist the store."""
        dirpath = os.path.dirname(persist_path)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        with open(persist_path, "w+") as f:
            json.dump(self._data, f)

    @classmethod
    def from_persist_path(cls, persist_path: str) -> "TaskStore":
        """Load a SimpleKVStore from a persist path."""
        if not os.path.exists(persist_path):
            raise ValueError(f"No existing {__name__} found at {persist_path}.")

        logger.debug(f"Loading {__name__} from {persist_path}.")
        with open(persist_path, "r+") as f:
            data = json.load(f)
        return cls(data)

    def to_dict(self) -> dict:
        """Save the store as dict."""
        return self._data

    @classmethod
    def from_dict(cls, save_dict: dict) -> "TaskStore":
        """Load a SimpleKVStore from dict."""
        return cls(save_dict)

