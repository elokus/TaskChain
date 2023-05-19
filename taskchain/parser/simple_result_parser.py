from __future__ import annotations

import re

from langchain.agents.agent import AgentOutputParser
from langchain.agents.mrkl.prompt import FORMAT_INSTRUCTIONS
from langchain.schema import BaseOutputParser
from langchain.schema import OutputParserException

PREFIX = "Result:"


class SimpleResultParser(AgentOutputParser):
    def get_format_instructions(self) -> str:
        return FORMAT_INSTRUCTIONS

    def parse(self, text: str) -> str:
        return text.split(PREFIX)[-1].strip()


        # \s matches against tab/newline/whitespace
        # regex = (
        #     r"Action\s*\d*\s*:[\s]*(.*?)[\s]*Action\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        # )
        # match = re.search(regex, text, re.DOTALL)
        # if not match:
        #     raise OutputParserException(f"Could not parse LLM output: `{text}`")
        # action = match.group(1).strip()
        # action_input = match.group(2)
        # return AgentAction(action, action_input.strip(" ").strip('"'), text)


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
