from task_chain.tools.research.search_result_loader import SearchResultLoader
from langchain.chains.summarize import load_summarize_chain
from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from task_chain.memory_store.provider import memory_store


def search_tool(query: str, research_meta: dict):
    """Perform a google search from organic results its extracting insights and storing them into research memory"""

    collection = research_meta["title"]
    searcher = SearchResultLoader.from_query(query)
    docs = searcher.load()

    memory_store.document.change_or_add_collection(collection, research_meta)

    memory_store.document.add(docs, research_meta)
    memory_store.document.persist()
    prompt_template = (
        "You are the ResearchAgent responsible for analyzing the collected data from various sources."
        " Using the following chunk of input data: {text},"
        f" analyze the information and identify relevant insights related to the following research objective: {query}."
        " Return the analyzed information as a list of insights."
    )
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])

    docs = memory_store.document.similarity_search(query, k=5)
    print([len(d.page_content) for d in docs])
    chain = load_summarize_chain(ChatOpenAI(),
                                 chain_type="map_reduce",
                                 return_intermediate_steps=True,
                                 map_prompt=PROMPT,
                                 combine_prompt=PROMPT)
    return chain({"input_documents":docs})


if __name__ == "__main__":
    res = search_tool("Methods to generate income online with ChatGPT", {"title":"income-generation", "content_type":"articles", "context":"income methods", "tags":"income methods"})
    print(res)