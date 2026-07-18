import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, DateTime
from pgvector.sqlalchemy import Vector


class Chunk(SQLModel, table=True):
    __tablename__ = "chunks"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    chatbot_id: uuid.UUID = Field(foreign_key="chatbots.id", index=True, nullable=False)
    document_id: uuid.UUID = Field(foreign_key="documents.id", index=True, nullable=False)
    chunk_index: int = Field(nullable=False)
    content: str = Field(nullable=False)
    embedding: list[float] = Field(sa_column=Column(Vector(384), nullable=False))
    source: str = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
