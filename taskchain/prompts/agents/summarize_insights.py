from langchain import PromptTemplate

prompt_template="""
You are the ResearchAgent responsible for analyzing the collected data from various sources.
Using the following chunk of input data: {text},
analyze the information and identify relevant insights related to the following research objective: {query}.
Return the analyzed information as a list of insights.
"""

SUMMARIZE_PROMPT = PromptTemplate(template=prompt_template, input_variables=["text", "query"])