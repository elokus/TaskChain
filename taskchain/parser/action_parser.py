from __future__ import annotations

import re
from typing import TypeVar

from langchain.base_language import BaseLanguageModel
from langchain.chains.llm import LLMChain
from langchain.output_parsers.prompts import NAIVE_FIX_PROMPT
from langchain.prompts.base import BasePromptTemplate
from langchain.schema import BaseOutputParser, OutputParserException
from pydantic import BaseModel

from taskchain.llm import get_basic_llm

T = TypeVar("T", bound=BaseModel)


FORMAT_INSTRUCTIONS = """Use the following format for your responses do not provide any additional text:

Thought: you should always think about what to do
Action: <command>
"""



class SimpleActionParser(BaseOutputParser):
    def get_format_instructions(self) -> str:
        return FORMAT_INSTRUCTIONS

    def parse(self, text: str) -> str:
        #\s matches against tab/newline/whitespace
        regex = (
            r"Action\s*\d*\s*:[\s]*(.*)?[\s\n]*"
        )
        match = re.search(regex, text, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{text}`")
        action = match.group(1).strip()
        return action



class FixedActionParser(BaseOutputParser):
    """Wraps a parser and tries to fix parsing errors."""

    parser: BaseOutputParser = SimpleActionParser()
    retry_chain: LLMChain = LLMChain(llm=get_basic_llm(), prompt=NAIVE_FIX_PROMPT)

    @classmethod
    def from_output_model(
            cls,
            llm: BaseLanguageModel = get_basic_llm()
    ) -> FixedActionParser:
        chain = LLMChain(llm=llm, prompt=NAIVE_FIX_PROMPT)
        parser = SimpleActionParser()
        return cls(parser=parser, retry_chain=chain)


    @classmethod
    def from_llm(
            cls,
            llm: BaseLanguageModel,
            parser: BaseOutputParser,
            prompt: BasePromptTemplate = NAIVE_FIX_PROMPT,
    ) -> FixedActionParser[T]:
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
            parsed_completion = self.parser.parse(new_completion)

        return parsed_completion

    def get_format_instructions(self) -> str:
        return self.parser.get_format_instructions()

    @property
    def _type(self) -> str:
        return self.parser._type
