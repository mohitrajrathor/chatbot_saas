from datetime import datetime, timezone
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_async_db
from app.core.security import decode_token, hash_api_key
from app.models.user import User
from app.models.chatbot import Chatbot
from app.models.api_key import APIKey

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_db():
        yield session


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    statement = select(User).where(User.id == user_id)
    result = await db.execute(statement)
    user = result.scalars().first()

    if not user or not user.is_active:
        raise credentials_exception

    return user


async def get_chatbot_from_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> Chatbot:
    invalid_key_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials or not credentials.credentials:
        raise invalid_key_exception

    key_hash = hash_api_key(credentials.credentials)
    statement = select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)
    result = await db.execute(statement)
    api_key_obj = result.scalars().first()

    if not api_key_obj:
        raise invalid_key_exception

    # Update last used timestamp
    api_key_obj.last_used_at = datetime.now(timezone.utc)
    db.add(api_key_obj)
    await db.commit()

    # Query associated chatbot
    cb_statement = select(Chatbot).where(Chatbot.id == api_key_obj.chatbot_id, Chatbot.is_active == True)
    cb_result = await db.execute(cb_statement)
    chatbot = cb_result.scalars().first()

    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated chatbot not found or inactive"
        )

    return chatbot
