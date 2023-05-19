from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Optional, List, Tuple, Any, Union, Sequence

from langchain import LLMChain, PromptTemplate, FewShotPromptTemplate, BasePromptTemplate
from langchain.agents import BaseSingleActionAgent, AgentOutputParser
from langchain.base_language import BaseLanguageModel
from langchain.callbacks.base import BaseCallbackManager
from langchain.callbacks.manager import Callbacks
from langchain.prompts import AIMessagePromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, \
    ChatPromptTemplate
from langchain.schema import AgentAction, AgentFinish, BaseMessage
from langchain.tools import BaseTool
from pydantic import BaseModel, root_validator

logger = logging.getLogger(__name__)


class BaseIndirectActionAgent(BaseSingleActionAgent):
    """Base Agent class."""

    @abstractmethod
    def plan_tool_input(
            self,
            intermediate_steps: List[Tuple[AgentAction, str]],
            tool_instructions: str,
            agent_action: AgentAction,
            callbacks: Callbacks = None,
            **kwargs: Any,
    ):
        return


    async def aplan_tool_input(
            self,
            intermediate_steps: List[Tuple[AgentAction, str]],
            tool_instructions: str,
            agent_action: AgentAction,
            callbacks: Callbacks = None,
            **kwargs: Any,
    ):
        return


class Agent(BaseIndirectActionAgent):
    """Class responsible for calling the language model and deciding the action.

    This is driven by an LLMChain. The prompt in the LLMChain MUST include
    a variable called "agent_scratchpad" where the agent can put its
    intermediary work.
    """

    llm_chain: LLMChain
    output_parser: AgentOutputParser
    allowed_tools: Optional[List[str]] = None
    tool_system_template: str = None

    def get_allowed_tools(self) -> Optional[List[str]]:
        return self.allowed_tools

    @property
    def return_values(self) -> List[str]:
        return ["output"]

    def _fix_text(self, text: str) -> str:
        """Fix the text."""
        raise ValueError("fix_text not implemented for this agent.")

    @property
    def _stop(self) -> List[str]:
        return [
            f"\n{self.observation_prefix.rstrip()}",
            f"\n\t{self.observation_prefix.rstrip()}",
        ]

    def _construct_scratchpad(
            self, intermediate_steps: List[Tuple[AgentAction, str]]
    ) -> Union[str, List[BaseMessage]]:
        """Construct the scratchpad that lets the agent continue its thought process."""
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\n{self.observation_prefix}{observation}\n{self.llm_prefix}"
        return thoughts

    def _construct_instruction_prompt(
            self,
            agent_action: AgentAction,
            tool_instructions: PromptTemplate) -> ChatPromptTemplate:
        """Construct the instruction prompt."""
        input_variables = self.llm_chain.prompt.input_variables
        template = self.tool_system_template.format(tool_name=agent_action.tool)

        messages = [
            SystemMessagePromptTemplate.from_template(template),
            *self.llm_chain.prompt.messages[1:],
            AIMessagePromptTemplate.from_template(
                template="{action_log}"),
            HumanMessagePromptTemplate(prompt=tool_instructions),
        ]
        action_log = agent_action.log if agent_action.log else agent_action.tool

        return ChatPromptTemplate(
            input_variables=input_variables,
            messages=messages,
            output_parser=tool_instructions.output_parser,
            partial_variables={"action_log":action_log}
        )
    #
    # def verify_plan(
    #         self,
    #         output: Union[AgentAction, AgentFinish],
    #         intermediate_steps: List[Tuple[AgentAction, str]],
    #         callbacks: Callbacks = None,
    #         **kwargs: Any,
    # ) -> dict[str, Any]:
    #     if len(intermediate_steps) == 0:
    #         return {"is_true": True, "reason": "No steps to verify."}
    #     observation = intermediate_steps[-1][1]
    #     thoughts = f"\n{self.observation_prefix}{observation}\n{self.llm_prefix}"
    #     thoughts += output.log
    #
    #     chain = LLMChain(prompt=VERIFICATION_PROMPT, llm=self.llm_chain.llm)
    #     result = chain.predict_and_parse(input=thoughts, callbacks=callbacks)
    #     if not result.is_true:
    #         from colorama import Fore
    #         print(Fore.RED + f"\n\n VERIFICATION FAILED \n\n due to: {result.reason}")
    #     return result.dict()


    def plan_tool_input(
            self,
            intermediate_steps: List[Tuple[AgentAction, str]],
            tool_instructions: PromptTemplate,
            agent_action: AgentAction,
            callbacks: Callbacks = None,
            **kwargs: Any,
    ) -> Union[str, dict[str, Any], BaseModel]:
        prompt = self._construct_instruction_prompt(agent_action, tool_instructions)

        chain = LLMChain(
            llm=self.llm_chain.llm,
            prompt=prompt
        )
        full_inputs = self.get_full_inputs(intermediate_steps, **kwargs)
        print("The Prompt for intermediate tool step is: \n\n")
        print(prompt.format_messages(**full_inputs))
        return {"input": chain.predict_and_parse(
            callbacks=callbacks, **full_inputs
        )}


    def plan(
            self,
            intermediate_steps: List[Tuple[AgentAction, str]],
            callbacks: Callbacks = None,
            **kwargs: Any,
    ) -> Union[AgentAction, AgentFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with observations
            callbacks: Callbacks to run.
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """
        full_inputs = self.get_full_inputs(intermediate_steps, **kwargs)
        full_output = self.llm_chain.predict(callbacks=callbacks, **full_inputs)
        return self.output_parser.parse(full_output)

    async def aplan(
            self,
            intermediate_steps: List[Tuple[AgentAction, str]],
            callbacks: Callbacks = None,
            **kwargs: Any,
    ) -> Union[AgentAction, AgentFinish]:
        """Given input, decided what to do.

        Args:
            intermediate_steps: Steps the LLM has taken to date,
                along with observations
            callbacks: Callbacks to run.
            **kwargs: User inputs.

        Returns:
            Action specifying what tool to use.
        """
        full_inputs = self.get_full_inputs(intermediate_steps, **kwargs)
        full_output = await self.llm_chain.apredict(callbacks=callbacks, **full_inputs)
        return self.output_parser.parse(full_output)


    async def aplan_tool_input(
            self,
            intermediate_steps: List[Tuple[AgentAction, str]],
            tool_instructions: str,
            agent_action: AgentAction,
            callbacks: Callbacks = None,
            **kwargs: Any,
    ):
        return

    def get_full_inputs(
            self, intermediate_steps: List[Tuple[AgentAction, str]], **kwargs: Any
    ) -> dict[str, Any]:
        """Create the full inputs for the LLMChain from intermediate steps."""
        thoughts = self._construct_scratchpad(intermediate_steps)
        new_inputs = {"agent_scratchpad": thoughts, "stop": self._stop}
        full_inputs = {**kwargs, **new_inputs}
        return full_inputs

    @property
    def input_keys(self) -> List[str]:
        """Return the input keys.

        :meta private:
        """
        return list(set(self.llm_chain.input_keys) - {"agent_scratchpad"})

    @root_validator()
    def validate_prompt(cls, values: dict) -> dict:
        """Validate that prompt matches format."""
        prompt = values["llm_chain"].prompt
        if "agent_scratchpad" not in prompt.input_variables:
            logger.warning(
                "`agent_scratchpad` should be a variable in prompt.input_variables."
                " Did not find it, so adding it at the end."
            )
            prompt.input_variables.append("agent_scratchpad")
            if isinstance(prompt, PromptTemplate):
                prompt.template += "\n{agent_scratchpad}"
            elif isinstance(prompt, FewShotPromptTemplate):
                prompt.suffix += "\n{agent_scratchpad}"
            else:
                raise ValueError(f"Got unexpected prompt type {type(prompt)}")
        return values

    @property
    @abstractmethod
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""

    @property
    @abstractmethod
    def llm_prefix(self) -> str:
        """Prefix to append the LLM call with."""

    @classmethod
    @abstractmethod
    def create_prompt(cls, tools: Sequence[BaseTool]) -> BasePromptTemplate:
        """Create a prompt for this class."""

    @classmethod
    def _validate_tools(cls, tools: Sequence[BaseTool]) -> None:
        """Validate that appropriate tools are passed in."""
        for tool in tools:
            if not tool.is_single_input:
                raise ValueError(
                    f"{cls.__name__} does not support multi-input tool {tool.name}."
                )

    @classmethod
    @abstractmethod
    def _get_default_output_parser(cls, **kwargs: Any) -> AgentOutputParser:
        """Get default output parser for this class."""

    @classmethod
    def from_llm_and_tools(
            cls,
            llm: BaseLanguageModel,
            tools: Sequence[BaseTool],
            callback_manager: Optional[BaseCallbackManager] = None,
            output_parser: Optional[AgentOutputParser] = None,
            **kwargs: Any,
    ) -> "Agent":
        """Construct an agent from an LLM and tools."""
        cls._validate_tools(tools)
        llm_chain = LLMChain(
            llm=llm,
            prompt=cls.create_prompt(tools),
            callback_manager=callback_manager,
        )
        tool_names = [tool.name for tool in tools]
        _output_parser = output_parser or cls._get_default_output_parser()
        return cls(
            llm_chain=llm_chain,
            allowed_tools=tool_names,
            output_parser=_output_parser,
            **kwargs,
        )

    def return_stopped_response(
            self,
            early_stopping_method: str,
            intermediate_steps: List[Tuple[AgentAction, str]],
            **kwargs: Any,
    ) -> AgentFinish:
        """Return response when agent has been stopped due to max iterations."""
        if early_stopping_method == "force":
            # `force` just returns a constant string
            return AgentFinish(
                {"output": "Agent stopped due to iteration limit or time limit."}, ""
            )
        elif early_stopping_method == "generate":
            # Generate does one final forward pass
            thoughts = ""
            for action, observation in intermediate_steps:
                thoughts += action.log
                thoughts += (
                    f"\n{self.observation_prefix}{observation}\n{self.llm_prefix}"
                )
            # Adding to the previous steps, we now tell the LLM to make a final pred
            thoughts += (
                "\n\nI now need to return a final answer based on the previous steps:"
            )
            new_inputs = {"agent_scratchpad": thoughts, "stop": self._stop}
            full_inputs = {**kwargs, **new_inputs}
            full_output = self.llm_chain.predict(**full_inputs)
            # We try to extract a final answer
            parsed_output = self.output_parser.parse(full_output)
            if isinstance(parsed_output, AgentFinish):
                # If we can extract, we send the correct stuff
                return parsed_output
            else:
                # If we can extract, but the tool is not the final tool,
                # we just return the full output
                return AgentFinish({"output": full_output}, full_output)
        else:
            raise ValueError(
                "early_stopping_method should be one of `force` or `generate`, "
                f"got {early_stopping_method}"
            )

    def tool_run_logging_kwargs(self) -> dict:
        return {
            "llm_prefix": self.llm_prefix,
            "observation_prefix": self.observation_prefix,
        }

