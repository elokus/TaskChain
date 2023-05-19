"""Chain for summarization with self-verification."""
from __future__ import annotations

from typing import Dict, List, Optional, Union

from colorama import Fore
from langchain import LLMChain, PromptTemplate, BasePromptTemplate
from langchain.base_language import BaseLanguageModel
from langchain.callbacks.manager import CallbackManagerForChainRun, Callbacks
from langchain.chains.base import Chain
from langchain.llms.base import BaseLLM

import taskchain.interaction as interact


class SuggestionChain(Chain):
    """Chain that suggests differen outputs and lets the user choose one."""
    output_key: str = "output"
    prompt: BasePromptTemplate
    proposal_prompt: BasePromptTemplate
    llm: BaseLanguageModel = None
    choices: int = 3
    is_feedback: bool = True

    @property
    def input_keys(self) -> List[str]:
        """Return input keys."""
        return self.prompt.input_variables

    @property
    def output_keys(self) -> List[str]:
        """Return output keys."""
        return [self.output_key]

    def _call(
            self,
            inputs: Dict[str, any],
            run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, any]:
        """Call the chain.

        Args:
            inputs: Inputs to the chain.
            run_manager: Callback manager for the chain run.

        Returns:
            Outputs of the chain.
        """
        init_chain = LLMChain(
            prompt=self.prompt,
            output_key="output",
            llm=self.llm,
            verbose=self.verbose
        )
        further_chain = LLMChain(
            prompt=self.proposal_prompt,
            output_key="output",
            llm=self.llm,
            verbose=self.verbose
        )
        selection = []
        i = 0
        while i < self.choices:
            if i == 0:
                output = init_chain.predict_and_parse(**inputs, callbacks=None)
            else:
                output = further_chain.predict_and_parse(**inputs, callbacks=None)
            selection.append(output)
            inputs["proposals"] = "\n\n".join([f"{n+1}. {sel}" for n, sel in enumerate(selection)])
            output_log = f"\n\nChoice {i+1}:\n{output}\n"
            i += 1

            if self.is_feedback and i < self.choices:
                feedback = inputs["feedback"] if "feedback" in inputs else ""
                _feedback = interact.input_feedback(output_log + "\n\nPlease enter your feedback here:\n>>>>>>")
                if _feedback == "stop":
                    break
                feedback += _feedback + "\n\n"
                inputs["feedback"] = feedback
            else:
                print(Fore.CYAN + output_log)

        selected = interact.select_option_cta_only(options=[n for n, sel in enumerate(selection)])

        return {self.output_key: selection[selected]}

    def predict_and_parse(
            self, callbacks: Callbacks = None, **kwargs: any
            ) -> Union[str, List[str], Dict[str, any]]:
            """Call predict and then parse the results.

            """

            result = self(kwargs, callbacks=callbacks)[self.output_key]
            return result

    @classmethod
    def from_llm(
            cls,
            prompt: PromptTemplate,
            llm: BaseLLM = None,
            choices: int = 3,
            is_feedback: bool = True,
            verbose: bool = True,
            **kwargs,
            ) -> "SuggestionChain":

        proposal_suffix = """
You made already following proposals for the above task:
{proposals}

Make a new proposal for the task:
        """

        proposal_with_feedback_suffix = """
      
You made already following proposals for the above task:
{proposals}

The User gave following feedback:
{feedback}

Make a new proposal for the task.
{remarks}
        """
        remarks = proposal_suffix if not is_feedback else proposal_with_feedback_suffix
        proposal_template = prompt.template
        proposal_template = proposal_template.replace("{remarks}", remarks)
        print(proposal_template)
        input_variables = ["proposals", "feedback"] if is_feedback else ["proposals"]
        input_variables.extend(prompt.input_variables)

        proposal_prompt = PromptTemplate(
            template=proposal_template,
            input_variables=input_variables,
            partial_variables=prompt.partial_variables,
            output_parser=prompt.output_parser,
        )

        return cls(
            prompt=prompt,
            proposal_prompt=proposal_prompt,
            llm=llm,
            choices=choices,
            verbose=verbose,
            is_feedback=is_feedback,
            **kwargs
        )
