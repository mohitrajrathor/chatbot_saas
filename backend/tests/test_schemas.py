import pytest
from pydantic import ValidationError
from app.schemas.auth import RegisterRequest, LoginRequest
from app.schemas.chatbot import ChatbotCreate, ChatbotUpdate
from app.schemas.chat import ChatRequest, ChatResponse


def test_register_request_validation():
    valid = RegisterRequest(email="user@example.com", password="securepassword")
    assert valid.email == "user@example.com"

    with pytest.raises(ValidationError):
        RegisterRequest(email="not-an-email", password="123")


def test_chatbot_create_validation():
    cb = ChatbotCreate(name="Support Bot", access_type="restricted", allowed_emails=["a@b.com"])
    assert cb.name == "Support Bot"
    assert cb.allowed_emails == ["a@b.com"]


def test_chat_request_response():
    req = ChatRequest(query="Hello bot")
    assert req.query == "Hello bot"

    res = ChatResponse(answer="Hello human!", sources=["doc1.pdf"])
    assert res.answer == "Hello human!"
    assert res.sources == ["doc1.pdf"]
