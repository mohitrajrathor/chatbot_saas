import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    storage_used_bytes: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
