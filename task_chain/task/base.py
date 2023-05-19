from __future__ import annotations
from pydantic import Field
from typing import Optional, Any

from task_chain.schema import BaseTask


class BaseTaskNode(BaseTask):
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
    relations: Optional[dict[str, Any]] = Field(default_factory=dict)
    inputs: list = Field(
        description="List of input keys of the task",
        default_factory=list
    )
    outputs: list = Field(
        description="List of output keys of the task",
        default_factory=list)