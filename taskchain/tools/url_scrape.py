from typing import Type

from langchain import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel

"""Loader that uses Selenium to load a page, then uses unstructured to load the html.
"""
from typing import List

from langchain.docstore.document import Document
from taskchain.tools.research.search_result_loader import SearchResultLoader

class ToolArgs(BaseModel):
    url: str


class UrlScraper(SearchResultLoader):
    name: str = "url_scraper"
    description: str = "Download and summarize a web page into a list of insights. Takes a url a query as an input."
    args_schema: Type[BaseModel] = ToolArgs
    verbose: bool = True

    def _validate_query(self):
        pass

    def _run(self, input: str, **kwargs):
        docs = self.load_url(input)
        return self.summarize_results(docs)

    async def _arun(self, input: str, research_meta: dict, **kwargs):
        return NotImplemented

    def summarize_results(self, results: List[Document]):
        prompt_template = (
            "You are the ResearchAgent responsible for analyzing the collected data from various sources."
            " Using the following chunk of input data: {text},"
            " Return the analyzed information as a list of insights."
        )
        PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])

        chain = load_summarize_chain(ChatOpenAI(),
                                     chain_type="map_reduce",
                                     return_intermediate_steps=False,
                                     map_prompt=PROMPT,
                                     combine_prompt=PROMPT)
        return chain.run({"input_documents":results})



if __name__ == "__main__":
    #res = search_tool("Methods to generate income online with ChatGPT", {"title":"income-generation", "content_type":"articles", "context":"income methods", "tags":"income methods"})
    #print(res)

    metas = [{"a":1, "b":2}, {"a":3, "b":4}, {"a":1, "b":2}, {"a":3, "b":4}, {"a":1, "b":2}, {"a":3, "b":4}]
    mte = [str(d) for d in metas]
    print(set(mte))
