import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    chatbot_id: uuid.UUID = Field(foreign_key="chatbots.id", index=True, nullable=False)
    filename: Optional[str] = Field(default=None)
    source_url: Optional[str] = Field(default=None)
    file_type: str = Field(nullable=False)  # 'pdf' | 'docx' | 'txt' | 'url'
    size_bytes: int = Field(default=0, nullable=False)
    status: str = Field(default="pending", nullable=False)  # 'pending' | 'processing' | 'ready' | 'failed'
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
