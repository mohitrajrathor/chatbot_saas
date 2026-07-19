import asyncio
import uuid
from datetime import datetime, timezone
from sqlmodel import select

from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.chatbot import Chatbot
from app.models.eval import EvalRun, EvalResult
from app.api.routes.chat import _execute_rag_pipeline
from app.services.rag.retriever import retrieve
from app.services.eval.eval_engine import evaluate_rag_triplet


async def _process_eval_run(eval_run_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        statement = select(EvalRun).where(EvalRun.id == eval_run_id)
        result = await db.execute(statement)
        eval_run = result.scalars().first()

        if not eval_run:
            return

        try:
            eval_run.status = "running"
            db.add(eval_run)
            await db.commit()

            cb_stmt = select(Chatbot).where(Chatbot.id == eval_run.chatbot_id)
            cb_res = await db.execute(cb_stmt)
            chatbot = cb_res.scalars().first()

            if not chatbot:
                eval_run.status = "failed"
                db.add(eval_run)
                await db.commit()
                return

            rows_stmt = select(EvalResult).where(EvalResult.eval_run_id == eval_run_id)
            rows_res = await db.execute(rows_stmt)
            results_rows = list(rows_res.scalars().all())

            for item in results_rows:
                # 1. Retrieve chunks
                chunks = await retrieve(db, query_text=item.question, chatbot_id=chatbot.id)

                # 2. Execute RAG pipeline
                rag_res = await _execute_rag_pipeline(db, chatbot, item.question)

                # 3. Evaluate triplet
                metrics = evaluate_rag_triplet(
                    question=item.question,
                    ground_truth=item.ground_truth,
                    generated_answer=rag_res.answer,
                    context_chunks=chunks
                )

                # 4. Save result
                item.generated_answer = rag_res.answer
                item.faithfulness = metrics["faithfulness"]
                item.answer_relevancy = metrics["answer_relevancy"]
                item.context_recall = metrics["context_recall"]
                item.context_precision = metrics["context_precision"]
                db.add(item)

            eval_run.status = "complete"
            eval_run.completed_at = datetime.now(timezone.utc)
            db.add(eval_run)
            await db.commit()

        except Exception:
            eval_run.status = "failed"
            db.add(eval_run)
            await db.commit()


@celery_app.task(name="tasks.run_eval")
def run_eval_task(eval_run_id_str: str) -> None:
    eval_run_id = uuid.UUID(eval_run_id_str)
    asyncio.run(_process_eval_run(eval_run_id))
