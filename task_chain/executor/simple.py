from __future__ import annotations
from typing import Sequence

from langchain.agents import AgentExecutor
from langchain.callbacks.manager import CallbackManagerForChainRun

from task_chain.agents.agent_registry import AgentRegistry
from task_chain.communication.base import BaseCommunicator
from task_chain.schema.types import MessageTypes, ManagerRole
from task_chain.executor.issue_handler import BaseIssueHandler
from task_chain.schema.base import BaseChain
from task_chain.storage.storage_context import TaskContextStore
from task_chain.task import Task

from task_chain.executor.base import BaseTaskManager


class SimpleTaskManager(BaseTaskManager):
    """A simple task manager that executes a single task.

    Executes a single task with a single agent prepares by running startup chains, executing agent
    and running shutdown chains.
    """

    def __init__(
            self,
            task: Task,
            agent_registry: AgentRegistry = None,
            agent_executor: AgentExecutor = None,
            resources: dict[str, any] = None,
            communication: BaseCommunicator = None,
            issue_handler: BaseIssueHandler = None,
            task_storage: TaskContextStore = None,
            startup_chains: Sequence[BaseChain] = None,
            persist_path: str = None,
            persist: bool = False,
            role: ManagerRole = ManagerRole.EXECUTION.value,
            verbose: bool = False,
            **kwargs
    ):
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
        self._subordinate_tasks = None
        self.add_to_cache("_subordinate_tasks")

    # TODO: add resource handler
    # load resource handler for complex resources that do not fit into agent context
    # e.g. vector_store_router, file_system, ...
    # and add appropriate tools to the agent config before loading the agent
    def _startup(self, run_manager: CallbackManagerForChainRun = None) -> tuple[any, bool]:
        if self.startup_chains:
            for chain in self.startup_chains:
                output: dict = chain.predict_and_parse(**self._prep_inputs(chain.input_keys))
                self.resources.update(output)

        if self.resources.get("resource_handler", None):
            pass

        if not self.agent_executor:
            if self.task.assigned_agent is None:
                raise ValueError("No agent assigned to task.")
            if self.agent_registry is None:
                raise ValueError("No agent registry provided.")
            self.agent_executor = self.agent_registry.load(
                self.task.assigned_agent, verbose=self.verbose
            )
        return None, True

    def _run(self, run_manager: CallbackManagerForChainRun) -> str:
        """Execute the task."""

        agent_input = self._prep_inputs(self.task.inputs)
        return self.agent_executor.run(
            **agent_input, callbacks=run_manager.get_child()
        )

    # TODO: add chain to prepare resources and select a resource handler for the following agents if necessary
    def _shutdown(
            self,
            result: any,
            run_manager: CallbackManagerForChainRun = None
            ) -> tuple[dict, bool]:
        """Shutdown the manager."""
        if len(self.task.outputs) == 1:
            result = {self.task.outputs[0]: result}
        elif len(self.task.outputs) > 1:
            if isinstance(result, dict) and all(key in result for key in self.task.outputs):
                result = {key: result[key] for key in self.task.outputs}
            else:
                raise ValueError(
                    f"Task {self.task.id} has multiple outputs but result is not a dict."
                )
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

        in_charge = [issue for issue in all_issues if issue["source"] in self.subordinate_tasks]
        for issue in in_charge:
            success = self.issue_handler.resolve(issue)
            # report unresolved issues
            if not success:
                issue.task_id = self.task.id
                self._submit_issue(issue)

        not_in_charge = [
            issue for issue in all_issues
            if issue["source"] not in self.subordinate_tasks
        ]
        for issue in not_in_charge:
            self._submit_issue(issue)
