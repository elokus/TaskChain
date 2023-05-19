from __future__ import annotations

import json
import re
from typing import Type, TypeVar

from langchain.agents.structured_chat.output_parser import StructuredChatOutputParser
from langchain.base_language import BaseLanguageModel
from langchain.chains.llm import LLMChain
from langchain.output_parsers.prompts import NAIVE_FIX_PROMPT
from langchain.prompts.base import BasePromptTemplate
from langchain.schema import BaseOutputParser, OutputParserException
from pydantic import BaseModel, ValidationError

from taskchain.llm import get_basic_llm
from taskchain.parser.pydantic_parser.format_instructions import PYDANTIC_FORMAT_INSTRUCTIONS
from taskchain.parser.utilities import get_short_schema

T = TypeVar("T", bound=BaseModel)


class ReducedPydanticParser(BaseOutputParser[T]):
    pydantic_object: Type[T]

    def parse(self, text: str) -> T:
        try:
            # Greedy search for 1st json candidate.
            match = re.search(
                "\{.*\}", text.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL
            )
            json_str = ""
            if match:
                json_str = match.group()
            json_object = json.loads(json_str)
            try:
                return self.pydantic_object.parse_obj(json_object)
            except ValidationError as e:
                if "action_input" in json_object:
                    return self.pydantic_object.parse_raw(json_object["action_input"])
                else:
                    raise e

        except (json.JSONDecodeError, ValidationError) as e:
            name = self.pydantic_object.__name__
            msg = f"Failed to parse {name} from completion {text}. Got: {e}"
            raise OutputParserException(msg)

    def get_format_instructions(self) -> str:
        schema_str = get_short_schema(self.pydantic_object)
        return PYDANTIC_FORMAT_INSTRUCTIONS.format(schema=schema_str)

    @property
    def _type(self) -> str:
        return "pydantic"



class FixedReducedPydanticParser(BaseOutputParser[T]):
    """Wraps a parser and tries to fix parsing errors."""

    parser: BaseOutputParser[T]
    model: Type[T]
    retry_chain: LLMChain

    @classmethod
    def from_output_model(
            cls,
            model: Type[T],
            llm: BaseLanguageModel = get_basic_llm()
    ) -> FixedReducedPydanticParser:
        chain = LLMChain(llm=llm, prompt=NAIVE_FIX_PROMPT)
        parser = ReducedPydanticParser(pydantic_object=model)
        return cls(parser=parser, retry_chain=chain, model=model)


    @classmethod
    def from_llm(
            cls,
            llm: BaseLanguageModel,
            parser: BaseOutputParser[T],
            prompt: BasePromptTemplate = NAIVE_FIX_PROMPT,
    ) -> FixedReducedPydanticParser[T]:
        chain = LLMChain(llm=llm, prompt=prompt)
        return cls(parser=parser, retry_chain=chain)

    def parse(self, completion: str) -> T:
        try:
            parsed_completion = self.parser.parse(completion)
        except OutputParserException as e:
            new_completion = self.retry_chain.run(
                instructions=self.parser.get_format_instructions(),
                completion=completion,
                error=repr(e),
            )
            try:
                parsed_completion = self.parser.parse(new_completion)
            except:
                agent_action = StructuredChatOutputParser().parse(new_completion)
                new_completion = agent_action.tool_input
                parsed_completion = self.parser.parse(new_completion)
        return parsed_completion

    def get_format_instructions(self) -> str:
        return self.parser.get_format_instructions()

    @property
    def _type(self) -> str:
        return self.parser._type
