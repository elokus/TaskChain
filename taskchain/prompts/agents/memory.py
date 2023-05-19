from typing import Union

from pydantic import BaseModel, Field, validator

from taskchain.prompts.loader import prompt_from_pydantic

ROLE_PREFIX_MEMORY = "You are {agent_name} Assistant. Your should execute a task with the following objective: {goal}."

INIT_MEMORY_TEMPLATE = """
Before you start your task define the metadata for storing you results and intermediate results into memory.
The memory is structured in several collections currently there are the following collections available:
{collections}
"""
INIT_MEMORY_FORMAT_INSTRUCTIONS = """
---
{schema}

---
You can define a new collection if you need by returning a new name into collection field of your response schema.
Define your research meta:
"""


class CollectionMeta(BaseModel):
    title: str = Field(description="name of the collection to store data in.")
    content_type: str = Field(description="content type of the expected data e.g.: Code, User data, Scientific Paper, Articles etc.")
    context: str = Field(description="A short key title for accessing this research within the collection")
    tags: Union[str, list] = Field(description="additional tags")

    @validator("tags", always=True)
    def tags_to_str(cls, v):
        if isinstance(v, list):
            return ",".join(v)

    @validator("title", always=True)
    def set_collection_title(cls, v):
        v = v.replace(" ", "-").lower()
        v = v.replace(".", "-").lower()
        v = v.replace(":", "-").lower()
        v = v.replace(",", "-").lower()
        v = v.replace("_", "-").lower()
        return v


MEMORY_PROMPT_TEMPLATE = ROLE_PREFIX_MEMORY + "\n" + INIT_MEMORY_TEMPLATE + "\n" + INIT_MEMORY_FORMAT_INSTRUCTIONS


MEMORY_STARTUP_PROMPT = prompt_from_pydantic(
    template=MEMORY_PROMPT_TEMPLATE,
    input_variables=["goal", "collections", "agent_name"],
    model=CollectionMeta
)