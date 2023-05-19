from pydantic import BaseModel
from typing import Type
from langchain.tools import BaseTool
from task_chain.schema.base import BaseIssue


class IssueReportTool(BaseTool):
    name: str = "report_issue"
    description: str = "Use this when you have problems solving a task. Use only in extreme cases." \
                       "Describe your problem as an input to this tool."
    return_direct = True


    def _run(self, input: str, **kwargs) -> BaseIssue:
        issue = BaseIssue(description=input)
        return issue

    async def _arun(self, input: str, research_meta: dict, **kwargs):
        return NotImplemented
