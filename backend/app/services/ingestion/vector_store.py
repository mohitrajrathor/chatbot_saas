import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete
from app.models.chunk import Chunk
from app.core.config import settings


async def upsert_chunks(
    db: AsyncSession,
    chunks_text: list[str],
    embeddings: list[list[float]],
    chatbot_id: uuid.UUID,
    document_id: uuid.UUID,
    source: str
) -> None:
    chunk_objects = [
        Chunk(
            chatbot_id=chatbot_id,
            document_id=document_id,
            chunk_index=idx,
            content=text,
            embedding=emb,
            source=source,
        )
        for idx, (text, emb) in enumerate(zip(chunks_text, embeddings))
    ]
    db.add_all(chunk_objects)
    await db.commit()


async def delete_by_document(db: AsyncSession, document_id: uuid.UUID) -> None:
    statement = delete(Chunk).where(Chunk.document_id == document_id)
    await db.execute(statement)
    await db.commit()


async def delete_by_chatbot(db: AsyncSession, chatbot_id: uuid.UUID) -> None:
    statement = delete(Chunk).where(Chunk.chatbot_id == chatbot_id)
    await db.execute(statement)
    await db.commit()


async def query_similar_chunks(
    db: AsyncSession,
    query_embedding: list[float],
    chatbot_id: uuid.UUID,
    top_k: int | None = None
) -> list[dict]:
    k = top_k or settings.TOP_K

    # Cosine distance order using pgvector <=> operator
    statement = (
        select(Chunk)
        .where(Chunk.chatbot_id == chatbot_id)
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(k)
    )
    result = await db.execute(statement)
    chunks = result.scalars().all()

    return [
        {
            "content": chunk.content,
            "source": chunk.source,
            "chunk_index": chunk.chunk_index,
            "document_id": str(chunk.document_id),
        }
        for chunk in chunks
    ]
