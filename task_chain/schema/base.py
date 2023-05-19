from __future__ import annotations
from langchain.callbacks.manager import Callbacks
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, validator, root_validator
from abc import ABC, abstractmethod, ABCMeta
from typing import Optional, Union, Sequence, NamedTuple

from langchain.chains.base import Chain
from langchain import LLMChain
import uuid

class BaseChain(Chain, ABC):
    """Base class for chains with predict and parse functionality like LLM Chains."""
    @abstractmethod
    def predict(self, callbacks: Callbacks = None, **kwargs: any) -> str:
        """Predict method for the chain."""
        pass

    @abstractmethod
    def predict_and_parse(
            self, callbacks: Callbacks = None, **kwargs: any
    ) -> Union[str, list[str], dict[str, any]]:
        """Predict and parse method for the chain."""
        pass

    @abstractmethod
    async def apredict_and_parse(
            self, callbacks: Callbacks = None, **kwargs: any
    ) -> Union[str, list[str], dict[str, str]]:
        pass

    @abstractmethod
    async def aapply_and_parse(
            self, input_list: list[dict[str, any]], callbacks: Callbacks = None
    ) -> Sequence[Union[str, list[str], dict[str, str]]]:
        pass


class BaseIssue(BaseModel):
    description: str
    solution: Optional[str]
    type: Optional[str]


class Issue(BaseIssue):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    type: str = "undefined_issue"
    task_id: str
    status: str = "open"

    def __str__(self):
        return f"{self.type} issue with task {self.task_id}: {self.description}"


class SearchResultItems(NamedTuple):
    url: str
    snippet: str


class Comment(BaseModel):
    id: str
    text: str
    date: str
    status: str = "new"

    @root_validator(pre=True)
    def parse_date(cls, values):
        if "T" in values['date']:
            values['date'] = values['date'].split('T')[0]
        if "text" not in values:
            values['text'] = values['data']['text']
        return values

    def __str__(self):
        return f"{self.text} ({self.date})"
