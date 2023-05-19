from __future__ import annotations

import os
from typing import Union

from dotenv import load_dotenv


def _validate_dotenv(keys: Union[str, list]):

    for key in list(keys):
        if key not in os.environ:
            return False
    return True


def load_dotenv_from_parents(keys: Union[str, list], depth: int=4):
    """Search and Load dotenv from parents directories till keys are found in ENV_VARS.
    :param keys: The key or list of keys to validate env.
    :param depth: The depth to search for dotenv file.
    """
    keys = list(keys)
    env_path = ".env"
    if _validate_dotenv(keys):
        return

    for i in range(depth):

        load_dotenv(env_path)
        if _validate_dotenv(keys):
            break
        else:
            if i == depth - 1:
                raise EnvironmentError(f"Key(s): {keys} not found ")
            env_path = "../" + env_path
    return


def find_file_in_parents(filename: str, depth: int=4):

    """Search and Load dotenv from parents directories till keys are found in ENV_VARS.
    :param keys: The key or list of keys to validate env.
    :param depth: The depth to search for dotenv file.
    """
    if os.path.isfile(filename):
        return filename
    if os.path.isfile("./" + filename):
        return "./" + filename
    for i in range(depth):
        if os.path.isfile("../" + filename):
            return "../" + filename
        filename = "../" + filename
    raise FileNotFoundError(f"File: {filename} not found ")


def find_root_dir(search_file: str = "config.yaml", depth: int=4):
    """Search and Load dotenv from parents directories till keys are found in ENV_VARS.
    :param keys: The key or list of keys to validate env.
    :param depth: The depth to search for dotenv file.
    """
    root_path = ""
    if os.path.isfile(search_file):
        return root_path
    if os.path.isfile("./" + search_file):
        return "./"
    for i in range(depth):
        if os.path.isfile("../" + search_file):
            return "../" + root_path
        search_file = "../" + search_file
        root_path = "../" + root_path
    raise FileNotFoundError(f"File: {search_file} not found ")

def get_client_config(keys: Union[str, list], depth=4):
    """Search and Load dotenv from parents directories till keys are found in ENV_VARS.
    :param keys: The key or list of keys to validate env and return.
    :param depth: The depth to search for dotenv file.

    :return: dict of keys and values.
    """

    keys = list(keys)
    load_dotenv_from_parents(keys, depth)

    return {key: os.environ[key] for key in keys}


def get_trello_config():
    config_keys = [
        "TRELLO_KEY",
        "TRELLO_SECRET",
        "TRELLO_TOKEN",
    ]
    return get_client_config(config_keys, depth=3)


def get_trello_client():
    from trello import TrelloClient
    config = get_trello_config()
    return TrelloClient(
        api_key=config["TRELLO_KEY"],
        api_secret=config["TRELLO_SECRET"],
        token=config["TRELLO_TOKEN"]
    )

def google_organic_search(query: str) -> list[dict]:
    from langchain import SerpAPIWrapper
    load_dotenv_from_parents(["SERPAPI_API_KEY"])
    serp = SerpAPIWrapper()
    res = serp.results(query)
    return res["organic_results"]

def parse_list_in_json(o: dict, key: str):
    if "," in o[key]:
        o[key] = o[key].split(",")
    if isinstance(o[key], str):
        o[key] = [o[key]]
    return o


def _resolve_pathlike_command_args(self, command_args):
    if "directory" in command_args and command_args["directory"] in {"", "/"}:
        command_args["directory"] = str(self.workspace.root)
    else:
        for pathlike in ["filename", "directory", "clone_path"]:
            if pathlike in command_args:
                command_args[pathlike] = str(
                    self.workspace.get_path(command_args[pathlike])
                )
    return command_args

def get_default_issue_task() -> dict:
    return {
        "name": "Issues",
        "inputs": ["issue"],
        "outputs": ["issue"],
        "type": "issue",
        "status": "OPEN",
    }