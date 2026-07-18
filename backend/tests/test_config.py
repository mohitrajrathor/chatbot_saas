from app.core.config import settings


def test_settings_load_defaults():
    assert settings.PROJECT_NAME == "RAG Chatbot SaaS"
    assert settings.LLM_PROVIDER in ["groq", "nim"]
    assert settings.TOP_K == 5
    assert settings.CHUNK_SIZE == 512
    assert settings.CHUNK_OVERLAP == 50
    assert "http://localhost:5173" in settings.BACKEND_CORS_ORIGINS
