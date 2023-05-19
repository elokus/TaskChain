from typing import Type, Optional, Union

from langchain import LLMChain, PromptTemplate
from langchain.agents import AgentExecutor
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from taskchain.llm import get_basic_llm_chain


class LLMChainConfig(BaseModel):
    prompt_template: str
    model_name: str = "gpt-3.5-turbo"
    llm_kwargs: dict = Field(default_factory=dict)
    chain_kwargs: dict = Field(default_factory=dict)


class BaseChainTool(BaseTool):
    name: str = "evaluate"
    description: str = "useful for evaluating your results before returning your final response"
    args_schema: Type[BaseModel] = None
    chain: Union[LLMChain, AgentExecutor] = None
    multi_step: bool = False

    @property
    def args(self):
        if self.args_schema is not None:
            return self.args_schema.schema()["properties"]
        return {k : "string" for k in self.chain.input_keys}

    def _run(self, *args, **kwargs):
        return self.chain.run(*args, **kwargs)

    async def _arun(self, *args, **kwargs):
        return await self.chain.arun(*args, **kwargs)


    def get_instructions(self, *args, **kwargs) -> PromptTemplate:
        pass


    @classmethod
    def from_chain_config(
            cls,
            config: LLMChainConfig,
            name: str,
            description: str,
            **kwargs) -> BaseTool:

        chain = get_basic_llm_chain(
            prompt_template=config.prompt_template,
            model_name=config.model_name,
            llm_kwargs=config.llm_kwargs,
            **config.chain_kwargs
        )
        return cls(name=name, description=description, chain=chain, **kwargs)

    @classmethod
    def from_template(
            cls,
            template: str,
            name: str,
            description: str,
            llm_kwargs: Optional[dict] = None,
            chain_kwargs: Optional[dict] = None,
            **kwargs) -> BaseTool:

        chain = get_basic_llm_chain(
            prompt_template=template,
            llm_kwargs=llm_kwargs,
            **chain_kwargs
        )

        return cls(name=name, description=description, chain=chain, **kwargs)




if __name__ == "__main__":
    pass
