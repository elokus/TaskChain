from __future__ import annotations
from task_chain.communication.base import BaseCommunicator, BaseMessagingUnit
from task_chain.communication.units.interaction.non_interactive import NonInteractor
from task_chain.communication.units.messaging import SimpleMessaging
from task_chain.communication.units.type_messaging import SingleTypeMessaging
from task_chain.singleton import AbstractSingleton
from task_chain.task import Task


class NonInteractiveCommunicator(BaseCommunicator, AbstractSingleton):
    """A Singleton Facade for all communication systems"""

    def __init__(
            self,
            messaging: BaseMessagingUnit = SimpleMessaging(),
            interactor: BaseMessagingUnit = NonInteractor(),
    ):
        """simple communicator constructor with a trello board, a simple messaging system and an issue message store"""
        super().__init__()
        self.register(messaging)
        self.register(interactor)
        self.register(SingleTypeMessaging("issue"))
