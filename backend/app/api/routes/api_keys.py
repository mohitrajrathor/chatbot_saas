import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_db, get_current_user
from app.core.security import generate_api_key
from app.models.user import User
from app.models.chatbot import Chatbot
from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyResponse

router = APIRouter()


async def _verify_chatbot_ownership(chatbot_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Chatbot:
    statement = select(Chatbot).where(Chatbot.id == chatbot_id, Chatbot.user_id == user_id)
    result = await db.execute(statement)
    chatbot = result.scalars().first()
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    return chatbot


@router.post("/{chatbot_id}/keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def generate_key_for_chatbot(
    chatbot_id: uuid.UUID,
    body: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> APIKeyResponse:
    await _verify_chatbot_ownership(chatbot_id, current_user.id, db)

    plaintext_key, key_hash = generate_api_key()
    api_key_obj = APIKey(
        chatbot_id=chatbot_id,
        user_id=current_user.id,
        key_name=body.key_name,
        key_hash=key_hash,
    )
    db.add(api_key_obj)
    await db.commit()
    await db.refresh(api_key_obj)

    response = APIKeyResponse.model_validate(api_key_obj)
    response.plaintext_key = plaintext_key
    return response


@router.get("/{chatbot_id}/keys", response_model=list[APIKeyResponse])
async def list_keys_for_chatbot(
    chatbot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[APIKeyResponse]:
    await _verify_chatbot_ownership(chatbot_id, current_user.id, db)

    statement = select(APIKey).where(APIKey.chatbot_id == chatbot_id)
    result = await db.execute(statement)
    return list(result.scalars().all())


@router.delete("/{chatbot_id}/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    chatbot_id: uuid.UUID,
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    await _verify_chatbot_ownership(chatbot_id, current_user.id, db)

    statement = select(APIKey).where(APIKey.id == key_id, APIKey.chatbot_id == chatbot_id)
    result = await db.execute(statement)
    api_key_obj = result.scalars().first()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found"
        )

    api_key_obj.is_active = False
    db.add(api_key_obj)
    await db.commit()
