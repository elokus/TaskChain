from __future__ import annotations
from langchain import BasePromptTemplate

from task_chain.prompts.task import (
    BREAK_DOWN, _SUMMARY_SCHEMA,
    EXTEND_TASKS,
    PARENT_TASK_PROMPT,
    ASSIGN_TASK_PROMPT,
    BEAK_DOWN_CHUNK_PROMPT, _SUMMARY_CHUNK_SCHEMA,

)
from task_chain.schema.types import PromptTypes
from task_chain.prompts.loader import prompt_from_pydantic
from task_chain.schema.output_model import PredictTaskSequence, PredictTask, PredictChoice


PROMPT_REGISTRY: dict[PromptTypes, BasePromptTemplate] = {
    PromptTypes.BREAK_DOWN: prompt_from_pydantic(
        BREAK_DOWN,
        input_variables=["context", "remarks"],
        partial_variables={"schema": _SUMMARY_SCHEMA},
    ),
    PromptTypes.EXTEND_LIST: prompt_from_pydantic(
        EXTEND_TASKS,
        input_variables=["context", "remarks"],
        model=PredictTaskSequence,
    ),
    PromptTypes.PARENT_TASK: prompt_from_pydantic(
        PARENT_TASK_PROMPT,
        input_variables=["context", "remarks"],
        model=PredictTask,
    ),
    PromptTypes.ASSIGN_TASK: prompt_from_pydantic(
        ASSIGN_TASK_PROMPT,
        input_variables=["context", "remarks"],
        model=PredictChoice,
    ),
    PromptTypes.BREAK_DOWN_CHUNK: prompt_from_pydantic(
        BEAK_DOWN_CHUNK_PROMPT,
        input_variables=["context", "remarks"],
        partial_variables={"schema": _SUMMARY_CHUNK_SCHEMA},
    )
}