from typing import Type

from langchain import PromptTemplate, LLMChain
from langchain.tools import BaseTool
from pydantic import BaseModel
from taskchain.memory_store.provider import memory_store
from taskchain.processing.code import load_repository
from taskchain.schema.agents import SearchResultItems

from taskchain.llm import get_basic_llm
from taskchain.parser.simple_result_parser import SimpleResultParser
from taskchain.tools.research.search_result_loader import SearchResultLoader


class SearchArgs(BaseModel):
    query: str


class GitHubSearchTool(BaseTool):
    name: str = "github_search"
    description: str = "Search the web for a GitHub repository and load it into code memory. Takes a query as input"
    args_schema: Type[BaseModel] = SearchArgs
    verbose: bool = True

    def _run(self, query: str, **kwargs):
        url = self.find_repository_url(query)
        if url == "None" or url is None:
            return "No matching Repository found for the provided query  provide a different query."
        docs, repository_name = load_repository(url)
        if repository_name is None:
            return f"Error while parsing url {url}"
        memory_store.add_code(docs, repository_name=repository_name)
        return f"Repository: {repository_name} loaded into code memory."

    async def _arun(self, query: str, research_meta: dict, **kwargs):
        return NotImplemented

    def _get_search_items(self, query: str) -> list[SearchResultItems]:
        """Perform a google search from organic results its extracting insights and storing them into research memory"""
        query = self._validate_query(query)
        searcher = SearchResultLoader.from_query(query, verbose=self.verbose)
        return searcher.get_search_items()

    def find_repository_url(self, query: str) -> str:
        items = self._get_search_items(query)
        prompt_template = (
            "Based on the search results provided below find the url for the GitHub repository "
            "that matches the following query: {query}.\n\n"
            "Search Results: {text}.\n\n"
            "Return your result as follows without any additional text:\n"
            "Result: <url>\n"
            "If none of the results match the query, return\n "
            "Result: None"
        )
        prompt = PromptTemplate(
            template=prompt_template, input_variables=["text", "query"], output_parser=SimpleResultParser()
        )
        chain = LLMChain(prompt=prompt, llm=get_basic_llm())
        return chain.predict_and_parse(text=str(items), query=query)

    def _validate_query(self, query: str) -> str:
        if "git" not in query.lower():
            query += " github"
        return query