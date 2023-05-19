from __future__ import annotations

from questionary import prompt

from taskchain.communication.base import BaseMessagingUnit
from taskchain.schema import TaskStatus
from taskchain.task.task_node import Task


def _review_task(remarks: str = None):
    if remarks is None:
        remarks = "No remarks"

    questions = [
        {
            "type": "text",
            "name": "feedback",
            "message": "Do you have any remarks?",
            "default": remarks,
        },
        {
            "type": "confirm",
            "name": "approved",
            "message": "Do you approve this task?",
            "default": True,
        },
        {
            "type": "select",
            "name": "status",
            "message": "set the status for that task.",
            "when": lambda answers: answers["approved"] is False,
            "choices": TaskStatus.list_values()
        }
    ]
    return prompt(questions)


class ConsoleInteractor(BaseMessagingUnit):
    """Abstract base class for fetching and submitting feedback interactions on tasks"""
    _data = {}

    def fetch_all(self):
        return NotImplemented

    def fetch(self, task: Task) -> dict[str, any]:
        remarks = self._data.get(task.id, None)
        print(f"Task details: \n{task.get_summary()}")
        answers = _review_task(remarks)
        if answers["approved"]:
            answers["status"] = TaskStatus.APPROVED
        del answers["approved"]
        return {
            "header": {"source": "console", "destination": task.id},
            "body": f"FEEDBACK: {answers['feedback']}",
            "payload": answers
        }

    def submit(
            self,
            message: str,
            header: dict,
            payload: dict = None,
            **kwargs: any):

        destination = header.get("destination", None)
        if destination is None:
            raise ValueError("No destination task specified.")

        self._data[destination] = {
            "header": header,
            "body": f"FEEDBACK: {message}",
            "payload": payload,
        }

    @property
    def type(self):
        return "feedback"

    def submit_direct(self, formatted_message: dict):
        return NotImplemented
