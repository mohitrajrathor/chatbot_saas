import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_db, get_chatbot_from_api_key
from app.core.security import decode_token
from app.models.user import User
from app.models.chatbot import Chatbot
from app.schemas.chat import ChatRequest, ChatResponse, ChatSource
from app.services.rag.retriever import retrieve
from app.services.rag.prompt_builder import build_prompt
from app.services.rag.llm_provider import get_llm_provider
from app.services.guardrails.classifier import (
    get_guardrails_classifier,
    UNSAFE_INPUT_MESSAGE,
    UNSAFE_OUTPUT_MESSAGE,
)

router = APIRouter()


async def _execute_rag_pipeline(
    db: AsyncSession,
    chatbot: Chatbot,
    message: str
) -> ChatResponse:
    # 0. Input Guardrail Check
    classifier = get_guardrails_classifier()
    if not classifier.is_safe(message):
        return ChatResponse(answer=UNSAFE_INPUT_MESSAGE, sources=[])

    # 1. Retrieve top-k context chunks
    chunks = await retrieve(db, query_text=message, chatbot_id=chatbot.id)

    # 2. Build system and user prompt
    system_prompt, user_prompt = build_prompt(
        chatbot_instructions=chatbot.instructions,
        context_chunks=chunks,
        user_query=message
    )

    # 3. Call LLM provider
    llm = get_llm_provider()
    answer = await llm.complete(prompt=user_prompt, system_instruction=system_prompt)

    # 4. Output Guardrail Check
    if not classifier.is_safe(answer):
        return ChatResponse(answer=UNSAFE_OUTPUT_MESSAGE, sources=[])

    # 5. Format sources
    sources = [
        ChatSource(
            content=c.get("content", ""),
            source=c.get("source", "Document"),
            score=c.get("score")
        )
        for c in chunks
    ]

    return ChatResponse(answer=answer, sources=sources)


@router.post("/{chatbot_id}", response_model=ChatResponse)
async def chat_with_api_key(
    chatbot_id: uuid.UUID,
    body: ChatRequest,
    chatbot: Chatbot = Depends(get_chatbot_from_api_key),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    if chatbot.id != chatbot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API Key does not belong to this chatbot"
        )
    if not chatbot.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chatbot is inactive"
        )

    return await _execute_rag_pipeline(db, chatbot, body.message)


@router.post("/web/{chatbot_id}", response_model=ChatResponse)
async def chat_web_widget(
    chatbot_id: uuid.UUID,
    body: ChatRequest,
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    # Fetch chatbot
    statement = select(Chatbot).where(Chatbot.id == chatbot_id)
    result = await db.execute(statement)
    chatbot = result.scalars().first()

    if not chatbot or not chatbot.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found or inactive"
        )

    # Access control verification
    if chatbot.access_type == "restricted":
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for restricted chatbot"
            )
        token = authorization.split(" ")[1]
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Check user email against allowed_emails
        user_stmt = select(User).where(User.id == uuid.UUID(user_id))
        user_res = await db.execute(user_stmt)
        user = user_res.scalars().first()

        allowed_list = chatbot.allowed_emails or []
        if not user or user.email not in allowed_list:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Your email is not authorized for this chatbot"
            )

    return await _execute_rag_pipeline(db, chatbot, body.message)
