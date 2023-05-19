from __future__ import annotations

from typing import Any, Dict, List

from langchain.schema import BaseMemory


class SharedTaskMemory(BaseMemory):
    """Simple memory for storing context or other bits of information that shouldn't
    ever change between prompts.
    """

    memories: Dict[str, Any] = dict()
    histories: Dict[str, Any] = dict()
    history_key: str = "agent_chat_history"

    @property
    def memory_variables(self) -> List[str]:
        return list(self.memories.keys())

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        return {**self.memories, self.history_key:self.histories}

    def _load_memory_variables(self, inputs: Dict[str, Any], input_keys: list[str]) -> Dict[str, str]:
        for key in input_keys:
            if key not in inputs:
                if key not in self.memories:
                    raise ValueError(f"Missing input key {key} in memory and inputs")
                inputs[key] = self.memories[key]
        return self.memories

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context to memory."""
        for key in outputs:
            print(f"Saving {key} to memory with value: {outputs[key]}")
            self.memories[key] = outputs[key]

    def add_key(self, key: str, value: Any) -> None:
        """Add a key to memory."""
        self.memories[key] = value

    def add_history(self, agent: str, value: Any) -> None:
        """Add a key to memory."""
        self.histories[agent] = value

    def load_history(self, agent_name: str) -> Any:
        """Add a key to memory."""
        if agent_name not in self.histories:
            return {self.history_key: ""}
        return {self.history_key: self.histories[agent_name]}

    def get(self, key: str, default=None) -> Any:
        """Get a key from memory."""
        return self.memories.get(key, default)

    def has(self, key: str) -> bool:
        """Check if memory has a key."""
        return key in self.memories

    def add(self, **kwargs):
        for k, v in kwargs.items():
            self.memories[k] = v



    def clear(self) -> None:
        """Nothing to clear, got a memory like a vault."""
        pass