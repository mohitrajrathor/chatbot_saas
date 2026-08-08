import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ChatbotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    instructions: str = Field(default="You are a helpful AI assistant.")
    access_type: str = Field(default="public")  # 'public' | 'restricted'
    allowed_emails: list[str] = Field(default_factory=list)


class ChatbotUpdate(BaseModel):
    name: str | None = None
    instructions: str | None = None
    access_type: str | None = None
    allowed_emails: list[str] | None = None
    is_active: bool | None = None


class ChatbotResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    instructions: str
    access_type: str
    allowed_emails: list[str] = Field(default_factory=list)
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
