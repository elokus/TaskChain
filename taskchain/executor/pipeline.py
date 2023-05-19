from __future__ import annotations

from typing import Sequence, Optional, Union

from langchain.agents import AgentExecutor
from langchain.callbacks.manager import CallbackManagerForChainRun

from taskchain.agents.agent_registry import AgentRegistry
from taskchain.communication.base import BaseCommunicator
from taskchain.executor.base import BaseTaskManager
from taskchain.executor.issue_handler import BaseIssueHandler
from taskchain.executor.simple import SimpleTaskManager
from taskchain.schema import TaskStatus
from taskchain.schema.base import BaseChain, BaseIssue, Issue
from taskchain.schema.types import MessageTypes, ManagerRole, IssueTypes
from taskchain.storage.storage_context import TaskContextStore
from taskchain.communication.non_interactive import NonInteractiveCommunicator
from taskchain.task import Task
from taskchain.executor.issue_handler.simple import SimpleIssueHandler


class PipelineManager(BaseTaskManager):

    def __init__(
            self,
            task: Task,
            agent_registry: AgentRegistry = None,
            agent_executor: Optional[AgentExecutor] = None,
            resources: dict[str, any] = None,
            communication: BaseCommunicator = None,
            issue_handler: BaseIssueHandler = None,
            task_storage: TaskContextStore = None,
            startup_chains: Sequence[BaseChain] = None,
            persist_path: str = None,
            persist: bool = False,
            role: ManagerRole = ManagerRole.SUPERVISOR.value,
            verbose: bool = False,
            **kwargs
    ):
        """Supervising Manager for a pipeline tasks with multiple subtasks.

        Args:
            task (Task): The pipeline parent task to be executed.
            agent_registry (AgentRegistry): The registry to load the agent from.
            agent_executor (AgentExecutor): The agent executor to use.
            resources (dict[str, any]): The resources to be used by the manager.
            communication (BaseCommunicator): The communicator to be used by the manager.
            issue_handler (BaseIssueHandler): The issue handler to be used by the manager.
            task_storage (TaskContextStore): The task storage to be used by the manager.
            startup_chains (Sequence[BaseChain]): The chains to be executed before the task.
            persist_path (str): The path to persist the task storage to.
            persist (bool): Whether to persist the task storage.
            role (ManagerRole): The role of the manager.
            verbose (bool): Whether to print the logs.

        Example:
            .. code-block:: python
                from task_chain.schema import Task, TaskStatus
                from task_chain.schema.agent import Agent, AgentRole



        """
        communication = communication or NonInteractiveCommunicator()
        task_storage = task_storage or TaskContextStore()
        issue_handler = issue_handler or SimpleIssueHandler(storage_context=task_storage)

        super().__init__(
            task=task,
            resources=resources,
            communication=communication,
            issue_handler=issue_handler,
            task_storage=task_storage,
            agent_registry=agent_registry,
            agent_executor=agent_executor,
            role=role,
            verbose=verbose,
            persist_path=persist_path,
            persist=persist,
            **kwargs
        )

        self.startup_chains = startup_chains
        self.closed_tasks = []
        self.blocked_tasks = []
        self._subordinate_tasks = None
        self.add_to_cache("_subordinate_tasks")

    def _startup(self, run_manager: CallbackManagerForChainRun = None) -> tuple[any, bool]:
        if self.startup_chains:
            for chain in self.startup_chains:
                output: dict = chain.predict_and_parse(**self._prep_inputs(chain.input_keys))
                self.resources.update(output)

        return None, True

    def _prep_tasks(self) -> list[Task]:
        """Filter subtasks where all the inputs are available in resource."""
        excluded_tasks = self.closed_tasks + self.blocked_tasks
        tasks = [
            self.task_storage.get_task(task_id) for task_id in self.subordinate_tasks
            if task_id not in excluded_tasks
        ]
        verified_tasks = []

        for task in tasks:
            if not task.inputs or all([input_key in self.resources for input_key in task.inputs]):
                verified_tasks.append(task)

        return verified_tasks

    def _run(self, run_manager: CallbackManagerForChainRun) -> Union[str, dict, BaseIssue]:
        """loop through all the subtasks and execute them."""
        tasks = self._prep_tasks()
        while tasks:
            for task in tasks:
                self._execute_subtask(task, run_manager)
            tasks = self._prep_tasks()

        if len(self.closed_tasks) == len(self.subordinate_tasks):
            result = {}
            for key in self.task.outputs:
                result[key] = self.resources[key]
            return result
        else:
            self.task.status = TaskStatus.BLOCKED
            return BaseIssue(
                description="unable to finish subtasks",
                type=IssueTypes.BLOCKED
            )

    def _execute_subtask(self, task: Task, run_manager: CallbackManagerForChainRun):
        """Execute a subtask."""
        task_manager = SimpleTaskManager(
            task=task,
            agent_registry=self.agent_registry,
            agent_executor=self.agent_executor,
            resources=self.resources,
            communication=self.communication,
            issue_handler=self.issue_handler,
            task_storage=self.task_storage,
            role=ManagerRole.EXECUTION.value,
            verbose=self.verbose,
        )
        task = task_manager.run(callbacks=run_manager.get_child())
        if task.status == TaskStatus.CLOSED:
            self.closed_tasks.append(task.id)
            for key, value in task.results.items():
                self.resources[key] = value
            return True
        else:
            self.blocked_tasks.append(task.id)
            return False

    def _shutdown(
            self,
            result: any,
            run_manager: CallbackManagerForChainRun = None
    ) -> tuple[any, bool]:
        """Shutdown the manager."""
        return result, True

    @property
    def subordinate_tasks(self):
        """One time call of subordinate tasks"""
        if self._subordinate_tasks is None:
            self._subordinate_tasks = self.task_storage.task_network.get_all_children(self.task.id)
        return self._subordinate_tasks

    def _process_issue(self):
        """Fetches all issues from communicator and resolves them if they are from subordinate tasks."""
        all_issues = self.communication.fetch_all(MessageTypes.ISSUE.value)

        if not all_issues:
            return
        in_charge = [issue for issue in all_issues if issue["header"]["source"] in self.subordinate_tasks]
        for issue in in_charge:
            issue = Issue(**issue["payload"])
            success = self.issue_handler.resolve(issue)
            # report unresolved issues
            if not success:
                issue.task_id = self.task.id
                self._submit_issue(issue)

        not_in_charge = [
            issue for issue in all_issues
            if issue["header"]["source"] not in self.subordinate_tasks
        ]
        for issue in not_in_charge:
            self._submit_issue(Issue(**issue["payload"]))
