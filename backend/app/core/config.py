import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = Field(default="RAG Chatbot SaaS")
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    API_V1_STR: str = Field(default="/api/v1")

    # Security Settings
    SECRET_KEY: str = Field(default="change_this_to_a_secure_random_key_in_production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    ALGORITHM: str = Field(default="HS256")

    # Database Settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/chatbot_saas"
    )
    SYNC_DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/chatbot_saas"
    )

    # Redis Settings
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # LLM Settings
    LLM_PROVIDER: str = Field(default="groq")
    GROQ_API_KEY: str | None = Field(default=None)
    GROQ_MODEL: str = Field(default="llama-3.3-70b-versatile")
    NIM_API_KEY: str | None = Field(default=None)
    NIM_BASE_URL: str = Field(default="https://integrate.api.nvidia.com/v1")
    NIM_MODEL: str = Field(default="meta/llama-3.1-70b-instruct")

    # Embedding & Guardrails
    EMBEDDING_MODEL: str = Field(default="BAAI/bge-small-en-v1.5")
    GUARDRAILS_MODEL: str = Field(default="unitary/toxic-bert")
    GUARDRAILS_THRESHOLD: float = Field(default=0.7)

    # RAG Settings
    TOP_K: int = Field(default=5)
    CHUNK_SIZE: int = Field(default=512)
    CHUNK_OVERLAP: int = Field(default=50)

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:8000", "http://localhost:3000"]
    )

    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
