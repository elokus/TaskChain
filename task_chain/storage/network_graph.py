from __future__ import annotations
from typing import Optional, Union, Sequence

from task_chain.storage.base import BaseTaskNetwork
from task_chain.task.task_node import Task
from colorama import Fore, Style, Back


def _colored_prefix(prefix: str, level: int):
    levels = {
        0: Fore.GREEN,
        1: Fore.YELLOW,
        2: Fore.BLUE,
        3: Fore.RED,
        4: Fore.MAGENTA,
        5: Fore.CYAN,
        6: Fore.WHITE,
    }
    return f"{levels[level]}{prefix}{Style.RESET_ALL}"


class TaskGraph(BaseTaskNetwork):
    """represents a tree structured task graph."""

    def load(self, data: dict):
        self.all_tasks = data['all_tasks']
        self.root_tasks = data['root_tasks']
        self.id_to_children = data['id_to_children']
        self.issue_to_id = data['issue_to_id']

    @property
    def size(self) -> int:
        """The number of tasks in the task graph."""
        return len(self.all_tasks)

    @property
    def id_to_index(self):
        """Map from task id to positional index"""
        return {task_id: index for index, task_id in self.all_tasks.items()}

    def get_index(self, task: Task):
        return self.id_to_index[task.id]

    def insert(
            self,
            task: Task,
            parent: Optional[Union[Task, str]] = None,
            children: Optional[Sequence[Union[Task, str]]] = None
    ):
        """Insert a task into the graph."""
        parent = parent or task.parent_id
        if parent is not None:
            return self.insert_under_parent(task, parent, children)

        index = self.size
        self.all_tasks[index] = task.id
        self.root_tasks[index] = task.id

        if children is None:
            children = []
        if all(isinstance(child, Task) for child in children):
            child_ids = [child.id for child in children]
        else:
            child_ids = [child for child in children]
        self.id_to_children[task.id] = child_ids

    def insert_under_issue(
            self,
            task: Task):
        """Map Issue ID to a task"""
        if task.issue_id:
            self.issue_to_id[task.issue_id] = task.id
        else:
            raise ValueError(f"Task {task.id} has no issue_id")

    def insert_under_parent(
            self,
            task: Task,
            parent: Union[Task, str, None],
            children: Optional[Sequence[Union[Task, str]]] = None
    ):
        """Insert a task under a parent task
        if None provided task will be added as root pipe task."""
        index = self.size
        if parent is None:
            self.root_tasks[index] = task.id
        else:
            parent_id = parent.id if isinstance(parent, Task) else parent
            if parent_id not in self.id_to_children:
                self.id_to_children[parent_id] = []
            self.id_to_children[parent_id].append(task.id)

        self.all_tasks[index] = task.id

        if children is None:
            children = []
        if all(isinstance(child, Task) for child in children):
            child_ids = [child.id for child in children]
        else:
            child_ids = [child for child in children]
        self.id_to_children[task.id] = child_ids

    def get_children(self, parent: Optional[Union[Task, str]]) -> list[str]:
        """Get children ids with a depth of 1 for a given parent task or id."""
        parent_id = parent.id if isinstance(parent, Task) else parent
        children = self.id_to_children[parent_id]
        return [child for child in children]

    def get_all_children(self, parent: Optional[Union[Task, str]]) -> list[str]:
        """Get all child up to an unlimited depth."""
        children = self.get_children(parent)
        if not children:
            return []
        for child in children:
            children.extend(self.get_all_children(child))
        return children

    def delete_task(self, task: Task):
        """Delete a task from the graph."""
        index = self.get_index(task)
        del self.all_tasks[index]
        if index in self.root_tasks:
            del self.root_tasks[index]
        if task.id in self.id_to_children:
            del self.id_to_children[task.id]

    def formatted_tree_view(self, task_id: str = None) -> str:
        if task_id is None:
            return self.print_list_tree()
        else:
            return self.print_list_tree_from(task_id)

    def print_list_tree_from(self, task_id: str):
        """Print the task graph as a list tree."""
        lvl = 0
        lines = [_colored_prefix("┐", lvl)]
        num_roots = len(self.root_tasks)
        for i, root_id in enumerate(self.root_tasks.values()):
            if root_id == task_id:
                root_id_str = f"{Back.BLACK}{root_id}{Style.RESET_ALL} {Fore.RED}<<<<<<<<{Fore.RESET}"
            else:
                root_id_str = root_id
            if i == num_roots - 1:
                root_str = f"{_colored_prefix('└──', lvl)}{root_id_str}"
                prefix = _colored_prefix("   ", lvl)
                sub_lines = self._node_to_str_from(prefix, root_id, lvl+1, task_id=task_id)
            else:
                root_str = f"{_colored_prefix('├──',lvl)}{root_id_str}"
                prefix = _colored_prefix("│  ", lvl)
                sub_lines = self._node_to_str_from(prefix, root_id, lvl+1, task_id=task_id)
            root_lines = [root_str] + sub_lines
            lines.extend(root_lines)
        return "\n".join(lines)

    def print_list_tree(self):
        """Print the task graph as a list tree."""
        lvl = 0
        lines = [_colored_prefix("┐", lvl)]
        num_roots = len(self.root_tasks)
        for i, root_id in enumerate(self.root_tasks.values()):
            if i == num_roots - 1:
                root_str = f"{_colored_prefix('└──', lvl)}{root_id}"
                prefix = _colored_prefix("   ", lvl)
                sub_lines = self._node_to_str(prefix, root_id, lvl+1)
            else:
                root_str = f"{_colored_prefix('├──',lvl)}{root_id}"
                prefix = _colored_prefix("│  ", lvl)
                sub_lines = self._node_to_str(prefix, root_id, lvl+1)
            root_lines = [root_str] + sub_lines
            lines.extend(root_lines)
        return "\n".join(lines)

    def _node_to_str(self, line_prefix: str, node_id: str, lvl: int=0):
        """Format a branch of the tree."""
        children = list(self.get_children(node_id))
        branches = len(children)
        lines = []
        if branches > 0:
            for i, child_id in enumerate(children):
                if i == branches - 1:
                    child_str = f"{line_prefix}{_colored_prefix('└──', lvl)}{child_id}"
                    sub_line_prefix = line_prefix + _colored_prefix("   ", lvl)
                else:
                    child_str = f"{line_prefix}{_colored_prefix('├──', lvl)}{child_id}"
                    sub_line_prefix = line_prefix + _colored_prefix("│  ", lvl)
                sub_lines = self._node_to_str(sub_line_prefix, child_id, lvl+1)
                child_lines = [child_str] + sub_lines
                lines.extend(child_lines)
        return lines

    def _node_to_str_from(self, line_prefix: str, node_id: str, lvl: int=0, task_id: str=None):
        """Format a branch of the tree."""
        children = list(self.get_children(node_id))
        branches = len(children)
        lines = []
        if branches > 0:
            for i, child_id in enumerate(children):
                if child_id == task_id:
                    child_id_str = f"{Back.BLACK}{child_id}{Style.RESET_ALL} {Fore.GREEN}<<<<<<<<{Fore.RESET}"
                else:
                    child_id_str = child_id

                if i == branches - 1:
                    child_str = f"{line_prefix}{_colored_prefix('└──', lvl)}{child_id_str}"
                    sub_line_prefix = line_prefix + _colored_prefix("   ", lvl)
                else:
                    child_str = f"{line_prefix}{_colored_prefix('├──', lvl)}{child_id_str}"
                    sub_line_prefix = line_prefix + _colored_prefix("│  ", lvl)
                sub_lines = self._node_to_str(sub_line_prefix, child_id, lvl+1)
                child_lines = [child_str] + sub_lines
                lines.extend(child_lines)
        return lines



