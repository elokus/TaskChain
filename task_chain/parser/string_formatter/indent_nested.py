"""Format nested objects to a string with indentations."""
from __future__ import annotations
from typing import Union
from pydantic import BaseModel
import string


def _list_to_str(ls: list) -> str:
    return str(ls).replace("[", "").replace("]", "")


def _get_indent(d: Union[dict, list], i: int = 0) -> int:
    if isinstance(d, list):
        i += 1
        _i = []
        for v in d:
            if isinstance(v, dict):
                _i.append(_get_indent(v))
            elif isinstance(v, list):
                _i.append(_get_indent(v))
        if _i:
            i += max(_i)
    else:
        i += 1
        _i = []
        for k, v in d.items():
            if isinstance(v, dict):
                _i.append(_get_indent(v))
            elif isinstance(v, list):
                _i.append(_get_indent(v))
        if _i:
            i += max(_i)
    return i


def _is_item(d: dict):
    if len(d.keys()) > 2:
        return True
    if len(d.keys()) == 2 and "name" in d.keys():
        return True
    return False


def _keys_to_list(d: dict) -> list:
    result = []
    for k, v in d.items():
        result.append(k)
        if isinstance(v, dict):
            for key, value in v.items():
                result.append(key)
                if isinstance(value, dict):
                    result.extend(_keys_to_list(value))
    return result


def _get_nesting_item_keys(
        dict_object: dict,
) -> dict:
    nested_keys = {}
    for key, value in dict_object.items():
        if isinstance(value, dict):
            if _is_item(value):
                nested_keys[key] = _get_nesting_item_keys(value)
        if isinstance(value, list):
            _nested_list_keys = []
            for v in value:
                if isinstance(v, dict):
                    if _is_item(v):
                        _nested_list_keys.append(_get_nesting_item_keys(v))
            if _nested_list_keys:
                _nested_list_keys = list(_nested_list_keys)
                _nested_list_keys = [(item, _get_indent(item)) for item in _nested_list_keys]
                max_indent_keys = [
                    item[0] for item in _nested_list_keys if item[1] == max(_nested_list_keys, key=lambda x: x[1])[1]
                ]
                nested_keys[key] = max_indent_keys[0]
    return nested_keys


def get_nested_keys(dict_object: dict) -> list:
    nested_keys = _get_nesting_item_keys(dict_object)
    return _keys_to_list(nested_keys)


def format_nested_list(
        nested_list,
        level=1,
        list_keys: list = None,
        drop: list[str] = None,
        max_depth: int = 3) -> str:
    formatted_str = ""

    indent = level * 4

    abc = list(string.ascii_lowercase)

    for i, item in enumerate(nested_list):
        if level < 2:
            bullet_str = "- "
        elif level == 2:
            bullet_str = f"{i}. "
        else:
            bullet_str = f"{abc[i]}. "

        if isinstance(item, dict):
            formatted_str += format_nested_dict(
                item, level, title_bullet_str=bullet_str, list_keys=list_keys, drop=drop, max_depth=max_depth
            )
        else:
            formatted_str += " " * indent + bullet_str + str(item) + "\n"
    return formatted_str


def format_nested_dict(
        nested_dict: dict,
        level: int = 1,
        title_bullet_str: str = "",
        list_keys: list = None,
        drop: list[str] = None,
        max_depth: int = 3
) -> str:

    list_keys = list_keys or get_nested_keys(nested_dict)
    title_key = list(nested_dict.keys())[0]

    indent = level * 4
    title_indent = 0 if level == 1 else indent

    bullet_str = "- "
    formatted_str = ""

    for key, value in nested_dict.items():
        if drop is not None and key in drop:
            continue
        elif key == title_key:
            formatted_str += " " * title_indent + title_bullet_str + str(value) + ":\n"
            if level >= max_depth:
                return formatted_str
        else:
            if isinstance(value, dict):
                if key in list_keys:
                    formatted_str += format_nested_dict(
                        value, level=level+1, list_keys=list_keys, drop=drop, max_depth=max_depth
                    )
                else:
                    formatted_str += " " * indent + bullet_str + key.capitalize() + ": "
                    formatted_str += _list_to_str(list(value.keys())) + "\n"
            elif isinstance(value, list):
                if key in list_keys:
                    formatted_str += " " * indent + bullet_str + key.capitalize() + ":\n"
                    formatted_str += format_nested_list(
                        value, level=level+1, list_keys=list_keys, drop=drop, max_depth=max_depth
                    )
                else:
                    formatted_str += " " * indent + bullet_str + key.capitalize() + ": "
                    formatted_str += _list_to_str(value) + "\n"
            else:
                formatted_str += " " * indent + bullet_str + key.capitalize() + ": " + str(value) + "\n"
    if level == 1:
        formatted_str += "\n"
    return formatted_str


def format_nested_object(
        nested_object: Union[dict, list, BaseModel, str],
        drop: list[str] = None,
        max_depth: int = 2
) -> str:
    if isinstance(nested_object, dict):
        if len(nested_object) > 1:
            return format_nested_dict(nested_object, drop=drop, max_depth=max_depth)
        else:
            key = list(nested_object.keys())[0]
            formatted_str = f"# {key.capitalize()}:\n"
            formatted_str += format_nested_object(
                nested_object[key], drop=drop, max_depth=max_depth
            )
            return formatted_str
    elif isinstance(nested_object, list):
        return format_nested_list(nested_object, drop=drop, max_depth=max_depth)
    elif isinstance(nested_object, BaseModel):
        return format_nested_list(nested_object.dict(), drop=drop, max_depth=max_depth)

    return nested_object


if __name__ == "__main__":

    # Adjusted nested_data to have the nested pipeline as a separate item
    nested_data = [
        {
            'pipeline': 'Skill Assessment and Enhancement',
            'input': ['objective', 'fullstack programming skills'],
            'output': ['skill assessment report', 'skill improvement decomposer'],
            'pipeline_tasks': [
                {'name': 'Research available programming skill assessment tools', 'agent': 'ResearchAgent'},
                {'name': 'Select appropriate programming skill assessment tool', 'agent': 'DecisionAgent'}
            ]
        },
        {
            'pipeline': 'Scaling Business',
            'input': ['market research'],
            'output': ['performance evaluation'],
            'pipeline_tasks': [
                {'name': 'Customer Needs Identification', 'agent': 'ResearchAgent'},
                {'name': 'New Product Development', 'agent': 'DesignAgent'},
                {'name': 'Marketing Strategy Creation', 'agent': 'MarketingAgent'},
                {'name': 'New Product Launch', 'agent': 'SalesAgent'},
                {'name': 'Performance Evaluation', 'agent': 'DecisionAgent'}
            ]
        }
    ]

    data = {'pipelines': [{'name': 'Data collection pipeline', 'description': 'Pipeline for collecting data from various sources.', 'input': ['Objective'], 'output': ['Collected data'], 'tasks': [{'name': 'Web research', 'description': 'Perform web research to collect data.', 'agent': 'ResearchAgent', 'input': ['Objective'], 'output': ['Collected data']}, {'name': 'Scientific paper research', 'description': 'Perform scientific paper research to collect data.', 'agent': 'ScientificResearchAgent', 'input': ['Objective'], 'output': ['Collected data']}, {'name': 'Revision', 'description': 'Revise collected data for accuracy and completeness.', 'agent': 'RevisionAgent', 'input': ['Collected data'], 'output': ['Revised data']}]}, {'name': 'Data cleaning and preprocessing pipeline', 'description': 'Pipeline for cleaning and preprocessing collected data.', 'input': ['Revised data'], 'output': ['Preprocessed data'], 'tasks': [{'name': 'Data cleaning', 'description': 'Clean collected data.', 'agent': 'NLPAgent', 'input': ['Revised data'], 'output': ['Cleaned data']}, {'name': 'Data preprocessing', 'description': 'Preprocess cleaned data for analysis.', 'agent': 'CodeInteractionAgent', 'input': ['Cleaned data'], 'output': ['Preprocessed data']}]}, {'name': 'Data analysis pipeline', 'description': 'Pipeline for analyzing preprocessed data.', 'input': ['Preprocessed data'], 'output': ['Insights and conclusions'], 'tasks': [{'name': 'Research', 'description': 'Perform additional research to support data analysis.', 'agent': 'ResearchAgent', 'input': ['Preprocessed data'], 'output': ['Additional research data']}, {'name': 'Data analysis', 'description': 'Analyze preprocessed data using artificial intelligence techniques.', 'agent': 'ArtificialIntelligenceAgent', 'input': ['Preprocessed data', 'Additional research data'], 'output': ['Analyzed data']}, {'name': 'Insights and conclusions', 'description': 'Draw insights and conclusions from analyzed data.', 'agent': 'RevisionAgent', 'input': ['Analyzed data'], 'output': ['Insights and conclusions']}]}, {'name': 'Report and presentation creation', 'description': 'Pipeline for creating a report and presentation based on analyzed data.', 'input': ['Insights and conclusions'], 'output': ['Report', 'Presentation'], 'tasks': [{'name': 'Generate general concepts', 'description': 'Generate general concepts based on analyzed data.', 'agent': 'ArtificialIntelligenceAgent', 'input': ['Insights and conclusions'], 'output': ['General concepts']}, {'name': 'Proofread and summarize', 'description': 'Proofread and summarize report.', 'agent': 'NLPAgent', 'input': ['General concepts'], 'output': ['Summarized report']}, {'name': 'Review and revise', 'description': 'Review and revise report for accuracy and completeness.', 'agent': 'RevisionAgent', 'input': ['Summarized report'], 'output': ['Revised report']}, {'name': 'Create report', 'description': 'Create a report based on analyzed data.', 'agent': 'CodeInteractionAgent', 'input': ['Revised report'], 'output': ['Report']}, {'name': 'Create presentation', 'description': 'Create a presentation based on analyzed data.', 'agent': 'CodeInteractionAgent', 'input': ['General concepts'], 'output': ['Presentation']}]}]}

    print(format_nested_object(data, drop=["description"], max_depth=2))
