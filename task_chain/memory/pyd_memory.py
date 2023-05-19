from typing import Any, Dict, List
from langchain.schema import BaseMemory
import json


class SharedPydanticMemory(BaseMemory):
    """Save LLM Chain results to memory and try to use json loads before saving to memory.
    """
    memories: Dict[str, Any] = dict()

    @property
    def memory_variables(self) -> List[str]:
        return list(self.memories.keys())

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        return {**self.memories}

    def _load_memory_variables(self, inputs: Dict[str, Any], input_keys: list[str]) -> Dict[str, str]:
        for key in input_keys:
            if key not in inputs:
                if key not in self.memories:
                    raise ValueError(f"Missing input key {key} in memory and inputs")
                inputs[key] = self.memories[key]
        return self.memories

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save output to memory."""

        for key in outputs:
            value = self.format_value(outputs[key], key)
            self.memories[key] = value

    def get(self, key: str, default=None) -> Any:
        """Get a key from memory."""
        return self.memories.get(key, default)

    def has(self, key: str) -> bool:
        """Check if memory has a key."""
        return key in self.memories

    def add(self, **kwargs):
        for k, v in kwargs.items():
            self.memories[k] = self.format_value(v, k)

    def format_value(self, value: Any, key: str = None) -> str:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except:
                if key is not None:
                    print(f"Could not execute json.loads() for key: {key}")
        return value



    def clear(self) -> None:
        """Nothing to clear, got a memory like a vault."""
        pass