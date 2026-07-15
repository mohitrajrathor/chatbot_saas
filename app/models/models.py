from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from pydantic import EmailStr



class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, nullable=False)
    password: str = Field(nullable=False)
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Chatbot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    instructions: str = Field(nullable=False)

    user_id: int | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Platform(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    webhook_url: str = Field(nullable=False)
    secret_key: str = Field(nullable=False)    

    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str = Field(nullable=False)
    response: str = Field(nullable=False)
    status: str = Field(default="pending", nullable=False)
    source_platform: str = Field(default="web", nullable=False)

    chatbot_id: int | None = Field(default=None, foreign_key="chatbot.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))