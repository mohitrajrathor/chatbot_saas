import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.chatbot import Chatbot
from app.models.document import Document
from app.models.chunk import Chunk
from app.schemas.chatbot import ChatbotCreate, ChatbotUpdate, ChatbotResponse

router = APIRouter()


@router.post("", response_model=ChatbotResponse, status_code=status.HTTP_201_CREATED)
async def create_chatbot(
    body: ChatbotCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatbotResponse:
    chatbot = Chatbot(
        user_id=current_user.id,
        name=body.name,
        instructions=body.instructions,
        access_type=body.access_type,
        allowed_emails=body.allowed_emails,
    )
    db.add(chatbot)
    await db.commit()
    await db.refresh(chatbot)
    return chatbot


@router.get("", response_model=list[ChatbotResponse])
async def list_chatbots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[ChatbotResponse]:
    statement = select(Chatbot).where(Chatbot.user_id == current_user.id, Chatbot.is_active == True)
    result = await db.execute(statement)
    return list(result.scalars().all())


@router.get("/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    chatbot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatbotResponse:
    statement = select(Chatbot).where(Chatbot.id == chatbot_id, Chatbot.user_id == current_user.id)
    result = await db.execute(statement)
    chatbot = result.scalars().first()

    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    return chatbot


@router.put("/{chatbot_id}", response_model=ChatbotResponse)
async def update_chatbot(
    chatbot_id: uuid.UUID,
    body: ChatbotUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ChatbotResponse:
    statement = select(Chatbot).where(Chatbot.id == chatbot_id, Chatbot.user_id == current_user.id)
    result = await db.execute(statement)
    chatbot = result.scalars().first()

    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )

    if body.name is not None:
        chatbot.name = body.name
    if body.instructions is not None:
        chatbot.instructions = body.instructions
    if body.access_type is not None:
        chatbot.access_type = body.access_type
    if body.allowed_emails is not None:
        chatbot.allowed_emails = body.allowed_emails
    if body.is_active is not None:
        chatbot.is_active = body.is_active

    db.add(chatbot)
    await db.commit()
    await db.refresh(chatbot)
    return chatbot


@router.delete("/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chatbot(
    chatbot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    statement = select(Chatbot).where(Chatbot.id == chatbot_id, Chatbot.user_id == current_user.id)
    result = await db.execute(statement)
    chatbot = result.scalars().first()

    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )

    # Clean up associated vector chunks, documents, and chatbot
    await db.execute(delete(Chunk).where(Chunk.chatbot_id == chatbot_id))
    await db.execute(delete(Document).where(Document.chatbot_id == chatbot_id))
    await db.delete(chatbot)
    await db.commit()
