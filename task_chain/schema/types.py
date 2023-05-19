from __future__ import annotations
from enum import Enum


class MessageTypes(str, Enum):
    """Enum for message types

    Attributes:
        FEEDBACK: The message is User feedback
        ISSUE: The message is an issue
        DIRECT: The message is a direct message from Agent to Agent
    """

    FEEDBACK = "feedback"
    ISSUE = "issue"
    DIRECT = "direct"


class ManagerRole(str, Enum):
    """The role of the manager.

    Attributes:
        EXECUTION: The manager is responsible for the execution of a single task
        TRAINING: The manager is responsible for the training an Agent for a task
        REVISION: The manager is responsible for the revision of a task
        SUPERVISOR: The manager is responsible for the supervision of a sequence of subtask

    """

    EXECUTION = "execution"
    TRAINING = "training"
    REVISION = "revision"
    SUPERVISOR = "supervisor"


class IssueTypes(str, Enum):
    """The type of issues that can be reported.

    Attributes:
        EXEC: An Error occurred during running execute() method
        TOOL: The issue is related to the tool used for the task
        RESOURCE: The issue is related to the resources used for the task
        COMPETENCE: The issue is related to the competence of the agent
        UNDEFINED: The issue type is not defined yet
        APPROVAL: The Task is not approved
        BLOCKED: The Task is blocked by issues in subtasks


    """

    EXEC = "execution_error"
    TOOL = "tool_error"
    RESOURCE = "resource_issue"
    COMPETENCE = "competence_issue"
    UNDEFINED = "undefined_issue"
    APPROVAL = "approval_issue"
    BLOCKED = "blocked_issue"


class TaskType(str, Enum):
    """Task types used in Task definition
    Attributes:
        PROJECT: The task is the root project goal defining task
        PIPELINE: The task is the high-level pipeline goal
        TASK: A basic task within a pipeline
        SUBTASK: The task is a subtask of a task
        ISSUE: The task is an issue solving Task

    """
    PROJECT = "project"
    PIPELINE = "pipeline"
    TASK = "task"
    SUBTASK = "subtask"
    ISSUE = "issue"


class TaskStatus(str, Enum):
    """Task statuses used in Task definition
    Attributes:
        OPEN: The task is open and ready to be worked on
        IN_PROGRESS: The task is currently being worked on
        BLOCKED: The task is blocked and cannot be worked on
        CLOSED: The task is closed
        ISSUE: The task has an issue and cannot be worked on
    """
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    CLOSED = "closed"
    ISSUE = "issue"
    APPROVED = "approved"

    @classmethod
    def list_values(cls):
        return list(TaskStatus._value2member_map_.keys())


class TaskRelations(str, Enum):
    """Task relationships used in Task Graph

    Attributes:
        ROOT: The task is the root task aka pipeline of the current task
        PREV: The task is the previous task in the task graph
        NEXT: The task is the next task in the task graph
        CARD: The card id of the task
        PARENT: The task is a parent task of the task graph
        AGENT: The agent assigned to the task
        ISSUE: The task is an issue solving task

    """
    ROOT: str = "root"
    PREV: str = "previous"
    NEXT: str = "next"
    PARENT: str = "parent"
    CARD: str = "card"
    AGENT: str = "agent"
    ISSUE: str = "issue"


class PromptTypes(str, Enum):

    BREAK_DOWN = "break_down"
    BREAK_DOWN_CHUNK = "break_down_chunk"
    EXTEND_LIST = "extend_list"
    PARENT_TASK = "parent_task"
    ASSIGN_TASK = "assign_task"
    ASSIGN_REVISE_TASK = "assign_revise_task"
    REVISION_TASK = "revision_task"
