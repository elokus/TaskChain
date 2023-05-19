from langchain.agents.agent_toolkits.base import BaseToolkit
from langchain.tools import BaseTool
from langchain.tools.file_management.list_dir import ListDirectoryTool
from langchain.tools.file_management.read import ReadFileTool
from langchain.tools.file_management.write import WriteFileTool
from langchain.tools.python.tool import PythonREPLTool

from taskchain.config import Config
from taskchain.tools.code_interaction import GitHubSearchTool, CodeRetrievalTool

CFG = Config()

_CODE_TOOLS = {
    tool_cls.__fields__["name"].default: tool_cls
    for tool_cls in [GitHubSearchTool, CodeRetrievalTool, PythonREPLTool]
}

_FILE_TOOLS = {
    tool_cls.__fields__["name"].default: tool_cls
    for tool_cls in [WriteFileTool, ReadFileTool, ListDirectoryTool]
}


class CodeToolkit(BaseToolkit):
    verbose: bool = True

    def get_tools(self) -> list[BaseTool]:
        """Get the tools in the toolkit."""
        tools: list[BaseTool] = []
        for tool in _CODE_TOOLS.keys():
            tool_cls = _CODE_TOOLS[tool]
            tools.append(tool_cls(verbose=self.verbose))
        for tool in _FILE_TOOLS.keys():
            tool_cls = _CODE_TOOLS[tool]
            tools.append(tool_cls(verbose=self.verbose, root_dir=CFG.file_creation_dir))
        return tools