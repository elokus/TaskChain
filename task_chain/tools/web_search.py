from task_chain.tools.research.search_result_loader import SearchResultLoader
from langchain.tools import BaseTool
from task_chain.schema import SearchResultItems
from pydantic import BaseModel
from typing import Type


class SearchArgs(BaseModel):
    input: str

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "Performs a web search based on the provided query and returns the top results with urls and snippets."
    args_schema: Type[BaseModel] = SearchArgs
    COLOR: str = "blue"
    verbose: bool = True

    def _validate_query(self):
        pass

    def _run(self, input: str, **kwargs) -> str:
        items = self._get_search_items(input)
        return str(items)

    async def _arun(self, input: str, research_meta: dict, **kwargs):
        return NotImplemented

    def _get_search_items(self, query: str) -> list[SearchResultItems]:
        """Perform a google search from organic results its extracting insights and storing them into research memory"""
        searcher = SearchResultLoader.from_query(query, verbose=self.verbose)
        return searcher.get_search_items()


