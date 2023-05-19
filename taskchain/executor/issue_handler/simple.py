from __future__ import annotations

from taskchain.executor.issue_handler.base import BaseIssueHandler
from taskchain.schema import TaskRelations, TaskStatus
from taskchain.schema.base import Issue
from taskchain.storage.storage_context import TaskContextStore
from taskchain.task.utilities import generate_issue_task


class SimpleIssueHandler(BaseIssueHandler):
    """A simple issue handler that creates a default issue task"""

    def __init__(self, storage_context: TaskContextStore):
        self.task_storage = storage_context

    @staticmethod
    def specify(description: str, task_id: str) -> Issue:
        """Creates an issue object from a task.
        Attributes:
            description: A description of the issue.
            task_id: The id of the task that the issue is related to.
        """
        issue = Issue(description=description, task_id=task_id)
        return issue

    def resolve(self, issue: Issue, *args, **kwargs):
        """Resolves an issue by creating a task from it and updating the issue status.
        Attributes:
                issue: The issue to resolve.
        """
        if isinstance(issue, dict):
            issue = Issue(**issue)
        ref_task = self.task_storage.get_task(issue.task_id)
        issue_task = generate_issue_task(issue, ref_task)
        ref_task.relations[TaskRelations.ISSUE] = issue_task.id
        ref_task.status = TaskStatus.ISSUE
        self.task_storage.add_task(issue_task)
        self.task_storage.update_task(ref_task)
