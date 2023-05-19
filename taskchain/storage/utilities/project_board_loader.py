from __future__ import annotations

from typing import Union

import taskchain.integrations.trello as trello
from taskchain.storage.base import BaseProjectBoard

TYPE_TO_PROJECT_BOARD = {
    "TrelloBoard": trello.TrelloBoard
}

def load_project_board(data: dict) -> Union[BaseProjectBoard, None]:
    if data["project_board"] == "None":
        return None
    else:
        project_cls = TYPE_TO_PROJECT_BOARD[data["project_board"]["type"]]
        return project_cls(project_id=data["project_board"]["project_id"])