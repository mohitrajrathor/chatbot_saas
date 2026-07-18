import uuid
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.rag.prompt_builder import build_prompt
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.chatbot import Chatbot
from app.models.api_key import APIKey
from app.core.security import generate_api_key, create_access_token


def test_prompt_builder_formatting():
    chunks = [
        {"content": "Python is a programming language.", "source": "py.txt"},
        {"content": "FastAPI builds web APIs rapidly.", "source": "docs.pdf"}
    ]
    sys_prompt, user_prompt = build_prompt("You are a helpful assistant.", chunks, "What is Python?")

    assert "You are a helpful assistant." in sys_prompt
    assert "Source: py.txt" in user_prompt
    assert "FastAPI builds web APIs rapidly." in user_prompt
    assert "QUESTION:\nWhat is Python?" in user_prompt


def test_prompt_builder_empty_context():
    sys_prompt, user_prompt = build_prompt("Instructions", [], "Unknown query")
    assert "[No relevant documents found]" in user_prompt


@pytest.mark.asyncio
async def test_chat_api_key_and_web_flow():
    async with AsyncSessionLocal() as db:
        # Create user & chatbot
        user = User(email=f"chat_user_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass")
        db.add(user)
        await db.commit()
        await db.refresh(user)

        chatbot = Chatbot(
            user_id=user.id,
            name="Chat Test Bot",
            instructions="Answer accurately.",
            access_type="public"
        )
        db.add(chatbot)
        await db.commit()
        await db.refresh(chatbot)

        # Create API key
        plaintext_key, key_hash = generate_api_key()
        api_key_obj = APIKey(
            chatbot_id=chatbot.id,
            user_id=user.id,
            key_name="Test Key",
            key_hash=key_hash
        )
        db.add(api_key_obj)
        await db.commit()

        # Mock LLM provider completion
        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "Python is a high-level programming language."

        with patch("app.api.routes.chat.get_llm_provider", return_value=mock_llm):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                # 1. Chat via API key
                key_headers = {"Authorization": f"Bearer {plaintext_key}"}
                key_res = await ac.post(
                    f"/api/v1/chat/{chatbot.id}",
                    headers=key_headers,
                    json={"message": "What is Python?"}
                )
                assert key_res.status_code == 200
                key_data = key_res.json()
                assert key_data["answer"] == "Python is a high-level programming language."

                # 2. Public Web Chat
                web_res = await ac.post(
                    f"/api/v1/chat/web/{chatbot.id}",
                    json={"message": "Tell me about Python"}
                )
                assert web_res.status_code == 200
                assert web_res.json()["answer"] == "Python is a high-level programming language."


@pytest.mark.asyncio
async def test_restricted_chatbot_access_control():
    async with AsyncSessionLocal() as db:
        user = User(email=f"allowed_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass")
        db.add(user)
        await db.commit()
        await db.refresh(user)

        chatbot = Chatbot(
            user_id=user.id,
            name="Restricted Bot",
            access_type="restricted",
            allowed_emails=[user.email]
        )
        db.add(chatbot)
        await db.commit()
        await db.refresh(chatbot)

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "Restricted answer"

        with patch("app.api.routes.chat.get_llm_provider", return_value=mock_llm):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                # Unauthorized request (no token) -> 401
                unauth_res = await ac.post(f"/api/v1/chat/web/{chatbot.id}", json={"message": "Hi"})
                assert unauth_res.status_code == 401

                # Authorized allowed user -> 200
                user_token = create_access_token({"sub": str(user.id)})
                auth_headers = {"Authorization": f"Bearer {user_token}"}
                auth_res = await ac.post(
                    f"/api/v1/chat/web/{chatbot.id}",
                    headers=auth_headers,
                    json={"message": "Hi"}
                )
                assert auth_res.status_code == 200
                assert auth_res.json()["answer"] == "Restricted answer"
