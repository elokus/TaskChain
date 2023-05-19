from typing import Type, Optional

from langchain import PromptTemplate
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool
from pydantic import BaseModel
from taskchain.tools.vectorstore_tool import CollectionRetrieverTools

from taskchain.tools.research.search_result_loader import SearchResultLoader

memory_store = None

class ResearchArgs(BaseModel):
    input: str
    research_meta: dict

class ResearchTool(BaseTool):
    name: str = "search_and_scrape"
    description: str = "Search the web for information related to a research objective. Takes a search query as an input."
    args_schema: Type[BaseModel] = ResearchArgs
    COLOR: str = "blue"
    verbose: bool = True

    def _validate_query(self):
        pass

    def _run(self, input: str, research_meta: dict, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs):
        self.search_and_scrape(input, research_meta, run_manager)
        return self.summarize_with_retriever(input, research_meta, run_manager)
        #return self.summarize_results(input, research_meta)

    async def _arun(self, input: str, research_meta: dict, run_manager: Optional[CallbackManagerForToolRun] = None, **kwargs):
        self.search_and_scrape(input, research_meta, run_manager)
        return self.summarize_results(input, research_meta, run_manager)

    def search_and_scrape(self, query: str, research_meta: dict, run_manager: Optional[AsyncCallbackManagerForToolRun] = None,):
        """Perform a google search from organic results its extracting insights and storing them into research memory"""
        collection = research_meta["title"]
        if not memory_store.check_query(query):
            _collection = memory_store.get_collection_from_query(query)
            return f"Query already exists in memory collection: {_collection}"

        searcher = SearchResultLoader.from_query(query, verbose=self.verbose)
        weblinks = searcher.get_search_items()
        search_items = []
        for item in weblinks:
            if memory_store.check_url(item.url):
                search_items.append(item)

        if not len(search_items) > 0:
            return
        docs = searcher.load_search_results(search_items)

        #ToDo: add retrieval for already saved documents
        memory_store.local.add_query(query, collection)
        for url, _ in search_items:
            if run_manager is not None:
                run_manager.on_text("parsing url: " + url, color="pink")
            memory_store.local.add_url(url, collection)
        memory_store.document.add(docs, research_meta)
        memory_store.persist()


    def summarize_with_retriever(self, query: str, research_meta: dict, run_manager: Optional[CallbackManagerForToolRun]=None):
        collection = research_meta["title"]
        retriever = CollectionRetrieverTools().get_retriever_func(collection)
        return retriever.run({"query":query})

    def summarize_results(self, query: str, research_meta: dict, run_manager: Optional[CallbackManagerForToolRun]=None):
        collection = research_meta["title"]
        memory_store.document.change_or_add_collection(collection, research_meta)
        prompt_template = (
            "You are the ResearchAgent responsible for analyzing the collected data from various sources."
            " Using the following chunk of input data: {text},"
            f" analyze the information and identify relevant insights related to the following research objective: {query}."
            " Return the analyzed information as a list of insights."
        )
        PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])

        docs = memory_store.document.similarity_search(query, k=5)
        chain = load_summarize_chain(ChatOpenAI(),
                                     chain_type="map_reduce",
                                     return_intermediate_steps=False,
                                     map_prompt=PROMPT,
                                     combine_prompt=PROMPT)
        if run_manager is not None:
            run_manager.on_text("Summarizing results", color="pink")
        return chain.run({"input_documents":docs})



if __name__ == "__main__":
    #res = search_tool("Methods to generate income online with ChatGPT", {"title":"income-generation", "content_type":"articles", "context":"income methods", "tags":"income methods"})
    #print(res)

    metas = [{"a":1, "b":2}, {"a":3, "b":4}, {"a":1, "b":2}, {"a":3, "b":4}, {"a":1, "b":2}, {"a":3, "b":4}]
    mte = [str(d) for d in metas]
    print(set(mte))
