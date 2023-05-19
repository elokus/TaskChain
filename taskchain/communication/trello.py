from __future__ import annotations

from taskchain.communication.base import BaseCommunicator, BaseMessagingUnit
from taskchain.communication.units.interaction.trello import TrelloInteractor
from taskchain.communication.units.messaging import SimpleMessaging
from taskchain.communication.units.type_messaging import SingleTypeMessaging
from taskchain.singleton import AbstractSingleton
from taskchain.storage.storage_context import TaskContextStore


class SimpleTrelloCommunicator(BaseCommunicator, AbstractSingleton):
    """A Singleton Facade for all communication systems"""

    def __init__(
            self,
            messaging: BaseMessagingUnit = SimpleMessaging(),
            interactor: BaseMessagingUnit = TrelloInteractor(
                storage_context=TaskContextStore()
            ),
    ):
        """simple communicator constructor with a trello board, a simple messaging system and an issue message store"""
        super().__init__()
        self.register(messaging)
        self.register(interactor)
        self.register(SingleTypeMessaging("issue"))
