from __future__ import annotations

from typing import Optional, Union, Any

from pydantic import Field

from taskchain.parser.string_formatter import format_nested_object
from taskchain.schema import TaskRelations
from taskchain.task.base import BaseTaskNode


class Task(BaseTaskNode):
    """A generic task node

    Attributes:
        name: The name of the task
        description: The description of the task
        inputs: The input(s) of the task
        outputs: The output(s) of the task
        relations: The relationship(s) of the task
    """
    summary: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    results: Optional[dict] = None
    relations: Optional[dict[TaskRelations, Any]] = Field(default_factory=dict)
    inputs: list = Field(
        description="List of input keys of the task",
        default_factory=list
    )
    outputs: list = Field(
        description="List of output keys of the task",
        default_factory=list)


    @property
    def parent_id(self):
        return self.relations.get(TaskRelations.PARENT, None)

    @property
    def root_id(self) -> Union[str, None]:
        return self.relations.get(TaskRelations.ROOT, None)

    #TODO raise errors for next and if not set to pass error message to agents
    @property
    def prev_id(self) -> Union[str, None]:
        return self.relations.get(TaskRelations.PREV, None)

    @property
    def next_id(self) -> Union[str, None]:
        return self.relations.get(TaskRelations.NEXT, None)

    @property
    def card_id(self) -> Union[str, None]:
        return self.relations.get(TaskRelations.CARD, None)

    @property
    def issue_id(self) -> Union[str, None]:
        return self.relations.get(TaskRelations.ISSUE, None)

    def get_description(self) -> str:
        desc_str = f"# Task: {self.name}\n"
        desc_str += f"## Description: \n{self.description}\n---\n"

        if self.summary:
            desc_str += f"## Summary: \n{self.summary}\n---\n"

        if self.details:
            details = format_nested_object(self.details)
            desc_str += f"## Details: \n{details}\n\n"
            inputs = ", ".join(self.inputs)
            desc_str += f" - Inputs: {inputs}\n"
            outputs = ", ".join(self.outputs)
            desc_str += f" - Outputs: {outputs}\n"
            desc_str += "---\n"

        if self.results:
            desc_str += f"## Results: \n{self.results}\n---\n"

        return desc_str

    def get_summary(self, indent: int=0) -> str:
        if self.summary:
            return self.summary

        summary = f"{indent*' '}Task: {self.name}\n"
        summary += f"{indent*' '}Description: {self.description}\n"
        summary += f"{indent*' '}Inputs: {self.inputs}\n"
        summary += f"{indent*' '}Outputs: {self.outputs}\n"
        return summary

    @property
    def inputs_str(self):
        return ", ".join(self.inputs)

    @property
    def outputs_str(self):
        return ", ".join(self.outputs)

    @property
    def short_title(self):
        return f"{self.name} - In:{self.inputs_str} | Out:{self.outputs_str}"

    @property
    def assigned_agent(self):
        if self.relations.get(TaskRelations.AGENT, None):
            return self.relations[TaskRelations.AGENT]

    def colored_card_str(self):
        from taskchain.parser.string_formatter.task_formatter import colored_task
        return colored_task(self)
