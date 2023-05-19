from __future__ import annotations

from typing import Sequence

from langchain.callbacks.manager import Callbacks, CallbackManager, CallbackManagerForChainRun

from taskchain.agents.agent_registry import AgentRegistry
from taskchain.communication.base import BaseCommunicator
from taskchain.executor.base import BaseTaskManager
from taskchain.executor.issue_handler import BaseIssueHandler
from taskchain.schema import TaskRelations
from taskchain.schema.types import MessageTypes
from taskchain.storage.base import BaseStore
from taskchain.storage.storage_context import TaskContextStore
from taskchain.task import Task
from taskchain.task.utilities import get_branch_tasks_by_id, filter_tasks_by_inputs


class ProjectExecutor:

    issue_backlog: list = []

    def __init__(
            self,
            task_storage: TaskContextStore,
            kv_storage: BaseStore,
            agent_registry: AgentRegistry,
            issue_handler: BaseIssueHandler,
            communicator: BaseCommunicator,
            callbacks: Callbacks = None,
            verbose: bool = True


    ) -> None:
        self.task_storage = task_storage
        self.kv_storage = kv_storage
        self.agent_registry = agent_registry
        self.issue_handler = issue_handler
        self.communication = communicator

        self.callbacks = callbacks
        self.verbose = verbose

    def startup(self, callbacks: Callbacks = None):
        """resolve issues and fetch feedback for project and pipeline tasks"""

        # fetch and resolve issues
        issues = self.communication.fetch_all(MessageTypes.ISSUE.value)
        for issue in issues:
            self.issue_handler.resolve(issue)

        relevant_tasks = []
        for pipe_id in self.pipeline_ids:
            relevant_tasks.extend(
                get_branch_tasks_by_id(pipe_id, self.task_storage)
            )


    def shutdown(self):
        pass

    def _init_callbacks(self, callbacks) -> CallbackManagerForChainRun:
        callback_manager = CallbackManager.configure(
            callbacks, self.callbacks, self.verbose
        )
        run_manager = callback_manager.on_chain_start(
            {"name": self.__class__.__name__},
            {}
        )
        return run_manager

    def run(self, callbacks: Callbacks = None):
        run_manager = self._init_callbacks(callbacks)

        #startup
        run_manager.on_text("running startup sequence")
        self.startup()
        run_manager.on_text("finished startup sequence")

        #run
        run_manager.on_text("running main sequence")
        self._run(run_manager)
        run_manager.on_text("finished main sequence")


        #shutdown
        run_manager.on_text("running shutdown sequence")
        self.shutdown()
        run_manager.on_text("finished shutdown sequence")

    def prepare_pipelines(self) -> Sequence[Task]:
        """find pipelines with all inputs ready and stored in kv_storage"""
        valid_pipelines = filter_tasks_by_inputs(self.pipeline_tasks, list(self.kv_storage.get_all().keys()))
        if len(valid_pipelines) == 0:
            raise ValueError("no valid pipelines found")
        return valid_pipelines

    def _run(self, run_manager: CallbackManagerForChainRun):
        # find ready tasks
        pipelines = self.prepare_pipelines()
        for pipe in pipelines:
            run_manager.on_text(f"starting pipeline {pipe.name}")
            self.execute_task(pipe, run_manager.get_child())
            run_manager.on_text(f"finished pipeline {pipe.name}")
        return

    def execute_task(self, task: Task, run_manager: CallbackManager):
        """execute task and all its children"""
        task_agent = self._setup_agent(task)
        task_agent.run(run_manager)
        self.task_storage.update_task(task)


    def _setup_agent(self, task: Task, **kwargs) -> BaseTaskManager:
        """Setup agent for task."""
        if task.assigned_agent is None:
            task.relations[TaskRelations.AGENT] = self.agent_registry.get_default_agent()

        task_agent = self.agent_registry.load(task.assigned_agent)
        task_agent.assign_task(task)
        return task_agent

    @property
    def pipeline_ids(self):
        return self.task_storage.task_network.get_children(
            self.task_storage.root_id
        )

    @property
    def pipeline_tasks(self):
        return self.task_storage.get_tasks(self.pipeline_ids)
