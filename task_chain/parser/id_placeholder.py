"""temporaryily replace ids within tasks with a placeholder, so that the id can be mapped later"""
from pydantic import BaseModel



def mapping_schema(input_task, id_map: dict, key: str="id", id_schema: str = "000"):

    old_id = getattr(input_task, key)
    new_id = id_schema + str(len(id_map))
    setattr(input_task, key, new_id)
    id_map[new_id] = old_id
    return input_task, id_map


def replace_parent_ids(input_tasks: list[BaseModel]):
    id_map = {}
    transformed_tasks = []
    for task in input_tasks:
        task, id_map = mapping_schema(task, id_map, key="parent_id")
        transformed_tasks.append(task)
    return transformed_tasks, id_map


def return_parent_ids(transformed_tasks: list[BaseModel], id_map: dict):
    reparsed_tasks = []
    for task in transformed_tasks:
        task.parent_id = id_map[task.parent_id]
        reparsed_tasks.append(task)
    return reparsed_tasks
