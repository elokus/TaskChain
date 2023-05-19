from task_chain.prompts.agents import (
    default,
)


_name_to_dict = {
    "default": {
        "prefix": default.PREFIX,
        "suffix": default.SUFFIX,
        "format_instructions": default.FORMAT_INSTRUCTIONS,
    },
}

def _load_prompt_type(prompt_type: str, prompt_name: str) -> str:
    """Load agent prompts by name and type.
    :param prompt_type: The type of prompt to load 'suffix', 'prefix', or 'format_instructions'.
    :param prompt_name: The name of the prompt to load.
    :returns: The prompt as a string.
    """
    return _name_to_dict[prompt_name][prompt_type]

def load_agent_prompt(prompt_specs: dict) -> dict[str, str]:
    """Load agent prompts prefix, suffix and format_instructions from a config dict.
    Example:
        prompt_specs = {"prefix": "default", "suffix": "default", "format_instructions": "default"}
        prompts = load_agent_prompt(prompt_specs)
    """
    prompts = {}
    for prompt_type, prompt_name in prompt_specs.items():
        prompts[prompt_type] = _load_prompt_type(prompt_type, prompt_name)
    return prompts
