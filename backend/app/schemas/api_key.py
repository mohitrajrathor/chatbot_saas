import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class APIKeyCreate(BaseModel):
    key_name: str = Field(min_length=1, max_length=100)


class APIKeyResponse(BaseModel):
    id: uuid.UUID
    chatbot_id: uuid.UUID
    key_name: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None
    plaintext_key: str | None = None

    model_config = ConfigDict(from_attributes=True)
