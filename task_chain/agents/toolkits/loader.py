from langchain.tools import BaseTool

import task_chain.agents.toolkits as kits

def NAME_TOOLKITS_MAP():
    return {
        #"research_toolkit": kits.research_toolkit.ResearchToolkit,
        #"code_toolkit": kits.code_toolkit.CodeToolkit,
        "file_toolkit": kits.external_toolkits.FileManagementToolkit,
        "open_api_toolkit": kits.external_toolkits.OpenAPIToolkit,
        "playwright_toolkit": kits.external_toolkits.PlayWrightBrowserToolkit,
        "power_bi_toolkit": kits.external_toolkits.PowerBIToolkit,
        "sql_toolkit": kits.external_toolkits.SQLDatabaseToolkit,
        "vector_store_toolkit": kits.external_toolkits.VectorStoreToolkit,
        "vector_store_router_toolkit": kits.external_toolkits.VectorStoreRouterToolkit,
        "json_toolkit": kits.external_toolkits.JsonToolkit,
        "nla_toolkit": kits.external_toolkits.NLAToolkit,
        "requests_toolkit": kits.external_toolkits.RequestsToolkit,
    }


def load_toolkit_by_name(name: str) -> list[BaseTool]:
    """Load tools from a toolkit."""
    name_toolkit_map = NAME_TOOLKITS_MAP()
    if name not in name_toolkit_map:
        raise ValueError(f"Toolkit {name} not found.")
    loader = name_toolkit_map[name]()
    return loader.get_tools()