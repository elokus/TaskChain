"""Configuration class to store the state of bools for different scripts access."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Union

import yaml
from dotenv import load_dotenv

from taskchain.singleton import Singleton
from taskchain.utilities import find_file_in_parents, find_root_dir

load_dotenv(verbose=True, override=True)


class Config(metaclass=Singleton):
    """Configuration class to store the state of bools for different scripts access.
    """

    def __init__(self) -> None:
        """Initialize the Config class"""
        filename = find_file_in_parents("config.yaml")
        with open(filename) as f:
            self.config_file = yaml.load(f, Loader=yaml.FullLoader)

        self.project_run_name = self.getenv("PROJECT_RUN_NAME", "Project AGI - " + datetime.now().strftime("%d%m%y_%H%M"))

        self.debug_mode = self.getenv("DEBUG_MODE", "True")
        self.local_storage_dir = self.getenv("LOCAL_STORAGE_DIR", "storage")
        self.local_memory_dir = self.getenv("LOCAL_MEMORY_DIR", "memory")
        self.get_local_dirs()
        self.file_creation_dir = self.local_storage_dir + "/generated"

        self.local_index_name = self.getenv("LOCAL_INDEX_NAME")
        self.trello_board_name = self.getenv("TRELLO_BOARD_NAME", "Project AGI")
        self.trello_board_id = self.getenv("TRELLO_BOARD_ID", None)
        self.trello_labels = self.getenv(
            "TRELLO_LABELS", {
                "open": "blue",
                "depends": "yellow",
                "approval": "orange",
                "done": "green",
                "closed": "green",
                "blocked": "red",
                "approved": "purple",
                "issue": "red",
            }
        )
        self.github_api_key = self.getenv("GITHUB_API_KEY")
        self.github_username = self.getenv("GITHUB_USERNAME")
        self.fast_llm_model = self.getenv("FAST_LLM_MODEL", "gpt-3.5-turbo")
        self.slow_llm_model = self.getenv("SLOW_LLM_MODEL", "gpt-4")

    def get_local_dirs(self):
        """Get root storage dir and logging dir in root path.
        For execution from different paths, this is needed to ensure
        that the local storage and memory dirs are always in the same place.
        """
        if self.local_storage_dir is None:
            storage_dir_name = self.getenv("LOCAL_STORAGE_DIR_NAME", "storage")
            storage_dir = os.path.join(find_root_dir(), storage_dir_name)
            if not os.path.exists(storage_dir):
                os.makedirs(storage_dir)
            self.set_local_memory_dir(os.path.abspath(storage_dir))

        if self.local_memory_dir is None:
            local_memory_dir_name = self.getenv("LOCAL_MEMORY_DIR_NAME", "memory")
            log_dir = os.path.join(find_root_dir(), local_memory_dir_name)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            self.set_local_memory_dir(os.path.abspath(log_dir))

    def getenv(self, key: str, default: Union[str, dict] = None) -> Union[str, int, float, bool, dict]:
        """Get an environment variable."""
        value = self.config_file.get(key, default)
        if value:
            return value
        value = os.getenv(key, default)
        if value == "True":
            return True
        if value == "False":
            return False
        return value

    def set_local_memory_dir(self, value: str) -> None:
        """Set the local memory directory value."""
        self.local_memory_dir = value

    def set_local_storage_dir(self, value: str) -> None:
        """Set the local memory directory value."""
        self.local_storage_dir = value

