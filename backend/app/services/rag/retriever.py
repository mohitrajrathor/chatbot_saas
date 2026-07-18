import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ingestion.embedder import get_embedder
from app.services.ingestion.vector_store import query_similar_chunks


async def retrieve(
    db: AsyncSession,
    query_text: str,
    chatbot_id: uuid.UUID,
    top_k: int | None = None
) -> list[dict]:
    embedder = get_embedder()
    query_vector = embedder.embed_query(query_text)
    return await query_similar_chunks(db, query_vector, chatbot_id, top_k=top_k)
