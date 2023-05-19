from __future__ import annotations
from trello import Card, Checklist, List, Board, Label, TrelloClient
from typing import Union, Optional
from task_chain.interaction import select_option
from requests.adapters import SSLError
from time import sleep

TRELLO_TYPES = Union[Card, Checklist, List, Board, Label, dict]


def retry_on_ssl_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SSLError:
            for i in range(1,5):
                sleep(i*2)
                try:
                    return func(*args, **kwargs)
                except SSLError:
                    continue

    return wrapper


def item_in_sequence(
        object_list: list[TRELLO_TYPES],
        name: str) -> bool:

    if len(object_list) == 0:
        return False
    if isinstance(object_list[0], dict):
        return any([obj["name"] == name for obj in object_list])
    return any([obj.name == name for obj in object_list])


def object_from_list(object_list: list[TRELLO_TYPES], name: str) -> Optional[TRELLO_TYPES]:
    for obj in object_list:
        if obj.name == name:
            return obj
    return None


def map_list_names(board) -> dict[str, any]:
    return {l.name: l for l in board.open_lists()}

def map_label_names(board) -> dict[str, any]:
    return {l.name: l for l in board.get_labels()}

@retry_on_ssl_error
def get_or_create_board_id(client: TrelloClient):
    boards = client.list_boards()
    options = [b.name for b in boards]
    options.append("Create new board")
    selected = select_option(options, "Select a trello board to use")
    if selected == "Create new board":
        board_name = input("Enter a name for the new board: ")
        board = client.add_board(board_name)
        board_id = board.id
    else:
        board_id = boards[options.index(selected)].id
    return board_id

@retry_on_ssl_error
def card_information_string(card: Card):
    card_str = f"# {card.name}"
    card_str += "Stats:"
    card_str += f"\n - List: {card.get_list().name}"
    card_str += f"\n - Labels: {', '.join([label.name for label in card.labels])}"
    movements = '\n   -'.join(card.list_movements())
    card_str += f"\n - Movements: {movements}"
    card_str += f"\n# Description: {card.desc}"
    return card_str