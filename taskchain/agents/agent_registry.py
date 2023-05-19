from __future__ import annotations

from typing import Union, Optional

from langchain import SerpAPIWrapper
from langchain.agents import load_tools, initialize_agent
from langchain.agents.types import AgentType
from langchain.prompts import HumanMessagePromptTemplate
from langchain.schema import BaseMemory
from langchain.tools import BaseTool, Tool
from pydantic import BaseModel, Field

from taskchain.agents.toolkits.loader import load_toolkit_by_name
from taskchain.llm import get_basic_llm
from taskchain.prompts.agents.loader import load_agent_prompt
from taskchain.tools.report_issue import IssueReportTool


class AgentConfig(BaseModel):
    """Agent configuration class.

    This class is used to configure an agent.
    """

    name: str
    description: str
    agent_type: Union[str, None] = AgentType.ZERO_SHOT_REACT_DESCRIPTION
    agent_path: Union[str, None] = None
    agent_kwargs: dict = Field(default_factory=dict, description="Additional key word arguments to pass to the underlying agent.")

    toolkit: Optional[str] = Field(defualt=None, description="Name of the toolkit to use for the agent.")
    tools: list[BaseTool] = Field(default_factory=list, description="A list of tools to use for the agent.")
    load_tools: list[str] = Field(default_factory=list, description="A list of tools to load from langchain for the agent.")
    prompt: Optional[dict] = Field(default=None, description="Custom prompt for the agent defined as dict with keys 'prefix', 'suffix', and 'format_instructions'.")

    
DEFAULT_AGENTS = [
    # AgentConfig(
    #     name="ResearchAgent",
    #     description="An Agent useful for performing research on complex or scientific topics.",
    #     toolkit="research_toolkit",
    # ),
    # AgentConfig(
    #     name="DecisionAgent",
    #     description="An Agent useful for making a decision based on a set of information.",
    #     toolkit="decision_toolkit",
    # ),
    AgentConfig(
        name="SearchAgent",
        description="An Agent useful for performing web search on basic questions.",
        tools=[
            Tool(name="Search", func=SerpAPIWrapper().run, description="useful for searching the web for information"),
            IssueReportTool()
        ],
    ),
    AgentConfig(
        name="CodeInteractionAgent",
        description="An Agent useful for generating or interacting with code.",
        toolkit="code_toolkit",
    ),
    # AgentConfig(
    #     name="OpenAPIAgent",
    #     description="An Agent useful for interacting with OpenAPI specification document.",
    #     toolkit="open_api_toolkit",
    # ),
    AgentConfig(
        name="FileManagementAgent",
        description="An Agent useful for interacting with files.",
        toolkit="file_toolkit",
    ),
    # AgentConfig(
    #     name="CSVAgent",
    #     description="An Agent useful for interacting with CSV files.",
    #     toolkit="csv_toolkit",
    # ),
    AgentConfig(
        name="AgentGeneratorAgent",
        description="An Agent useful for generating new Agents based on a description of requirements.",
        toolkit="agent_generator_toolkit",
    )
]

class AgentRegistry:
    """Agent registry class.

    This class is used to register agents and to retrieve them by name.
    """

    def __init__(self, agents: list[AgentConfig] = None, upsert: bool = True):
        """Initialize the registry.
        Args:
            agents: A list of agents to register set or add to register.
            upsert: Whether to update default agents or overwrite with provided agents list.

        """
        self._agents: dict[str, AgentConfig] = {agent.name: agent for agent in DEFAULT_AGENTS}

        if agents is not None:
            agents = {agent.name: agent for agent in agents}
            if upsert:
                self._agents.update(agents)
            else:
                self._agents = agents


    def register(self, agent_config: AgentConfig):
        """Register an agent.

        Args:
            agent (Agent): The agent to register.
        """
        self._agents[agent_config.name] = agent_config

    def get(self, name) -> AgentConfig:
        """Get an agent by name.

        Args:
            name (str): The name of the agent to retrieve.

        Returns:
            Agent: The agent with the specified name.
        """
        agent_config = self._agents.get(name, None)
        if agent_config is None:
            raise KeyError(f"Agent {name} not found.")
        return agent_config

    def load(self, name: str, memory: BaseMemory = None, **kwargs):
        """Load Task Manager by agent name."""
        config = self.get(name)
        tools = self.load_tools_from_config(config)
        custom_prompts = load_agent_prompt(config.prompt) if config.prompt else None

        if "Custom" in config.agent_type:
            return self._load_custom_agent(config, tools, custom_prompts, memory, **kwargs)
        else:
            return self._load_langchain_agent(config, tools, custom_prompts, memory, **kwargs)

    def _load_custom_agent(
            self,
            config: AgentConfig,
            tools: list[BaseTool],
            custom_prompts: dict = None,
            memory: BaseMemory = None,
            **kwargs):
        pass

    @staticmethod
    def _load_langchain_agent(
            config: AgentConfig,
            tools: list[BaseTool],
            custom_prompts: dict = None,
            memory: BaseMemory = None,
            **kwargs):
        """Load a Langchain agent from config."""
        llm = kwargs["llm"] if "llm" in kwargs else get_basic_llm()
        agent_kwargs = config.agent_kwargs

        if "agent_kwargs" in kwargs:
            for k, v in kwargs["agent_kwargs"].items():
                agent_kwargs[k] = v

        if custom_prompts:
            agent_kwargs = {**agent_kwargs, **custom_prompts}
        if memory:
            agent_kwargs = {**agent_kwargs, "memory": memory}

        return initialize_agent(
            tools=tools,
            llm=llm,
            agent=config.agent_type,
            agent_path=config.agent_path,
            agent_kwargs=agent_kwargs,
            **kwargs)

    @staticmethod
    def load_tools_from_config(config: AgentConfig) -> list[BaseTool]:
        tools = []
        if config.toolkit:
            tools = load_toolkit_by_name(config.toolkit)
        if config.load_tools:
            tools.extend(load_tools(config.load_tools))
        if config.tools:
            tools.extend(config.tools)
        if len(tools) == 0:
            raise ValueError("The Agent has no tools available define at least one tool for the agent.")
        return tools

    def get_all(self):
        """Get all registered agents.

        Returns:
            dict: A dictionary of all registered agents.
        """
        return [{"name": agent.name, "description": agent.description} for agent in self._agents.values()]

    def add_tool_to_agent(self, agent_name: str, tool: BaseTool):
        """Add a tool to an agent."""
        agent_config = self.get(agent_name)
        agent_config.tools.append(tool)
        self.register(agent_config)

    def add_resources_to_agent(self, agent_name: str, variable: str, value: str):
        """Add resource prompt to langchain agents.

        Currently only supported with Zero_Shot_React, Chat_Zero_Shot_React, and Structured_Chat_Zero_Shot_React.
        """
        agent_config = self.get(agent_name)
        template = (
            "Based on previous work you have the following knowledge resources "
            "for achieving your current objective.\n"
            "RESOURCES: {resources}"
            )

        if agent_config.agent_type == AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION:
            agent_config.agent_kwargs["memory_prompt"] = [HumanMessagePromptTemplate.from_template(template)]
            agent_config.agent_kwargs["input_variables"] = ["input", "agent_scratchpad", "resources"]

        elif agent_config.agent_type == AgentType.ZERO_SHOT_REACT_DESCRIPTION:
            suffix = (
                "Begin!\n"
                "Objective: {input}\n"
                f"{template}\n"
                "Thought:{agent_scratchpad}"
            )
            agent_config.agent_kwargs["suffix"] = suffix
            agent_config.agent_kwargs["input_variables"] = ["input", "agent_scratchpad", "resources"]

        elif agent_config.agent_type == AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION:
            suffix = (
                f"{template}\n"
                "Begin! Reminder to always use the exact characters `Final Answer` when responding."
            )
            agent_config.agent_kwargs["suffix"] = suffix
            agent_config.agent_kwargs["input_variables"] = ["input", "agent_scratchpad", "resources"]
        else:
            return
        self.register(agent_config)






