from __future__ import annotations
from task_chain.schema import TaskType, TaskStatus
from task_chain.task.task_node import Task
from colorama import Fore, Style, Back


def colored_task(
        task: Task,
        indent: int = 14,
        max_width: int = 64,
    ) -> str:

    text_color = Fore.GREEN
    if task.type == TaskType.ISSUE:
        highlight = Fore.RED
        text_color = Fore.YELLOW

    elif task.status == TaskStatus.ISSUE:
        highlight = Fore.RED
        text_color = Fore.YELLOW
    elif task.status == TaskStatus.IN_PROGRESS:
        highlight = Fore.YELLOW
    elif task.status == TaskStatus.CLOSED:
        highlight = Fore.GREEN
        text_color = Fore.WHITE
    else:
        highlight = Fore.BLUE

    lines = _formatted_task_lines(
        task, highlight=highlight, text_color=text_color, indent=indent, max_width=max_width)
    return _outline_task(lines, highlight=highlight, max_width=max_width)


def _prefix(key, width: int=13):
    """Return a prefix string."""
    _width = width - len(key)
    return f"{key.upper()}:{_width*' '}"


def trim_lines(content: str, indent=14, max_width=61):
    lines = []
    for line in content.split("\n"):
        while len(line)+indent > max_width:
            if not lines:
                lines.append(line[:max_width-indent-1] + "-")
                line = line[max_width-indent-1:]
            else:
                lines.append(" "*indent + line[:max_width-indent-1] + "-")
                line = line[max_width-indent-1:]
        if not lines:
            lines.append(line)
        else:
            lines.append(" "*indent + line)
    return lines


def _formatted_task_lines(
        task: Task,
        indent: int = 14,
        max_width: int = 44,
        highlight: str = Fore.BLUE,
        text_color: str = Fore.GREEN) -> list[str]:
    """Print a task as an outline."""
    first_line = f"{_prefix('TASK TYPE')}{highlight}{task.type.upper()}{Fore.RESET}"
    space = max_width - len(f"STATUS: {task.status}") - len(_remove_ansii(first_line)) - 2
    first_line += f"{' '*space}STATUS: {highlight}{task.status.upper()}{Fore.RESET}"

    lines = [
        first_line,
        " ",
        f"{_prefix('ID')}{highlight}{task.id}{Fore.RESET}",
        " "
    ]

    for key in ["name", "description", "inputs", "outputs"]:
        content = getattr(task, key)
        if isinstance(content, list):
            content = ", ".join(content)
            if len(content)+indent > max_width:
                content = "\n".join(content.split(", "))
        _lines = trim_lines(content, indent=indent, max_width=max_width)
        lines.append(f"{_prefix(key)}{text_color}{_lines[0]}{Fore.RESET}")
        for line in _lines[1:]:
            lines.append(f"{text_color}{line}{Fore.RESET}")
    if task.assigned_agent:
        lines.append(f"{_prefix('AGENT')}{highlight}{task.assigned_agent}{Fore.RESET}")

    return lines


def _outline_task(
        lines: list[str],
        max_width: int = 64,
        highlight: str = Fore.BLUE,
    ) -> str:

    new_lines = []
    width = max_width + 4
    # header
    new_lines.append(f" {highlight}{'-'*width}{Fore.RESET}")
    for line in lines:
        new_lines.append(f"{highlight}|{Fore.RESET} {line}{' '*(width-2-len(_remove_ansii(line)))}{highlight} |{Fore.RESET}")

    # footer
    new_lines.append(f" {highlight}{'-'*width}{Fore.RESET}")
    return "\n".join(new_lines)


def _remove_ansii(string: str):
    """Remove ansii characters from a string."""
    import re
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', string)


