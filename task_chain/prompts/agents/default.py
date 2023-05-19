ROLE_PREFIX = """You are {agent_name} Assistant. """

TOOL_PREFIX ="""You have access to the following tools:"""

PREFIX = ROLE_PREFIX + "\n" + TOOL_PREFIX

FORMAT_INSTRUCTIONS = """Use the following format for your responses:

Goal: the goal you must achieve
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question"""
SUFFIX = """
If you have problems achieving your goal, need other resources or tools, or have any other problems you can report an issue by responding with:
Issue: <your issue>
If you achieved the defined goal return your final answer in the following format:
Final Answer: <answer>'
{agent_chat_history}

Goal: {goal}
Thought:{agent_scratchpad}"""
