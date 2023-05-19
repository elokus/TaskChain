from task_chain.schema.output_model import PredictRevision
from task_chain.prompts.loader import prompt_from_pydantic
from langchain.prompts import PromptTemplate


EVALUATION_TEMPLATE = """
As the RevisionAgent, evaluate the quality of task execution for the given goal: {goal}. 
Use the specified evaluation criteria: {evaluation}.
For the provided results: {result}. 
Provide a brief evaluation report.
"""


REVISION_TEMPLATE = """
You are an Task Execution Supervisor who is revising following task: {task}.
The evaluation of the results led to the following evaluation report: {evaluation_report}
You should now make a final decision whether the task was executed successfully or not.
If not you should provide a short feedback instruction for the execution team.

---
{schema}
---

Revision:
"""


EVALUATION_PROMPT = PromptTemplate(template=EVALUATION_TEMPLATE, input_variables=["goal", "evaluation", "result"])

REVISION_PROMPT = prompt_from_pydantic(
    template=REVISION_TEMPLATE,
    input_variables=["task", "evaluation_report"],
    model=PredictRevision
)
