from __future__ import annotations

from taskchain.communication.base import BaseMessagingUnit
from taskchain.task import Task


class SingleTypeMessaging(BaseMessagingUnit):

    def __init__(self, message_type: str):
        """ Stores messages of a given type.
        Allows fetching and submitting of messages of that type without receiver verification

        Attributes:
            message_type (str): the type of messages to be stored
        """
        self._type = message_type
        self._data: list[dict] = []

    def fetch_all(self):
        messages = self._data
        self._data = []
        return messages

    def fetch(self, task: Task) -> list[dict]:
        return []

    def submit(
            self,
            message: str,
            header: dict,
            payload: dict = None,
            **kwargs: any):
        """Add a message with self._type to the message queue without specific destination id."""
        message = {"header": header, "body": message, "payload": payload}
        self._data.append(message)

    def submit_direct(self, formatted_message: dict):
        self._data.append(formatted_message)

    @property
    def type(self):
        return self._type
