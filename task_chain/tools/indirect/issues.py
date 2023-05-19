from langchain import LLMChain, PromptTemplate
from langchain.tools import BaseTool
from task_chain.prompts.loader import prompt_from_pydantic
from task_chain.memory_store.provider import memory_store
from pydantic import BaseModel, Field
from typing import Type, Optional, Union


class AddInputArgs(BaseModel):
    task_id: str = Field(description="the task id to add the input to")
    input_name: str = Field(description="the name of the input variable to add to the task")
    description: str = Field(description="a description of the expected input data")


class AddInputTool(BaseTool):
    name: str = "add_input"
    description: str = "useful to add an input variable to a task which is used to access the resource storage"
    args_schema: Type[BaseModel] = None
    output_model: Type[BaseModel] = AddInputArgs
    multi_step: bool = True

    @property
    def args(self):
        return "task_id"

    def _run(self, input: any):
        print("SOLUTION: adding input to: " + str(input))
        return "Input variable added successfully"

    async def _arun(self, *args, **kwargs):
        return

    def get_context(self, task_id: str) -> str:
        return """
        Task: {
            "name": "analyze local code",
            "description": "analyze and summarize the local code",
            "inputs": ["objective"],
            "outputs": ["summary"],
            "id": "1234jklj23434",
            }
        """

    def get_instructions(self, task_id: str) -> PromptTemplate:
        context = self.get_context(task_id)
        template = """
        {context}
        
        To add an new input variable to a task:
        {schema}
        """
        return prompt_from_pydantic(template, model=self.output_model, partial_variables={"context": context})


class ChangeResourcesArgs(BaseModel):
    task_id: str = Field(description="the task id to add the input to")
    input_name: str = Field(description="the name of the input variable to change the value for")
    description: str = Field(description="a description of the expected input data")
    value: str = Field(description="the new value for the input variable")


class ChangeResources(BaseTool):
    name: str = "update_resources"
    description: str = (
        "Change a value for an input key or add a new key value pair in resource storage."
        " Use only if you know the value of a required input variable. Do not make a value up."
    )
    args_schema: Type[BaseModel] = None
    output_model: Type[BaseModel] = ChangeResourcesArgs
    multi_step: bool = True

    @property
    def args(self):
        return "task_id"

    def _run(self, input: any, **kwargs):
        if input.name == "CANCEL":
            print("\nCANCELING INPUT CHANGE\n")
            return "Input value not changed CANCELED by Agent"
        print("SOLUTION: changing input to: " + str(input))
        return "Input value changed successfully"

    async def _arun(self, *args, **kwargs):
        return


    def get_instructions(self, *args, **kwargs) -> PromptTemplate:
        template = """
        To change the value of a input variable for a task:
        {schema}
        
        Do only add resources if you have know the value do not make up a value.
        If you do not know the value of a input variable enter "CANCEL" into all fields of the schema.
        """
        return prompt_from_pydantic(template, model=self.output_model)


class CreateTaskArg(BaseModel):
    root_task_id: str = Field(description="the task id where the issue occurred")
    name: str = Field(description="the name of the new task")
    description: str = Field(description="a description of the new task")
    output: str = Field(description="the name of the output variable for storing the result of the task")
    responsible: str = Field(description="who is responsible for solving the task")


class CreateUserTask(BaseTool):
    name: str = "create_user_task"
    description: str = "create a dependent task for the user. Useful if human input, local knowledge, additional information is needed to solve a task"
    args_schema: Type[BaseModel] = None
    output_model: Type[BaseModel] = CreateTaskArg
    multi_step: bool = True

    @property
    def args(self):
        return "task_id"

    def _run(self, input: any, **kwargs):
        print("Creating Task for User" + str(input))
        return "Created Task for User successfully"

    async def _arun(self, *args, **kwargs):
        return


    def get_instructions(self, *args, **kwargs) -> PromptTemplate:
        template = """
        To create a new task for the user:
        {schema}
        """
        return prompt_from_pydantic(template, model=self.output_model)


class CreateAITask(BaseTool):
    name: str = "create_ai_task"
    description: str = "create a dependent task for an AI Agent. Useful if the issue can be solved by AI Agents with research and coding skills"
    args_schema: Type[BaseModel] = None
    output_model: Type[BaseModel] = CreateTaskArg
    multi_step: bool = True

    @property
    def args(self):
        return "task_id"

    def _run(self, input: any, **kwargs):
        print("Creating Task for User" + str(input))
        return "Created task for AI successfully"

    async def _arun(self, *args, **kwargs):
        return


    def get_instructions(self, *args, **kwargs) -> PromptTemplate:
        template = """
        To create a new task for the user:
        {schema}
        """
        return prompt_from_pydantic(template, model=self.output_model)


class ViewTaskResults(BaseTool):
    name: str = "task_status"
    description: str = "Useful to check if a dependent task was solved or not and to access results if the task is closed"
    args_schema: Type[BaseModel] = None
    output_model: Type[BaseModel] = None
    multi_step: bool = False

    @property
    def args(self):
        return "task_id"

    def _run(self, input: any, **kwargs):
        print("Viewing Task details for" + str(input))
        return f"task_id: {input}, status: open, result: None"

    async def _arun(self, *args, **kwargs):
        return


    def get_instructions(self, *args, **kwargs) -> PromptTemplate:
        template = """
        To create a new task for the user:
        {schema}
        """
        return prompt_from_pydantic(template, model=self.output_model)







if __name__ == "__main__":
    pass
