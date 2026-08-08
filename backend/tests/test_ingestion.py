import uuid
import pytest
from app.services.ingestion.extractor import extract_txt, extract
from app.services.ingestion.chunker import chunk_text
from app.services.ingestion.embedder import get_embedder
from app.services.ingestion.vector_store import upsert_chunks, query_similar_chunks, delete_by_document
from app.core.database import AsyncSessionLocal
from app.models.chatbot import Chatbot
from app.models.document import Document
from app.models.user import User


def test_txt_extractor():
    sample_bytes = b"Hello world! This is a test document."
    extracted = extract_txt(sample_bytes)
    assert extracted == "Hello world! This is a test document."


def test_chunker_splitting():
    long_text = "Sentence one. " * 100
    chunks = chunk_text(long_text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 250 for c in chunks)


def test_embedder_generation():
    embedder = get_embedder()
    texts = ["Sample text query 1", "Sample text query 2"]
    embeddings = embedder.embed_texts(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384  # bge-small-en-v1.5 is 384 dimensions


@pytest.mark.asyncio
async def test_vector_store_upsert_and_similarity_query():
    async with AsyncSessionLocal() as db:
        # Create user & chatbot
        user = User(email=f"vec_user_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass")
        db.add(user)
        await db.commit()
        await db.refresh(user)

        chatbot = Chatbot(user_id=user.id, name="Vector Bot")
        db.add(chatbot)
        await db.commit()
        await db.refresh(chatbot)

        doc = Document(chatbot_id=chatbot.id, filename="rag.txt", file_type="txt", size_bytes=100)
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        embedder = get_embedder()
        chunks = [
            "Retrieval Augmented Generation (RAG) combines search with LLMs.",
            "PostgreSQL with pgvector allows fast vector similarity search.",
            "FastAPI is a modern web framework for Python."
        ]
        embeddings = embedder.embed_texts(chunks)

        # Upsert chunks
        await upsert_chunks(
            db=db,
            chunks_text=chunks,
            embeddings=embeddings,
            chatbot_id=chatbot.id,
            document_id=doc.id,
            source="rag.txt"
        )

        # Query similar chunks
        query_text = "Tell me about vector search in Postgres"
        query_vector = embedder.embed_query(query_text)
        results = await query_similar_chunks(db=db, query_embedding=query_vector, chatbot_id=chatbot.id, top_k=2)

        assert len(results) >= 1
        assert "pgvector" in results[0]["content"]

        # Clean up
        await delete_by_document(db, doc.id)
