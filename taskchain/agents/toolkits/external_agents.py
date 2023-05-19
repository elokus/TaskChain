import yaml
from langchain.agents.agent_toolkits import (
    create_pandas_dataframe_agent,
    create_csv_agent,
    create_python_agent,
    create_json_agent,
)
from langchain.agents.agent_toolkits.openapi.planner import create_openapi_agent
from langchain.agents.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain.requests import RequestsWrapper
from langchain.tools.python.tool import PythonAstREPLTool, PythonREPLTool
from pandas import DataFrame

from taskchain.llm import get_llm_by_name

llm = get_llm_by_name("gpt-3.5-turbo")


class AgentLoader:
    def __init__(self, model_name: str="gpt-3.5-turbo", verbose: bool=True):
        self.model_name = model_name
        self.llm = get_llm_by_name(model_name)
        self.verbose = verbose

    def required_input_variables(self, toolkit_name: str):
        """Get the required input variables for a toolkit."""
        return

    def create_pandas_dataframe_agent(self, df: DataFrame, *args, **kwargs):
        return create_pandas_dataframe_agent(self.llm, df, *args, **kwargs)

    def create_csv_agent(self, *args, **kwargs):
        return create_csv_agent(self.llm, *args, **kwargs)

    def create_python_agent(self, *args, **kwargs):
        return create_python_agent(self.llm, *args, **kwargs)

    def create_openapi_agent(self, *args, **kwargs):
        return create_openapi_agent(self.llm, *args, **kwargs)

    def create_json_agent(self, *args, **kwargs):
        return create_json_agent(self.llm, *args, **kwargs)


def create_openapi_agent_from_yaml(filepath: str, headers: dict = None, model_name: str = "gpt-4", **kwargs):
    """Create an OpenAPI agent from a YAML file containing OpenAPI Spec and optional an auhtentication header."""
    with open(filepath) as f:
        raw_spec = yaml.load(f, Loader=yaml.Loader)
    spec = reduce_openapi_spec(raw_spec)
    request_wrapper = RequestsWrapper(headers=headers)
    return create_openapi_agent(spec, request_wrapper, get_llm_by_name(model_name), **kwargs)


def create_csv_agent_from_filepath(filepath: str, model_name="gpt-3.5-tubro", **kwargs):
    """Create a CSV agent from a filepath."""
    return create_csv_agent(get_llm_by_name(model_name), filepath, pandas_kwargs=kwargs)


def create_python_agent_ast(model_name: str="gpt-3.5-turbo", **kwargs):
    """Create a Python agent from a REPL."""
    tool = PythonAstREPLTool()
    return create_python_agent(llm=get_llm_by_name(model_name), tool=tool, **kwargs)


def create_python_agent_default(model_name: str="gpt-3.5-turbo", **kwargs):
    """Create a Python agent from a REPL."""
    tool = PythonREPLTool()
    return create_python_agent(llm=get_llm_by_name(model_name), tool=tool, **kwargs)