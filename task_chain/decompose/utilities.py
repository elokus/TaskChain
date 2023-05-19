from __future__ import annotations
import asyncio
from typing import Sequence, Tuple, Optional, Union

from task_chain.chains.loader import load_chain
from task_chain.parser.string_formatter import format_nested_object
from task_chain.schema.types import PromptTypes
from task_chain.schema.output_model import PredictChoice
from task_chain.schema import TaskType, TaskRelations
from task_chain.task.task_node import Task
from task_chain.task.utilities import update_relation

CHILD_TASK_TYPE = {
    TaskType.PROJECT: TaskType.PIPELINE,
    TaskType.PIPELINE: TaskType.TASK,
    TaskType.TASK: TaskType.SUBTASK
}



def _assign_agents_to_tasks(task: Task, agents: list[dict], verbose: bool = False) -> Task:
    """Assign agents to tasks."""
    numbered_list = []
    for i, agent in enumerate(agents):
        numbered_list.append(f"{i+1}. Name: {agent['name']}, Description: {agent['description']}")
    numbered_list = "\n".join(numbered_list)
    chain = load_chain(PromptTypes.ASSIGN_TASK, verbose=verbose)
    context = f"TASK:\n{task.get_summary(indent=4)}\n\nAGENTS:\n{numbered_list}"
    choice: PredictChoice = chain.predict_and_parse(context=context, remarks="Begin!")
    agent = agents[int(choice.choice) - 1]
    task = update_relation(task, TaskRelations.AGENT, agent["name"])
    return task

#TODO: add verbose to execution chain
async def _aassign_agents_to_tasks(task: Task, agents: list[dict], verbose: bool = False) -> Task:
    """Assign agents to tasks Async."""
    numbered_list = []
    for i, agent in enumerate(agents):
        numbered_list.append(f"{i+1}. Name: {agent['name']}, Description: {agent['description']}")
    numbered_list = "\n".join(numbered_list)
    chain = load_chain(PromptTypes.ASSIGN_TASK, verbose=verbose)
    context = f"TASK:\n{task.get_summary(indent=4)}\n\nAGENTS:\n{numbered_list}"
    choice: PredictChoice = await chain.apredict_and_parse(context=context, remarks="Begin!")
    agent = agents[int(choice.choice) - 1]
    task = update_relation(task, TaskRelations.AGENT, agent["name"])
    return task

#TODO: add verbose to execution chain
def assign_agents_to_tasks(
        tasks: Union[Sequence[Sequence[Task]],Sequence[Task]],
        agents: list[dict],
        verbose: bool=False
) -> Union[Sequence[Sequence[Task]],Sequence[Task]]:
    _tasks = []

    for pipeline_tasks in tasks:

        if isinstance(pipeline_tasks, Task):
            _tasks.append(_assign_agents_to_tasks(pipeline_tasks, agents, verbose=verbose))

        else:
            _pipeline_tasks = []
            for task in pipeline_tasks:
                task = _assign_agents_to_tasks(task, agents, verbose=verbose)
                _pipeline_tasks.append(task)
            _tasks.append(_pipeline_tasks)
    return _tasks

#TODO: add verbose to execution chain
async def aassign_agents_to_tasks(
        tasks: Union[Sequence[Sequence[Task]], Sequence[Task]],
        agents: list[dict],
        verbose: bool=False
) -> Union[Sequence[Sequence[Task]], Sequence[Task]]:

    if isinstance(tasks[0], Task):
        _tasks = await asyncio.gather(*[_aassign_agents_to_tasks(task, agents, verbose=verbose) for task in tasks])
        return _tasks
    seq_tasks = []
    for pipeline_tasks in tasks:
        _pipeline_tasks = []
        _inputs = [{"task": task, "agents": agents, "verbose": verbose} for task in pipeline_tasks]
        _tasks = await asyncio.gather(*[_aassign_agents_to_tasks(**_input) for _input in _inputs])
        seq_tasks.append(_tasks)
    return seq_tasks

def break_down_objective(
        objective: str,
        parent_task: Optional[Task] = None,
        parent_type: TaskType = TaskType.PIPELINE,
        child_type: TaskType = None,
        verbose: bool = False,
        is_chunk: bool = False,
) -> Tuple[Task, Sequence[Task]]:
    """Create a task and sequence of subtasks from an input string."""
    child_type = child_type or CHILD_TASK_TYPE[parent_type]

    remarks = "Begin!"
    if is_chunk:
        prompt_type = PromptTypes.BREAK_DOWN_CHUNK
    else:
        prompt_type = PromptTypes.BREAK_DOWN
    summary_chain = load_chain(prompt_type, suggest=False, verbose=verbose)
    summary = summary_chain.predict_and_parse(context=objective, remarks=remarks)

    extend_chain = load_chain(PromptTypes.EXTEND_LIST, verbose=verbose)
    children = extend_chain.predict_and_parse(context=summary, remarks=remarks)

    if not parent_task:
        parent_chain = load_chain(PromptTypes.PARENT_TASK, verbose=verbose)
        context = format_nested_object(children.dict())
        remarks = f"Known information about the parent task: {objective} \nBegin! "
        parent = parent_chain.predict_and_parse(context=context, remarks=remarks)
        parent_task = Task(**parent.dict(), summary=summary, type=parent_type)
    else:
        parent_task.summary = summary

    children = [Task(**child.dict(), type=child_type) for child in children.tasks]
    children_tasks = []

    for i, child in enumerate(children):
        next_task_id = children[i + 1].id if i + 1 < len(children) else None
        prev_task_id = children[i - 1].id if i - 1 >= 0 else None
        relations = {
            TaskRelations.PARENT: parent_task.id,
            TaskRelations.NEXT: next_task_id,
            TaskRelations.PREV: prev_task_id,
        }
        child.relations = relations

        children_tasks.append(child)
    return parent_task, children_tasks

async def abreak_down_objective(
        objective: str,
        parent_task: Optional[Task] = None,
        parent_type: TaskType = TaskType.PIPELINE,
        child_type: TaskType = None,
        is_chunk: bool = False,
        verbose: bool = True,

) -> Tuple[Task, Sequence[Task]]:
    """Create a task and sequence of subtasks from an input string."""
    child_type = child_type or CHILD_TASK_TYPE[parent_type]

    remarks = "Begin!"
    if is_chunk:
        prompt_type = PromptTypes.BREAK_DOWN_CHUNK
    else:
        prompt_type = PromptTypes.BREAK_DOWN
    summary_chain = load_chain(prompt_type, suggest=False, verbose=verbose)
    summary = await summary_chain.apredict_and_parse(context=objective, remarks=remarks)

    extend_chain = load_chain(PromptTypes.EXTEND_LIST, verbose=verbose)
    children = await extend_chain.apredict_and_parse(context=summary, remarks=remarks)
    print(children)

    if not parent_task:
        parent_chain = load_chain(PromptTypes.PARENT_TASK, verbose=verbose)
        context = format_nested_object(children.dict())
        remarks = f"Known information about the parent task: {objective} \nBegin! "
        parent = await parent_chain.apredict_and_parse(context=context, remarks=remarks)
        parent_task = Task(**parent.dict(), summary=summary, type=parent_type)
    else:
        parent_task.summary = summary

    children = [Task(**child.dict(), type=child_type) for child in children.tasks]
    children_tasks = []

    for i, child in enumerate(children):
        next_task_id = children[i + 1].id if i + 1 < len(children) else None
        prev_task_id = children[i - 1].id if i - 1 >= 0 else None
        relations = {
            TaskRelations.PARENT: parent_task.id,
            TaskRelations.NEXT: next_task_id,
            TaskRelations.PREV: prev_task_id,
        }
        child.relations = relations

        children_tasks.append(child)
    return parent_task, children_tasks


def break_down_task(task: Task, verbose: bool = False):
    """Create a task pipelines and sequence of subtasks from an input string."""
    task, subtasks = break_down_objective(
        task.get_summary(), parent_task=task, parent_type=task.type, verbose=verbose
    )
    return task, subtasks


def _prep_prevnext_context(task, task_dict: dict[str, Task]) -> str:
    """Prepare context object containing previous and next task information."""
    prev_task = task_dict.get(task.relations[TaskRelations.PREV], None)
    next_task = task_dict.get(task.relations[TaskRelations.NEXT], None)

    context = f"CURRENT TASK: {task.get_summary()}"
    context += f"\n - PREVIOUS TASK: {prev_task.get_summary()}" if prev_task else "No previous task."
    context += f"\n - NEXT TASK: {next_task.get_summary()}" if next_task else "No next task."
    return context


async def _abreak_down_pipelines(task_dict: dict[str, Task], verbose: bool = False):
    """Breakdown a pipeline with context of previous and next task"""
    input_list = []
    for task in task_dict.values():
        context = _prep_prevnext_context(task, task_dict)
        input_list.append({"objective": context, "parent_task":task, "parent_type": task.type, "verbose": verbose})

    seq_task_subtask = await asyncio.gather(*[abreak_down_objective(**input) for input in input_list])

    summaries = []
    tasks = []
    seq_subtasks = []
    for task, subtasks in seq_task_subtask:
        summary = _summary_from_breakdown(task, subtasks)
        task.summary = summary
        summaries.append(summary)
        tasks.append(task)

        subtasks = [update_relation(task, TaskRelations.ROOT, task.root_id) for task in subtasks]
        seq_subtasks.append(subtasks)

    return tasks, seq_subtasks, summaries


def _summary_from_breakdown(task: Task, subtasks: Sequence[Task]) -> str:
    """Create a summary from a task and its subtasks."""
    summary = f"{task.short_title}\n"
    for subtask in subtasks:
        summary += f" - {subtask.short_title}\n"
    return summary

def _break_down_pipelines(task_dict: dict[str, Task], verbose: bool = False):
    """Breakdown a pipeline with context from previous and next tasks."""

    summaries = []
    tasks = []
    seq_subtasks = []
    for task in task_dict.values():
        context = _prep_prevnext_context(task, task_dict)
        task, subtasks = break_down_objective(
            objective=context, parent_task=task, parent_type=task.type, verbose=verbose
        )
        summary = _summary_from_breakdown(task, subtasks)
        task.summary = summary
        summaries.append(summary)
        tasks.append(task)
        subtasks = [update_relation(task, TaskRelations.ROOT, task.root_id) for task in subtasks]
        seq_subtasks.append(subtasks)

    return tasks, seq_subtasks, summaries


def break_down_project(
        objective: str, run_async: bool = True, verbose: bool = True
) -> Tuple[Task, Sequence[Task], Sequence[Sequence[Task]]]:
    """Create a task pipelines and sequence of subtasks from an input string.
    Update the relations of the tasks to reflect the project as the root.
    Attributes:
        objective: The objective of the project.
    """
    project, pipelines = break_down_objective(objective, parent_type=TaskType.PROJECT, verbose=verbose)
    pipelines = [update_relation(pipeline, TaskRelations.ROOT, project.id) for pipeline in pipelines]
    pipeline_dict = {pipeline.id: pipeline for pipeline in pipelines}

    # break down pipelines into tasks
    if run_async:
        pipelines, tasks, summaries = asyncio.run(_abreak_down_pipelines(pipeline_dict, verbose=verbose))
    else:
        pipelines, tasks, summaries = _break_down_pipelines(pipeline_dict, verbose=verbose)
    seq_tasks = []
    for seq_task in tasks:
        _tasks = [update_relation(task, TaskRelations.ROOT, project.id) for task in seq_task]
        seq_tasks.append(_tasks)

    project.summary = "\n".join(summaries)
    return project, pipelines, tasks