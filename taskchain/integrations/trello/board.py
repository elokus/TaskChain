from __future__ import annotations

from trello import Card

import taskchain.integrations.trello.utilities as trutils
from taskchain.schema import TaskType, TaskStatus, TaskRelations
from taskchain.storage.base import BaseProjectBoard
from taskchain.storage.task_store import TaskStore
from taskchain.task.task_node import Task
from taskchain.utilities import get_trello_client

task_store = TaskStore()


DEFAULT_CHECKLIST_NAME = "Subtasks"

DEFAULT_LABEL: dict[str, str] = {
    TaskStatus.CLOSED: "green",
    TaskStatus.OPEN: "yellow",
    TaskStatus.IN_PROGRESS: "orange",
    TaskStatus.ISSUE: "red",
    TaskStatus.BLOCKED: "red",
}


class TrelloBoard(BaseProjectBoard):

    def __init__(self, board_id: str = None, list_for_pipeline: bool = True):
        """Trello board integration.
        Mirrors tasks to a Trello Board and adds Card IDs to the task nodes.

        Attributes:
            board_id: Trello board ID.
            list_for_pipeline: If True, a list for each pipeline is created where TaskType.TASK will be added.
        """


        self.client = get_trello_client()
        if board_id is None:
            board_id = trutils.get_or_create_board_id(self.client)

        super().__init__(board_id)
        self.list_for_pipeline = list_for_pipeline
        self.board = self.client.get_board(self.project_id)
        self._lists = trutils.map_list_names(self.board)
        self._labels = trutils.map_label_names(self.board)

    @trutils.retry_on_ssl_error
    def get_all(self):
        cards = self.board.visible_cards()
        cards = [trutils.card_information_string(card) for card in cards]
        return cards

    @trutils.retry_on_ssl_error
    def add_task(self, task: Task):
        """Create Trello Card from Task and add Card ID to Task Node."""
        list_name = self._prep_list_name(task)
        if list_name not in self._lists:
            self._lists[list_name] = self.board.add_list(list_name, pos="bottom")

        card = self._lists[list_name].add_card(
            name=task.name,
            desc=task.get_description()
        )

        parent = task_store.get_task(task.parent_id)
        if parent is not None:
            parent_card = self.board.get_card(parent.card_id)
            self.add_checklist_item(parent_card, task.name)

        task.relations[TaskRelations.CARD] = card.id
        task_store.put(task.id, task.dict())

    @trutils.retry_on_ssl_error
    def close_task(self, task: Task):
        """Close a task by setting the card to closed and move to close list in Trello."""
        card = self.board.get_card(task.card_id)
        card.set_closed(True)

        parent = task_store.get_task(task.parent_id)
        if parent is not None:
            parent_card = self.board.get_card(parent.card_id)
            checklist = trutils.object_from_list(parent_card.checklists, DEFAULT_CHECKLIST_NAME)
            if checklist is not None:
                checklist.set_checklist_item(name=task.name, checked=True)

        list_name = TaskStatus.CLOSED.title()
        if list_name not in self._lists:
            self._lists[list_name] = self.board.add_list(list_name)
        card.change_list(self._lists[list_name].id)

    @trutils.retry_on_ssl_error
    def set_status(self, task: Task, status: str):
        """Set the status of a task as colored and named label.
        Only one label per card is allowed."""
        card = self.board.get_card(task.card_id)
        self._set_status(card, status)

    @trutils.retry_on_ssl_error
    def get_status(self, task: Task) -> str:
        """Get the status of a task as colored and named label."""
        card = self.board.get_card(task.card_id)
        return [label.name for label in card.labels][0]


    @trutils.retry_on_ssl_error
    def delete_task(self, task: Task):
        """Delete a task card from Trello."""
        card = self.board.get_card(task.card_id)
        card.delete()

    @trutils.retry_on_ssl_error
    def update_task(self, updated_task: Task, card_id: str = None):
        """Update the name, description and status of a task from updated Task Node."""
        if card_id is None:
            card_id = updated_task.card_id
        card = self.board.get_card(card_id)
        card.set_name(updated_task.name)
        card.set_description(updated_task.description)
        self._set_status(card, updated_task.status)

    @trutils.retry_on_ssl_error
    def add_comment(self, task: Task, comment: str):
        """Add a comment to a task card."""
        card = self.board.get_card(task.card_id)
        card.comment(comment)

    @trutils.retry_on_ssl_error
    def get_comments(self, task: Task):
        """Get all comments from a task card."""
        card = self.board.get_card(task.card_id)
        return card.comments

    @trutils.retry_on_ssl_error
    def add_checklist_item(
            self,
            card: Card,
            item_name: str,
            checklist_name: str = DEFAULT_CHECKLIST_NAME
    ):
        checklist = trutils.object_from_list(card.checklists, checklist_name)
        if checklist is None:
            checklist = card.add_checklist(checklist_name, [])

        if not trutils.item_in_sequence(checklist.items, item_name):
            checklist.add_checklist_item(item_name)


    ### HELPER FUNCTIONS ###

    def _prep_list_name(self, task: Task) -> str:
        """Prepares the list name for a Card creation based on the task type.
        If list_for_pipeline is True, the list name will be the pipeline name.
        Else the list name will be the task type.
        """
        if task.type == TaskType.TASK:
            if self.list_for_pipeline:
                pipeline_name = task_store.get_task(task.parent_id).name
                return f"P - {pipeline_name}"
        return task.type.title()

    @trutils.retry_on_ssl_error
    def _set_status(self, card: Card, status: str):
        for label in card.labels:
            card.remove_label(label)

        if status not in self._labels:
            color = DEFAULT_LABEL.get(status, "purple")
            self._labels[status] = self.board.add_label(status, color)
        card.add_label(status)

    @trutils.retry_on_ssl_error
    def _get_status(self, card: Card) -> str:
        """Get the status of a task as colored and named label."""
        return [label.name for label in card.labels][0]

    @property
    def type(self):
        return "TrelloBoard"
