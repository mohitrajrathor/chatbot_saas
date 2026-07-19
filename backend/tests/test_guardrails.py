import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.chatbot import Chatbot
from app.models.api_key import APIKey
from app.core.security import generate_api_key
from app.services.guardrails.classifier import (
    GuardrailsClassifier,
    UNSAFE_INPUT_MESSAGE,
    UNSAFE_OUTPUT_MESSAGE,
)


def test_guardrails_classifier_safe_and_unsafe_detection():
    classifier = GuardrailsClassifier(threshold=0.5)

    # Mock HF pipeline returning safe label
    mock_safe_pipeline = MagicMock(return_value=[{"label": "LABEL_0", "score": 0.99}])
    classifier._classifier = mock_safe_pipeline
    assert classifier.is_safe("Hello world, clean text.") is True

    # Mock HF pipeline returning toxic label
    mock_toxic_pipeline = MagicMock(return_value=[{"label": "toxic", "score": 0.95}])
    classifier._classifier = mock_toxic_pipeline
    assert classifier.is_safe("Toxic text content") is False


@pytest.mark.asyncio
async def test_input_guardrail_blocking_in_chat_endpoint():
    async with AsyncSessionLocal() as db:
        user = User(email=f"guard_user_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass")
        db.add(user)
        await db.commit()
        await db.refresh(user)

        chatbot = Chatbot(user_id=user.id, name="Guard Bot")
        db.add(chatbot)
        await db.commit()
        await db.refresh(chatbot)

        plaintext_key, key_hash = generate_api_key()
        api_key_obj = APIKey(chatbot_id=chatbot.id, user_id=user.id, key_name="K", key_hash=key_hash)
        db.add(api_key_obj)
        await db.commit()

        # Mock classifier to reject input
        mock_classifier = MagicMock()
        mock_classifier.is_safe.side_effect = lambda text: False if "toxic" in text.lower() else True

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "Normal response"

        with patch("app.api.routes.chat.get_guardrails_classifier", return_value=mock_classifier), \
             patch("app.api.routes.chat.get_llm_provider", return_value=mock_llm):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                headers = {"Authorization": f"Bearer {plaintext_key}"}
                response = await ac.post(
                    f"/api/v1/chat/{chatbot.id}",
                    headers=headers,
                    json={"message": "This is toxic content"}
                )
                assert response.status_code == 200
                data = response.json()
                assert data["answer"] == UNSAFE_INPUT_MESSAGE
                assert data["sources"] == []


@pytest.mark.asyncio
async def test_output_guardrail_blocking_in_chat_endpoint():
    async with AsyncSessionLocal() as db:
        user = User(email=f"guard_user2_{uuid.uuid4().hex[:6]}@example.com", password_hash="pass")
        db.add(user)
        await db.commit()
        await db.refresh(user)

        chatbot = Chatbot(user_id=user.id, name="Guard Bot 2")
        db.add(chatbot)
        await db.commit()
        await db.refresh(chatbot)

        plaintext_key, key_hash = generate_api_key()
        api_key_obj = APIKey(chatbot_id=chatbot.id, user_id=user.id, key_name="K2", key_hash=key_hash)
        db.add(api_key_obj)
        await db.commit()

        # Mock classifier to reject LLM output
        mock_classifier = MagicMock()
        mock_classifier.is_safe.side_effect = lambda text: False if "bad_output" in text.lower() else True

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "This contains bad_output text"

        with patch("app.api.routes.chat.get_guardrails_classifier", return_value=mock_classifier), \
             patch("app.api.routes.chat.get_llm_provider", return_value=mock_llm):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                headers = {"Authorization": f"Bearer {plaintext_key}"}
                response = await ac.post(
                    f"/api/v1/chat/{chatbot.id}",
                    headers=headers,
                    json={"message": "Clean question"}
                )
                assert response.status_code == 200
                data = response.json()
                assert data["answer"] == UNSAFE_OUTPUT_MESSAGE
