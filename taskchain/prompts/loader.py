from __future__ import annotations

from string import Formatter
from typing import Type, TypeVar, Union, Any, Optional

from fastapi.encoders import jsonable_encoder
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.prompts.chat import BaseMessagePromptTemplate
from pydantic import BaseModel

from taskchain.llm import get_basic_llm
from taskchain.parser.pydantic_parser import FixedReducedPydanticParser
from taskchain.parser.utilities import get_short_schema

T = TypeVar("T", bound=BaseModel)

def _prompt_from_pydantic(
        template: str,
        input_variables: list = None,
        partial_variables: dict = None,
        examples: str = None,
        model: Type[T] = None) -> tuple[
    str, Union[set, list], Union[dict[Any, Any], dict, None], Optional[FixedReducedPydanticParser]]:

    """Create PromptTemplate with output parser from Pydantic model and prompt template.
    placeholder for format instructions is {schema} in template.
    placeholder for example is {example} in template.
    """

    if model is None:
        output_parser = None
    else:
        output_parser = FixedReducedPydanticParser.from_output_model(model=model)


    partial_variables = {} if partial_variables is None else partial_variables
    if examples is not None:
        partial_variables["example"] = examples
    if output_parser is not None:


        partial_variables["schema"] = output_parser.get_format_instructions()

    if input_variables is None:
        input_variables = {
            v for _, v, _, _ in Formatter().parse(template) if v is not None and v not in partial_variables
        }

    return template, input_variables, partial_variables, output_parser

def _prompt_from_pydantic2(
        template: str,
        input_variables: list = None,
        partial_variables: dict = None,
        examples: str = None,
        model: Type[T] = None) -> tuple[str, list, dict, OutputFixingParser]:

    """Create PromptTemplate with output parser from Pydantic model and prompt template.
    placeholder for format instructions is {schema} in template.
    placeholder for example is {example} in template.
    """

    _parser = PydanticOutputParser(pydantic_object=model)
    output_parser = OutputFixingParser.from_llm(get_basic_llm(), _parser)

    partial_variables = {} if partial_variables is None else partial_variables
    if examples is not None:
        partial_variables["example"] = examples
    if output_parser is not None:

        SCHEMA = """
        The response should be a JSON object with the following schema:\n
        ```
        {schema}
        ```
        The response should be compatible with Python's json.loads function.
        """

        schema = jsonable_encoder(get_short_schema(model))

        partial_variables["schema"] = SCHEMA.format(schema=schema)

    if input_variables is None:
        input_variables = {
            v for _, v, _, _ in Formatter().parse(template) if v is not None and v not in partial_variables
        }

    return template, input_variables, partial_variables, output_parser

def prompt_from_pydantic(template: str,
                         input_variables: list = None,
                         partial_variables: dict = None,
                         examples: str = None,
                         model: Type[T] = None) -> PromptTemplate:
    template, input_variables, partial_variables, output_parser = _prompt_from_pydantic(
        template, input_variables, partial_variables, examples, model
    )
    return PromptTemplate(
        template=template,
        input_variables=input_variables,
        partial_variables=partial_variables,
        output_parser=output_parser,
    )

def chat_prompt_from_pydantic(
        messages: list[BaseMessagePromptTemplate],
        template: str,
        input_variables: list = None,
        partial_variables: dict = None,
        examples: str = None,
        model: Type[T] = None) -> ChatPromptTemplate:

    human_prompt = prompt_from_pydantic(
        template, input_variables, partial_variables, examples, model
    )
    partial_variables = partial_variables or {}
    final_prompt = HumanMessagePromptTemplate(prompt=human_prompt)
    prompt = ChatPromptTemplate.from_messages([*messages,final_prompt])
    prompt.output_parser = human_prompt.output_parser
    prompt.partial_variables = partial_variables
    return prompt
