import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: uuid.UUID
    chatbot_id: uuid.UUID
    filename: str | None = None
    source_url: str | None = None
    file_type: str
    size_bytes: int
    status: str
    error_message: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
