import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON, DateTime


class Chatbot(SQLModel, table=True):
    __tablename__ = "chatbots"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    name: str = Field(nullable=False)
    instructions: str = Field(default="You are a helpful AI assistant.", nullable=False)
    access_type: str = Field(default="public", nullable=False)  # 'public' | 'restricted'
    allowed_emails: Optional[list[str]] = Field(default=[], sa_column=Column(JSON))
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
