##############################
# Breakdown Task Prompt
##############################

BREAK_DOWN = """
Breakdown the following task into a sequence of subtasks. Define the input and output keys of each task as lowercase strings.
ROOT TASK: 
{context}

{schema}

Additional instructions:
Create a flat list as shown above do not break subtasks down further.
Try to break down into as few subtasks as possible.
{remarks}
"""

_SUMMARY_SCHEMA = """
Return your respond as string in the following format without any introducing or describing text:

Name of Root Task:
    - Name of Subtask 1
    - Name of Subtask 2
    ...
    - Name of Subtask n
    
"""

##############################
# Extend Task Prompt
##############################

EXTEND_TASKS = """
Based on the following sequence of subtasks, define the input and output keys of each task as lowercase strings with underscores and
add a description for each subtask.
TASK LIST: 
{context}

{schema}

Additional instructions:
Do not define the root task only the subtasks.
{remarks}
"""

##############################
# Root Task Prompt
##############################

PARENT_TASK_PROMPT = """
Based on the following sequence of subtasks, specify the parent task by defining the input and output keys of each task as lowercase strings with undersores.
TASK LIST:
{context}

{schema}

Additional instructions:
Do not define the subtasks only the parent task.
{remarks}
"""

##############################
# Break Down Chunk Prompt
##############################

BEAK_DOWN_CHUNK_PROMPT = """
Breakdown the following task into a sequence of subtasks. Define the input and output keys of each task as lowercase strings.
Reduce the sequence of subtasks by identifying and removing redundant subtasks. 
Consider the previous and next task when creating subtasks and defining the input and output keys.
CONTEXT:
{context}

{schema}

Additional instructions:
{remarks}
"""


_SUMMARY_CHUNK_SCHEMA = """
Return your respond as string in the following format without any introducing or describing text:

Name of Root Task:
    - Name of Subtask 1, Inputs: ..., Outputs: ...
    - Name of Subtask 2, Inputs: ..., Outputs: ...
    ...
    - Name of Subtask n, Inputs: ..., Outputs: ...

"""


##############################
# Revision Task Prompt
##############################

REVISION_TASK_PROMPT = """
For the following project decomposer, revise the sequence of tasks and subtasks. 
Reduce the sequence of subtasks by identifying and removing redundant subtasks.
TASK LIST:
{context}

{schema}

Additional instructions:
{remarks}
"""

##############################
# Assignment Task Prompt
##############################

ASSIGN_TASK_PROMPT = """
For the following task select the Agent that fits best for successfully executing the task.
You should select a more specialized Agent over a more general one. 
{context}

{schema}

Additional instructions:
{remarks}
"""

##############################
# Assign & Revise Task Prompt
##############################

ASSIGN_REVISE_TASK_PROMPT = """
For the following project decomposer, revise the sequence of tasks and subtasks so that the tasks are assigned to the most competent Agent.
TASK LIST:
{context}

You can assign the following Agents:
{agents}

{schema}

Additional instructions:
You can change the subtasks so that they fit the Agents competencies.
{remarks}
"""
