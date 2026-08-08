import asyncio
import uuid
from sqlmodel import select
from app.tasks.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.document import Document
from app.services.ingestion.extractor import extract
from app.services.ingestion.chunker import chunk_text
from app.services.ingestion.embedder import get_embedder
from app.services.ingestion.vector_store import upsert_chunks


async def _process_ingestion(document_id: uuid.UUID, file_bytes: bytes | None = None) -> None:
    async with AsyncSessionLocal() as db:
        # Fetch document
        statement = select(Document).where(Document.id == document_id)
        result = await db.execute(statement)
        doc = result.scalars().first()

        if not doc:
            return

        try:
            # Update status to processing
            doc.status = "processing"
            db.add(doc)
            await db.commit()

            source_input = file_bytes if file_bytes else doc.source_url
            if not source_input:
                raise ValueError("No source content or URL available for ingestion")

            # Extract text
            raw_text = extract(source_input, doc.file_type)

            # Chunk text
            chunks = chunk_text(raw_text)

            # Generate embeddings
            embedder = get_embedder()
            embeddings = embedder.embed_texts(chunks)

            # Upsert into pgvector
            source_name = doc.filename or doc.source_url or "document"
            await upsert_chunks(
                db=db,
                chunks_text=chunks,
                embeddings=embeddings,
                chatbot_id=doc.chatbot_id,
                document_id=doc.id,
                source=source_name,
            )

            # Update status to ready
            doc.status = "ready"
            doc.error_message = None
            db.add(doc)
            await db.commit()

        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            db.add(doc)
            await db.commit()


@celery_app.task(name="tasks.ingest_document")
def ingest_document_task(document_id_str: str, file_bytes: bytes | None = None) -> None:
    doc_id = uuid.UUID(document_id_str)
    asyncio.run(_process_ingestion(doc_id, file_bytes))
