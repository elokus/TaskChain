from __future__ import annotations
from task_chain.communication.base import BaseMessagingUnit
from task_chain.schema.base import Comment
from task_chain.storage.storage_context import TaskContextStore
from task_chain.task import Task


class TrelloInteractor(BaseMessagingUnit):
    """Interactor for fetching and submitting feedback interactions on tasks"""

    def __init__(self, storage_context: TaskContextStore):

        if storage_context.project_board.type != "TrelloBoard":
            raise ValueError("The project board is not a TrelloBoard. Use other interactor.")

        self.task_storage = storage_context
        self.project_board = storage_context.project_board

    def fetch_all(self):
        return NotImplemented

    def fetch(self, task: Task) -> dict[str, str]:
        """Fetches the feedback and status of a task from the Trello card associated with it"""
        if task.card_id is None:
            raise ValueError("Task is not associated with a Trello card.")
        card = self.project_board.get_card(task.card_id)
        feedback = Comment(**card.comments)
        labels = [label.name for label in card.labels]
        status = "open" if len(labels) == 0 else labels[0].lower()
        return {
            "header": {"source": task.id, "destination": task.id},
            "body": f"Feedback for task {task.id}:\n{feedback}\nStatus: {status}",
            "payload": {"feedback": str(feedback), "status": status}
        }

    def submit(
            self,
            message: str,
            header: dict,
            payload: dict = None,
            **kwargs: any
    ):
        """Submits a feedback message to the Trello card associated with the receiver task as a comment"""
        if header["destination"] is None:
            raise ValueError("No destination task specified.")
        destination_task = self.task_storage.get_task(header["destination"])
        if destination_task.card_id is None:
            raise ValueError("Task is not associated with a Trello card.")
        card = self.project_board.get_card(destination_task.card_id)
        card.comment(message)

    def submit_direct(self, formatted_message: dict):
        return NotImplemented

    @property
    def type(self):
        return "feedback"

