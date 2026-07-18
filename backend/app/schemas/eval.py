import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EvalRunResponse(BaseModel):
    id: uuid.UUID
    chatbot_id: uuid.UUID
    status: str
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EvalResultResponse(BaseModel):
    id: uuid.UUID
    eval_run_id: uuid.UUID
    question: str
    ground_truth: str
    generated_answer: str | None = None
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_recall: float | None = None
    context_precision: float | None = None

    model_config = ConfigDict(from_attributes=True)
