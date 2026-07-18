import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime


class EvalRun(SQLModel, table=True):
    __tablename__ = "eval_runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    chatbot_id: uuid.UUID = Field(foreign_key="chatbots.id", index=True, nullable=False)
    status: str = Field(default="pending", nullable=False)  # 'pending' | 'running' | 'complete' | 'failed'
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )


class EvalResult(SQLModel, table=True):
    __tablename__ = "eval_results"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    eval_run_id: uuid.UUID = Field(foreign_key="eval_runs.id", index=True, nullable=False)
    question: str = Field(nullable=False)
    ground_truth: str = Field(nullable=False)
    generated_answer: Optional[str] = Field(default=None)
    faithfulness: Optional[float] = Field(default=None)
    answer_relevancy: Optional[float] = Field(default=None)
    context_recall: Optional[float] = Field(default=None)
    context_precision: Optional[float] = Field(default=None)
