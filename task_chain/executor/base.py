from __future__ import annotations
from abc import abstractmethod, ABC
from typing import Union

from langchain.agents import AgentExecutor
from langchain.callbacks.manager import Callbacks, CallbackManager, CallbackManagerForChainRun

from task_chain.agents.agent_registry import AgentRegistry
from task_chain.communication.base import BaseCommunicator
from task_chain.schema.types import MessageTypes, ManagerRole, IssueTypes
from task_chain.executor.issue_handler import BaseIssueHandler
from task_chain.schema import TaskRelations, TaskStatus
from task_chain.storage.storage_context import TaskContextStore
from task_chain.task import Task

from task_chain.schema.base import BaseIssue, Issue

DEFAULT_PERSIST_PATH = "./storage/task_manager_run.json"

class BaseTaskManager(ABC):

    role: str

    def __init__(
            self,
            task: Task,
            resources: dict[str, any] = None,
            agent_registry: any = None,
            agent_executor: AgentExecutor = None,
            communication: BaseCommunicator = None,
            issue_handler: BaseIssueHandler = None,
            task_storage: TaskContextStore = None,
            role: ManagerRole = ManagerRole.SUPERVISOR,
            callbacks: Callbacks = None,
            verbose: bool = False,
            persist_path: str = None,
            persist: bool = False,
            **kwargs
    ):
        self.task = task
        self.role = role
        self.task_storage = task_storage
        self.resources = resources or {}
        self.communication = communication
        self.issue_handler = issue_handler
        self.cache_attributes = list()
        self.verbose = verbose
        self.callbacks = callbacks
        self.persist_path = persist_path
        self.should_persist = persist
        self.agent_executor = agent_executor
        self.agent_registry = agent_registry


        if persist_path is None:
            self.persist_path = DEFAULT_PERSIST_PATH
        if self.agent_executor is None and self.agent_registry is None:
            self.agent_registry = AgentRegistry()

    ################################
    #  Main Execution Process
    ################################

    def startup(self, run_manager: CallbackManagerForChainRun = None, skip_startup: bool = False) -> tuple[any, bool]:
        """Startup process before execution. Resolve Issues, fetch messages, initialize Agents, etc.
        Custom startup logic can be implemented in _startup() method.
        Returns:
            Tuple[startup_output, success]
                startup_output (any): Output object of startup process (e.g. an Issue)
                success (bool): Whether startup was successful
        """
        if self.issue_handler is not None:
            self._process_issue()

        if self.communication:
            all_messages = self.communication.fetch_all_for_task(self.task)
            feedback = ""
            for message_type, messages in all_messages.items():
                if message_type == MessageTypes.FEEDBACK.value:
                    self.task.status = messages["payload"]["status"]
                    feedback += f"USER FEEDBACK: {messages['payload']['feedback']}"
                else:
                    if isinstance(messages, list):
                        if len(messages) > 0:
                            feedback += f"{message_type.upper()}: {', '.join([m['body'] for m in messages])}\n"
                    else:
                        raise NotImplementedError(f"Message type {message_type} not implemented.")
            if feedback != "":
                self.resources["feedback"] = feedback

        if skip_startup:
            return None, True

        return self._startup(run_manager=run_manager)

    def run(
            self,
            callbacks: Callbacks = None,
            repeat_execution: bool = False,
            skip_startup: bool = False) -> any:
        """Main Execution process runs startup, execution and shutdown.
        Returns the result of the execution or an issue if an error occurred.
        """
        run_manager = self._init_callbacks(callbacks=callbacks)
        if not repeat_execution:
            self.on_execution_start(run_manager=run_manager)
            startup_output, success = self.startup(run_manager=run_manager, skip_startup=skip_startup)
        else:
            startup_output, success = None, True

        if not success:
            result = startup_output
        elif self.task.status == TaskStatus.APPROVED.value:
            try:
                result = self._run(run_manager=run_manager)
            except Exception as e:
                self.on_execution_error(str(e), run_manager=run_manager)
                result = BaseIssue(description=str(e), type=IssueTypes.EXEC)
        else:
            result = BaseIssue(description="waiting for approval", type=IssueTypes.APPROVAL)

        return self.shutdown(result=result, run_manager=run_manager)

    def shutdown(self, result: any, run_manager: CallbackManagerForChainRun = None) -> Task:

        if isinstance(result, BaseIssue):
            result = Issue(**result.dict(exclude_unset=True), task_id=self.task.id)
            self.on_issue(issue=result, run_manager=run_manager)
            self.task.relations[TaskRelations.ISSUE] = result.id
            self.task.status = TaskStatus.ISSUE
            self._submit_issue(issue=result)
        else:
            shutdown_output, success = self._shutdown(result=result, run_manager=run_manager)
            if success:
                self.task.status = TaskStatus.CLOSED
                self.task.results = shutdown_output
            else:
                # add shutdown output to feedback and rerun execution process
                self.resources["feedback"] = self.resources["feedback"] + "\n" + shutdown_output
                return self.run(repeat_execution=True)

        self.task_storage.update_task(self.task)

        if self.should_persist:
            self.persist()

        self.on_execution_end(result, run_manager=run_manager)
        return self.task

    ################################
    #  Abstract Methods
    ################################

    @abstractmethod
    def _startup(self, run_manager: CallbackManagerForChainRun) -> tuple[dict, bool]:
        pass

    @abstractmethod
    def _run(self, run_manager: CallbackManagerForChainRun) -> Union[str, dict, BaseIssue]:
        pass

    @abstractmethod
    def _shutdown(
            self,
            result: any,
            run_manager: CallbackManagerForChainRun
            ) -> tuple[any, bool]:
        pass

    @abstractmethod
    def _process_issue(self):
        pass

    ################################
    #  State Management
    ################################

    def persist(self):
        """Persist all states of the manager."""
        if self.persist_path is not None:
            return self.task_storage.persist(self.persist_path)
        return self.task_storage.persist()

    def add_to_cache(self, *args):
        new_attr = [arg for arg in args if hasattr(self, arg)]
        self.cache_attributes.extend(new_attr)
        self.cache_attributes = list(set(self.cache_attributes))

    def reset_cache(self):
        for attr in self.cache_attributes:
            setattr(self, attr, None)

    ################################
    #  Helper
    ################################

    def _fetch_feedback_and_status(self):
        if self.communication:
            feedback_message = self.communication.fetch(MessageTypes.FEEDBACK.value, self.task)
            feedback = feedback_message["payload"]["feedback"]
            status = feedback_message["payload"]["status"]
        else:
            feedback = "None"
            status = TaskStatus.APPROVED.value
        self.task.status = status
        self.task_storage.update_task(self.task)
        return feedback

    def _submit_issue(
            self,
            issue: Issue,
            message: str = None) -> bool:
        """Submit an issue to the communication system."""
        if self.communication:
            self.communication.submit(
                message=message or issue.description,
                message_type=MessageTypes.ISSUE.value,
                source_id=issue.task_id,
                payload=issue.dict()
            )
            return True
        return False

    def _prep_inputs(self, input_keys: list) -> dict[str, any]:
        """Prepare inputs for chain"""
        resource_dict = {}
        inputs = {}
        objective = ""
        for key in input_keys:
            resource_dict[key] = self.resources.get(key, None)

        resources = "\n - ".join([f"{key}: {value}" for key, value in resource_dict.items()]) \
            if resource_dict else "None"

        if "resources" in self.agent_executor.agent.input_keys:
            inputs["resources"] = resources
        else:
            objective += (
                "For your task you have the following knowledge resources from previous work available.\n" \
                f"RESOURCES:\n - {resources}\n\n"
            )

        objective += f"OBJECTIVE: {self.task.description}\n"

        if "feedback" in self.resources:
            objective += "\n\nREMARKS: " + self.resources["feedback"]

        return {**inputs, "input": objective}

    ################################
    #  Callbacks
    ################################

    @property
    def callback_name(self):
        return f"[Task Manager Role: {self.role}] Task: {self.task.name}"

    def on_execution_start(self, run_manager: CallbackManagerForChainRun):
        """print current context within task tree and start message"""
        if self.task_storage is not None:
            task_context = self.task_storage.repr_current_context(self.task.id)
            run_manager.on_text(f"\nCURRENT CONTEXT:\n{task_context}\n\n")
        run_manager.on_text(f"starting:\n\n")
        run_manager.on_text(f"{self.task.colored_card_str()}\n\n")

    def on_execution_end(self, output: str, run_manager: CallbackManagerForChainRun):
        """print current context within task tree and end message"""
        run_manager.on_text(f"finished {self.callback_name}\n with output: {output}\n\n")

    def on_execution_error(self, message: str, run_manager: CallbackManagerForChainRun):
        """print current context within task tree and error message"""
        run_manager.on_text(f"error while executing {self.callback_name}\nError: {message}\n\n")

    def on_issue(self, issue: Issue, run_manager: CallbackManagerForChainRun):
        """callback for when an issue is raised"""
        run_manager.on_text(
            f"Executing Agent reported an issue {self.callback_name}"
            f"\nIssue: {issue.description}\n"
            "Submitting issue to communication system and updating task status.\n\n"
        )

    def _init_callbacks(self, callbacks) -> CallbackManagerForChainRun:
        """initialize run manager from callbacks and verbose flag"""
        callback_manager = CallbackManager.configure(
            callbacks, self.callbacks, self.verbose
        )
        run_manager = callback_manager.on_chain_start(
            {"name": self.__class__.__name__},
            {}
        )
        return run_manager
