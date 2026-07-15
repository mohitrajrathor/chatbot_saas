from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App General Settings
    PROJECT_NAME: str = Field(default="Chatbot SaaS", description="The name of the application")
    ENVIRONMENT: str = Field(default="development", description="Application environment (development, staging, production)")
    DEBUG: bool = Field(default=True, description="Enable or disable debug mode")
    API_V1_STR: str = Field(default="/api/v1", description="API route prefix")
    
    # Database Settings
    # Matches database_url in .env because case_sensitive=False
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/chatbot_saas",
        description="Database connectio.n URL"
    )
    
    # Security/Authentication Settings
    SECRET_KEY: str = Field(
        default="change_this_to_a_secure_random_key_for_production",
        description="Secret key for signing JWT tokens"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 8,  # 8 days
        description="JWT access token lifetime in minutes"
    )
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:8000", "http://localhost:3000"],
        description="List of origins allowed to make CORS requests"
    )
    
    # AI / LLM Integration Settings
    OPENAI_API_KEY: str | None = Field(default=None, description="OpenAI API Key")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama local API base URL")
    
    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Allows lowercase env keys (like database_url) to bind to uppercase fields
        extra="ignore"
    )

# Instantiate settings to be imported across the application
settings = Settings()
