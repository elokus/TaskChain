# TaskChain

TaskChain is a robust and efficient solution built upon the LangChain framework. It leverages LangChain's strengths, addressing the complexities associated with tasks and tool management in agent-based models. TaskChain focuses on breaking down larger goals into manageable pipelines, with each pipeline comprising a series of tasks executed by responsible agents.

## Key Features

- **Hierarchical Task Structure:** TaskChain features a well-structured hierarchy of tasks, which include Projects, Pipelines, Tasks, Issues, and Subtasks. This allows the system to deal with both complex projects involving multiple milestones and simpler standalone projects.
- **Decomposer:** This component breaks down tasks into manageable subtasks, resulting in a tree structure of task objects. It allows for both sequential and iterative breakdowns, providing flexibility in project management.
- **Task Management System:** TaskChain includes ProjectManager, PipelineManager, and TaskManager, which serve to execute tasks efficiently. Built upon the BaseTaskManager, these components provide a robust communication system and a default execution logic.
- **Kanban Board Integration:** TaskChain integrates with the Kanban Boards (at this point only Trello is supported), a web-based project management tool. This allows users to visualize the progress of their projects and manage tasks in a more intuitive way.

## Quickstart

Before you start, ensure you have the latest version of LangChain installed. If not, you can install it with pip:

```bash
pip install --upgrade langchain
```
Once you've installed LangChain, you can install TaskChain directly from GitHub. Here's how:

### (Option 1): Install TaskChain from PyPI
Install the project (ensure you have a Python environment set up):
```bash
pip install taskchain
```

### (Option 2): Install TaskChain from GitHub
Clone the repository:
```bash
Copy code
git clone https://github.com/yourusername/TaskChain.git
```
Navigate into the cloned repository:
```bash
Copy code
cd TaskChain
```
Install the project (ensure you have a Python environment set up):
```bash
Copy code
pip install .
```
Now, you're all set to use TaskChain! Refer to the Usage section to get started.

## Usage

To help you get started, we've provided some examples in the form of Jupyter notebooks:

1. [Decomposer - Break Down a Task into Pipelines](https://github.com/elokus/TaskChain/blob/master/docs/showcase/break_down_task.ipynb):
   This notebook illustrates how you can use TaskChain's Decomposer to break down complex tasks into manageable
   pipelines.
2. [Run a Pipeline Manager](https://github.com/elokus/TaskChain/blob/master/docs/showcase/showcase-pipeline.ipynb): This
   notebook guides you through the process of setting up and running a Pipeline Manager, one of the key features of
   TaskChain.

## Contributing

We welcome contributions! Please see our contributing guide for more details.

## License

TaskChain is open source software licensed under the [MIT license](LICENSE).

