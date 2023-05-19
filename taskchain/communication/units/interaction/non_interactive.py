from __future__ import annotations

from taskchain.communication.base import BaseMessagingUnit
from taskchain.schema import TaskStatus
from taskchain.task.task_node import Task


class NonInteractor(BaseMessagingUnit):
    """Abstract base class for fetching and submitting feedback interactions on tasks"""
    _data = {}
    def fetch_all(self):
        return NotImplemented

    def fetch(self, task: Task) -> dict[str, any]:
        return {
            "header": {"source": "console", "destination": task.id},
            "body": f"FEEDBACK: None",
            "payload": {"feedback": "", "status": TaskStatus.APPROVED}
        }


    def submit(
            self,
            message: str,
            header: dict,
            payload: dict = None,
            **kwargs: any):
        pass

    @property
    def type(self):
        return "feedback"

    def submit_direct(self, formatted_message: dict):
        return NotImplemented
