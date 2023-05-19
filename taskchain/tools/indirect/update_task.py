from typing import Type, Union

from langchain import PromptTemplate
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, root_validator
from taskchain.memory_store.provider import memory_store

from taskchain.parser.utilities import validate_id
from taskchain.prompts.loader import prompt_from_pydantic


class ChangeKwarg(BaseModel):
    key: str = Field(description="The key to change the value for.")
    value: Union[str, list, dict] = Field(description="The new value for the key.")


class InputSchema(BaseModel):
    task_id: str = Field(description="The Task ID where an value should be changed.")

    @root_validator
    def validate_id(cls, values: dict[str, any]):
        id = values["task_id"]
        try:
            validate_id(id)
            return values
        except:
            raise ValueError(f"Input ID: {id} is not a valid ID.")


class BaseUpdateTask(BaseTool):
    name: str = "update_task"
    description: str = "useful for updating the current state of a task."
    args_schema: Type[BaseModel] = InputSchema
    input_model: Type[BaseModel] = ChangeKwarg
    multi_step: bool = True
    task_id: str = None

    def _parse_input(
            self,
            tool_input: Union[str, dict],
    ) -> None:
        """Convert tool input to pydantic model."""
        tool_input = tool_input["input"]
        input_args = self.input_model
        if isinstance(tool_input, str):
            if input_args is not None:
                key_ = next(iter(input_args.__fields__.keys()))
                input_args.validate({key_: tool_input})
        elif isinstance(tool_input, input_args):
            return
        else:
            if input_args is not None:
                try:
                    input_args.validate(tool_input)
                except:
                    print(tool_input)

    def _parse_init_input(
            self,
            tool_input: Union[str, dict],
    ) -> None:
        """Convert tool input to pydantic model."""
        input_args = self.args_schema
        if isinstance(tool_input, str):
            if input_args is not None:
                key_ = next(iter(input_args.__fields__.keys()))
                input_args.validate({key_: tool_input})
        else:
            if input_args is not None:
                input_args.validate(tool_input)


    def _run(self, input: Union[ChangeKwarg]):
        memory_store.update_task(self.task_id, **{input.key:input.value})
        task = memory_store.get_task(self.task_id)
        if input.key == "dependencies":
            print("updating dependencies...")
            for dependency in task.dependencies:
                dep_task = memory_store.get_task(dependency)
                res = memory_store.project.add_dependend_card(task.card_id, dep_task.card_id)
                if res:
                    print(f"Attach Card: {dep_task.card_id} to card: {task.card_id}")
                else:
                    print(f"Failed to attach card for card: {task.card_id} to card: {dep_task.card_id}")
        memory_store.project.add_label(task.card_id, "depends")
        return f"Task updated for Task ID: {self.task_id}\nFor key: {input.key}\nnew value: {input.value}"


    async def _arun(self, *args, **kwargs):
        return

    def get_context(self, task_id: str) -> str:
        return memory_store.get_task(task_id).dict()

    def _context_options(self, task_id: str) -> dict[str, any]:
        return memory_store.get_task(task_id).dict()

    def get_instructions(self, task_id: dict) -> PromptTemplate:
        self._parse_init_input(task_id)
        self.task_id = task_id["task_id"]
        context = self.get_context(self.task_id)
        context = str(context).replace("{", "{{").replace("}", "}}")
        prefix = f"This is the current state of the task:\n{context}"
        template = """
        
To add an change a key value pair to the task, use the following format:
{schema}
"""
        return prompt_from_pydantic(prefix+template, model=self.input_model)
