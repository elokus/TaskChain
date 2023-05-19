from __future__ import annotations

from langchain import LLMChain
from langchain.chains.base import Chain

from taskchain.chains.suggestion_chain import SuggestionChain
from taskchain.llm import get_llm_by_name
from taskchain.prompts.registry import PROMPT_REGISTRY
from taskchain.schema.types import PromptTypes


def load_chain(
        prompt_type: PromptTypes,
        llm_name: str = None,
        suggest: bool = False,
        llm_kwargs: dict = None,
        **kwargs,
) -> Chain:
    """Load a chain from a prompt type and llm name"""
    llm_kwargs = llm_kwargs or {}
    llm = get_llm_by_name(llm_name, **llm_kwargs)
    prompt = PROMPT_REGISTRY[prompt_type]
    if suggest:
        return SuggestionChain.from_llm(llm=llm, prompt=prompt, **kwargs)
    return LLMChain(llm=llm, prompt=prompt, **kwargs)