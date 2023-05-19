from abc import abstractmethod

from taskchain.communication.base import BaseMessagingUnit
from taskchain.task import Task


class BaseMessaging(BaseMessagingUnit):

    @abstractmethod
    def submit(self, message: str, receiver_task: Task, **kwargs: any):
        pass


class SimpleMessaging(BaseMessaging):
    """A router for sending and receiving messages between agents.
    Stores messages in a dictionary keyed by receiver name.
    """

    def __init__(self):
        self._data = {}
        self._receivers = []

    def submit(
            self,
            message: str,
            header: dict = None,
            payload: dict = None,
            **kwargs: any):
        """Push a message to a receiver identified by the task id."""
        if header["destination"] is None:
            raise ValueError("No destination id specified.")
        self._validate_receiver(header["destination"])
        self._data[header["destination"]].append(
            {"header": header, "body": message, "payload": payload}
        )

    def fetch(self, task: Task) -> list[dict]:
        """Fetches all messages for a given task and clears the message queue.
        Receiver is identified by the task id.
        """
        messages = self._get_messages(task.id)
        self._data[task.id] = []
        return messages

    def _get_messages(self, receiver: str) -> list[dict]:
        self._validate_receiver(receiver)
        return self._data[receiver]

    def _validate_receiver(self, receiver: str):
        if receiver not in self._receivers:
            self._receivers.append(receiver)
            self._data[receiver] = []

    def fetch_all(self):
        ...

    @property
    def type(self):
        return "direct"

    def submit_direct(self, formatted_message: dict):
        self._data.update(formatted_message)
