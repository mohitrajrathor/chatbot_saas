from typing import Optional, Union
from pydantic import BaseModel, Field, ConfigDict, model_validator


class ChatSource(BaseModel):
    content: str = ""
    source: str
    score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    message: str = Field(default="")

    @property
    def query(self) -> str:
        return self.message

    @model_validator(mode="before")
    @classmethod
    def populate_message(cls, data: dict) -> dict:
        if isinstance(data, dict):
            if "query" in data and not data.get("message"):
                data["message"] = data["query"]
        return data

    model_config = ConfigDict(from_attributes=True)


# Alias for backward compatibility
ChatQueryRequest = ChatRequest


class ChatResponse(BaseModel):
    answer: str
    sources: list[Union[ChatSource, str]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
