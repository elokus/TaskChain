from __future__ import annotations
from abc import abstractmethod, ABC
from typing import Union

from task_chain.singleton import AbstractSingleton
from task_chain.task import Task


class BaseMessagingUnit(ABC):
    """Abstract Base class for single communication unit"""

    @abstractmethod
    def fetch_all(self):
        pass

    @abstractmethod
    def fetch(self, task: Task):
        pass

    @abstractmethod
    def submit(
            self,
            message: str,
            header: dict,
            payload: dict = None,
            **kwargs: any):
        pass

    @property
    @abstractmethod
    def type(self):
        pass

    @abstractmethod
    def submit_direct(self, formatted_message: dict):
        pass


class BaseCommunicator(ABC):
    """A Facade abstract base class for all communication systems"""

    def __init__(self):
        self._units = {}

    def register(self, unit: BaseMessagingUnit):
        self._units[unit.type] = unit

    def fetch(self, message_type: str, task: Task) -> dict[str, Union[str, dict]]:
        """Fetches all messages for a given task."""
        return self._units[message_type].fetch(task)

    def fetch_all(self, message_type: str) -> list:
        """Fetches all messages for a given message type"""
        return self._units[message_type].fetch_all()

    def fetch_all_for_task(self, task: Task) -> dict[str, any]:
        """Fetches all messages for a given message type and destination"""
        messages = {}
        for message_type in self._units:
            messages[message_type] = self._units[message_type].fetch(task)
        return messages

    def submit(
            self,
            message: str,
            message_type: str,
            source_id: str = None,
            destination_id: str = None,
            payload: dict = None,
            header: dict = None,
            **kwargs: any):
        """Submits a message to the communication system
        Prepares header and payload for the message and submits it to the communication system.

        Args:
            message (str): The message to be submitted
            message_type (str): The type of the message, which routes the message to the correct communication unit
            source_id (Task, optional): The task that sends the message. Defaults to None.
            destination_id (Task, optional): The task that receives the message. Defaults to None.
            payload (dict, optional): The payload of the message. Defaults to None.
            header (dict, optional): The header of the message. Defaults to None.
                           If no header is provided, a header is created with the following structure:
                           {source: sender_task.id, destination: receiver_task.id}
                           If provided it overwrites the source and destination fields.

            **kwargs (any): Additional arguments for the communication unit


        """
        if message_type not in self._units:
            raise ValueError(f"Message type {message_type} not registered.")

        header = header or {}
        if "source" not in header:
            header["source"] = source_id
        if "destination" not in header:
            header["destination"] = destination_id

        return self._units[message_type].submit(message, header=header, payload=payload, **kwargs)

    def submit_direct(self, formatted_message: dict, message_type: str):
        if message_type not in self._units:
            raise ValueError(f"Message type {message_type} not registered.")

        return self._units[message_type].submit_direct(formatted_message)


