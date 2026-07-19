import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.chatbot import Chatbot
from app.models.eval import EvalRun, EvalResult
from app.schemas.eval import EvalRunResponse, EvalRunDetailResponse, EvalResultResponse
from app.services.eval.eval_parser import parse_and_validate_eval_csv
from app.tasks.eval_task import run_eval_task

router = APIRouter()


async def _verify_chatbot_ownership(chatbot_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Chatbot:
    statement = select(Chatbot).where(Chatbot.id == chatbot_id, Chatbot.user_id == user_id)
    result = await db.execute(statement)
    chatbot = result.scalars().first()
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    return chatbot


@router.post("/{chatbot_id}/eval", response_model=EvalRunResponse, status_code=status.HTTP_201_CREATED)
async def create_eval_run(
    chatbot_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> EvalRunResponse:
    await _verify_chatbot_ownership(chatbot_id, current_user.id, db)

    file_bytes = await file.read()
    test_items = parse_and_validate_eval_csv(file_bytes)

    # 1. Create EvalRun
    eval_run = EvalRun(
        chatbot_id=chatbot_id,
        status="pending"
    )
    db.add(eval_run)
    await db.commit()
    await db.refresh(eval_run)

    # 2. Create EvalResult rows
    results_objects = [
        EvalResult(
            eval_run_id=eval_run.id,
            question=item["question"],
            ground_truth=item["ground_truth"],
        )
        for item in test_items
    ]
    db.add_all(results_objects)
    await db.commit()

    # 3. Dispatch Celery task (or inline fallback during test)
    try:
        run_eval_task.delay(str(eval_run.id))
    except Exception:
        from app.tasks.eval_task import _process_eval_run
        import asyncio
        asyncio.create_task(_process_eval_run(eval_run.id))

    return eval_run


@router.get("/{chatbot_id}/eval", response_model=list[EvalRunResponse])
async def list_eval_runs(
    chatbot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[EvalRunResponse]:
    await _verify_chatbot_ownership(chatbot_id, current_user.id, db)

    statement = select(EvalRun).where(EvalRun.chatbot_id == chatbot_id)
    result = await db.execute(statement)
    return list(result.scalars().all())


@router.get("/{chatbot_id}/eval/{run_id}", response_model=EvalRunDetailResponse)
async def get_eval_run_detail(
    chatbot_id: uuid.UUID,
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> EvalRunDetailResponse:
    await _verify_chatbot_ownership(chatbot_id, current_user.id, db)

    # Fetch EvalRun
    run_stmt = select(EvalRun).where(EvalRun.id == run_id, EvalRun.chatbot_id == chatbot_id)
    run_res = await db.execute(run_stmt)
    eval_run = run_res.scalars().first()

    if not eval_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eval run not found"
        )

    # Fetch results
    rows_stmt = select(EvalResult).where(EvalResult.eval_run_id == run_id)
    rows_res = await db.execute(rows_stmt)
    results = list(rows_res.scalars().all())

    # Calculate averages
    faith_scores = [r.faithfulness for r in results if r.faithfulness is not None]
    rel_scores = [r.answer_relevancy for r in results if r.answer_relevancy is not None]
    rec_scores = [r.context_recall for r in results if r.context_recall is not None]
    prec_scores = [r.context_precision for r in results if r.context_precision is not None]

    avg_faith = round(sum(faith_scores) / len(faith_scores), 3) if faith_scores else None
    avg_rel = round(sum(rel_scores) / len(rel_scores), 3) if rel_scores else None
    avg_rec = round(sum(rec_scores) / len(rec_scores), 3) if rec_scores else None
    avg_prec = round(sum(prec_scores) / len(prec_scores), 3) if prec_scores else None

    return EvalRunDetailResponse(
        id=eval_run.id,
        chatbot_id=eval_run.chatbot_id,
        status=eval_run.status,
        created_at=eval_run.created_at,
        completed_at=eval_run.completed_at,
        average_faithfulness=avg_faith,
        average_answer_relevancy=avg_rel,
        average_context_recall=avg_rec,
        average_context_precision=avg_prec,
        results=[EvalResultResponse.model_validate(r) for r in results]
    )
