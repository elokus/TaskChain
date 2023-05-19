from __future__ import annotations
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.prompts import PromptTemplate
from task_chain.config import Config

CFG = Config()


def get_basic_llm_chain(
        prompt_template: str,
        model_name=None,
        llm_kwargs: dict = None,
        **kwargs) -> LLMChain:

    if model_name is None:
        model_name = CFG.fast_llm_model
    if llm_kwargs is None:
        llm_kwargs = {}
    llm = ChatOpenAI(model_name=model_name, **llm_kwargs)
    prompt = PromptTemplate.from_template(prompt_template)
    return LLMChain(llm=llm, prompt=prompt, **kwargs)


def call_expert_llm(prompt, **kwargs):
    system = SystemMessagePromptTemplate.from_template(prompt)
    chain = LLMChain(llm=ChatOpenAI(model_name="gpt-4"), prompt=ChatPromptTemplate.from_messages([system]))
    return chain.predict(**kwargs)


def get_basic_llm(**kwargs):
    return ChatOpenAI(model_name=CFG.fast_llm_model, **kwargs)


def get_expert_llm(**kwargs):
    return ChatOpenAI(model_name="gpt-4", **kwargs)


def get_llm_by_name(model_name: str, **kwargs):
    if model_name is None:
        return get_basic_llm(**kwargs)
    return ChatOpenAI(model_name=model_name, **kwargs)


def get_default_llm(**kwargs):
    return get_basic_llm(**kwargs)