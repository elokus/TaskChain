from abc import ABC, abstractmethod


class BaseIssueHandler(ABC):

    @staticmethod
    @abstractmethod
    def specify(description: str, task_id: str):
        """Creates an issue from a task."""
        pass

    @abstractmethod
    def resolve(self, issue, *args, **kwargs):
        pass
