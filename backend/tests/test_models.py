import uuid
from app.models.user import User
from app.models.chatbot import Chatbot
from app.models.document import Document
from app.models.api_key import APIKey
from app.models.eval import EvalRun, EvalResult
from app.models.chunk import Chunk


def test_user_model_instantiation():
    user = User(email="test@example.com", password_hash="hashed_pw")
    assert isinstance(user.id, uuid.UUID)
    assert user.email == "test@example.com"
    assert user.storage_used_bytes == 0
    assert user.is_active is True


def test_chatbot_model_instantiation():
    user_id = uuid.uuid4()
    chatbot = Chatbot(user_id=user_id, name="Test Bot", instructions="Be helpful.")
    assert isinstance(chatbot.id, uuid.UUID)
    assert chatbot.user_id == user_id
    assert chatbot.access_type == "public"
    assert chatbot.allowed_emails == []


def test_document_model_instantiation():
    chatbot_id = uuid.uuid4()
    doc = Document(chatbot_id=chatbot_id, filename="doc.pdf", file_type="pdf", size_bytes=1024)
    assert isinstance(doc.id, uuid.UUID)
    assert doc.chatbot_id == chatbot_id
    assert doc.status == "pending"


def test_api_key_model_instantiation():
    user_id = uuid.uuid4()
    chatbot_id = uuid.uuid4()
    key = APIKey(chatbot_id=chatbot_id, user_id=user_id, key_name="default", key_hash="sha256_hash")
    assert isinstance(key.id, uuid.UUID)
    assert key.is_active is True


def test_eval_models_instantiation():
    chatbot_id = uuid.uuid4()
    eval_run = EvalRun(chatbot_id=chatbot_id)
    assert isinstance(eval_run.id, uuid.UUID)
    assert eval_run.status == "pending"

    result = EvalResult(
        eval_run_id=eval_run.id,
        question="What is RAG?",
        ground_truth="Retrieval Augmented Generation",
    )
    assert isinstance(result.id, uuid.UUID)
    assert result.question == "What is RAG?"


def test_chunk_model_instantiation():
    chatbot_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    embedding = [0.1] * 384
    chunk = Chunk(
        chatbot_id=chatbot_id,
        document_id=doc_id,
        chunk_index=0,
        content="Sample text",
        embedding=embedding,
        source="doc.pdf"
    )
    assert isinstance(chunk.id, uuid.UUID)
    assert len(chunk.embedding) == 384
