from task_chain.memory_store.provider import memory_store
from langchain.tools import BaseTool
from pydantic import BaseModel
from typing import Type
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from task_chain.llm_utils import get_llm_by_name



class SearchArgs(BaseModel):
    query: str
    repository_name: str


class CodeRetrievalTool(BaseTool):
    name: str = "code_retrieval"
    description: str = "Retrieves code from a code memory based on the provided query and repository."
    args_schema: Type[BaseModel] = SearchArgs
    DEFAULT_MODEL: str = "gpt-3.5-turbo"

    def _run(self, query: str, repository_name: str, **kwargs):
        retriever = memory_store.get_code_retriever(repository_name)
        llm = get_llm_by_name(self.DEFAULT_MODEL)
        qa = ConversationalRetrievalChain.from_llm(llm, retriever=retriever)
        return qa.run(question=query)

    async def _arun(self, query: str, repository_name: str, research_meta: dict, **kwargs):
        return NotImplemented
