"""Utilities for the json_fixes package."""
from __future__ import annotations
import re

from langchain.schema import BaseMessage
from pydantic import BaseModel
from typing import TypeVar, Type, Union

from task_chain.config import Config

CFG = Config()


def extract_char_position(error_message: str) -> int:
    """Extract the character position from the JSONDecodeError message.

    Args:
        error_message (str): The error message from the JSONDecodeError
          exception.

    Returns:
        int: The character position.
    """

    char_pattern = re.compile(r"\(char (\d+)\)")
    if match := char_pattern.search(error_message):
        return int(match[1])
    else:
        raise ValueError("Character position not found in the error message.")


def _get_descripition_from_definitions(d: dict, def_dict: dict):
    res = {}
    for k, v in d["properties"].items():
        if "allOf" in v:
            id = v["allOf"][0]["$ref"].split("/")[-1]
            _v = def_dict[id]
            res[k] = _get_descripition_from_definitions(_v, def_dict)
        elif "items" in v:
            if "$ref" not in v["items"]:
                res[k] = [v["description"]]
                continue
            id = v["items"]["$ref"].split("/")[-1]
            _v = def_dict[id]
            res[k] = [_get_descripition_from_definitions(_v, def_dict)]
        else:
            res[k]= v["description"]
    return res


def _get_description(d: dict):
    res = {}
    for k, v in d["properties"].items():
        if "allOf" in v:
            id = v["allOf"][0]["$ref"].split("/")[-1]
            def_dict = d["definitions"]
            _v = def_dict[id]
            res[k] = _get_descripition_from_definitions(_v, def_dict)
        elif "items" in v:
            if "$ref" not in v["items"]:
                res[k] = [v["description"]]
                continue
            id = v["items"]["$ref"].split("/")[-1]
            def_dict = d["definitions"]
            _v = def_dict[id]
            res[k] = [_get_descripition_from_definitions(_v, def_dict)]
        else:
            res[k]= v["description"]
    return res

def _get_indent(d: Union[dict, list], i: int=0) -> int:
    if isinstance(d, list):
        i += 1
        _i = []
        for v in d:
            if isinstance(v, dict):
                _i.append(_get_indent(v))
            elif isinstance(v, list):
                _i.append(_get_indent(v))
        if _i:
            i += max(_i)
    else:
        i += 1
        _i = []
        for k, v in d.items():
            if isinstance(v, dict):
                _i.append(_get_indent(v))
            elif isinstance(v, list):
                _i.append(_get_indent(v))
        if _i:
            i += max(_i)
    return i


T = TypeVar("T", bound=BaseModel)

def _get_short_schema(model: Type[T]) -> dict:
    return _get_description(model.schema())

def get_short_schema(model: Type[T]) -> str:
    import json
    schema = _get_short_schema(model)
    return json.dumps(schema,indent=_get_indent(schema))

def indented_string(obj: Union[dict, list, str]) -> Union[str, list]:
    if isinstance(obj, str):
        return obj
    if isinstance(obj, list) and isinstance(obj[0], BaseMessage):
        return obj

    import json
    return json.dumps(obj, indent=_get_indent(obj))

def _is_item(d: dict, item_keys: Union[list, set]):
    if len(set(d.keys()).intersection(item_keys)) >= 2:
        return True

def _keys_to_list(d: dict) -> list:
    result = []
    for k, v in d.items():
        result.append(k)
        if isinstance(v, dict):
            for key, value in v.items():
                result.append(key)
                if isinstance(value, dict):
                    result.extend(_keys_to_list(value))
    return result

def _get_nesting_item_keys(
        dict_object: dict,
        item_keys: set={"name", "description", "agent", "output", "input"},
        ) -> dict:
    nested_keys = {}
    for key, value in dict_object.items():
        if isinstance(value, dict):
            if _is_item(value, item_keys):
                nested_keys[key] = _get_nesting_item_keys(value, item_keys)
        if isinstance(value, list):
            _nested_list_keys = []
            for v in value:
                if isinstance(v, dict):
                    if _is_item(v, item_keys):
                        _nested_list_keys.append(_get_nesting_item_keys(v, item_keys))
            if _nested_list_keys:
                _nested_list_keys = list(_nested_list_keys)
                _nested_list_keys = [(item, _get_indent(item)) for item in _nested_list_keys]
                max_indent_keys = [item[0] for item in _nested_list_keys if item[1] == max(_nested_list_keys, key=lambda x: x[1])[1]]
                nested_keys[key] = max_indent_keys[0]
    return nested_keys

def get_nested_keys(dict_object: dict, item_keys: set={"name", "description", "agent", "output", "input"}) -> list:
    nested_keys = _get_nesting_item_keys(dict_object, item_keys)
    return _keys_to_list(nested_keys)


def format_nested_list(nested_list, indent=0, numeration=False, bullet=False):
    formatted_str = ""
    count = 1
    for item in nested_list:
        if isinstance(item, dict):
            formatted_str += format_nested_dict(item, indent, numeration, bullet)
        elif isinstance(item, list):
            formatted_str += format_nested_list(item, indent, numeration, bullet)
        else:
            prefix = f"{count}. " if numeration else ""
            bullet_str = "- " if bullet else ""
            formatted_str += " " * indent + bullet_str + prefix + str(item) + "\n"
            count += 1
    return formatted_str


def format_nested_dict(nested_dict, indent=0, numeration=False, bullet=False):
    formatted_str = ""
    for key, value in nested_dict.items():
        if key in ["name", "pipeline"]:
            bullet_str = "- " if indent < 8 else ""
            formatted_str += " " * indent + bullet_str + str(value) + "\n"
        else:
            formatted_str += " " * indent + key.capitalize() + ": "
            if isinstance(value, list):
                formatted_str += ", ".join([str(item) for item in value]) + "\n"
            elif isinstance(value, dict):
                formatted_str += "\n" + format_nested_dict(value, indent + 4)
            else:
                formatted_str += str(value) + "\n"
            if key == "pipeline_tasks":
                formatted_str += format_nested_list(value, indent + 4, numeration=True, bullet=indent < 8)
    return formatted_str
#

def validate_id(id):
    import uuid
    try:
        uuid.UUID(id)
    except:
        raise ValueError("Invalid id")




