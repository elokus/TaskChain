from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Union

import uuid

from task_chain.schema import TaskType, TaskStatus


class PredictTask(BaseModel):
    name: str = Field(description="Name of the task (Title Case string).")
    description: str = Field(description="Description of the task.")
    inputs: list = Field(description="List of input key/s (underscore lowercase string)")
    outputs: list = Field(description="List of output key/s (underscore lowercase string).")


class PredictTaskSequence(BaseModel):
    tasks: list[PredictTask] = Field(description="List of tasks to be predicted.")


class BaseTask(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    name: str
    description: str
    status: TaskStatus = TaskStatus.OPEN
    type: TaskType = TaskType.TASK


class PredictTaskAgent(PredictTask):
    agent_name: str = Field(description="Name of the agent assigned.")


class PredictChoice(BaseModel):
    choice: int = Field(description="index of the chosen option (integer).")
    reason: str = Field(description="Reason for the choice (string).")


class PredictRevision(BaseModel):
    decision: bool = Field(description="Bool value indicating whether the task was executed successfully or not.")
    feedback: Union[str, None] = Field(description="Feedback instruction for the execution team.")

