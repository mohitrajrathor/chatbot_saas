import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.chatbot import Chatbot
from app.models.document import Document
from app.models.chunk import Chunk
from app.schemas.document import DocumentResponse
from app.tasks.ingest_task import ingest_document_task

MAX_USER_STORAGE_BYTES = 10 * 1024 * 1024  # 10 MB per user
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "url"}

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


@router.post("/{chatbot_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    chatbot_id: uuid.UUID,
    file: Optional[UploadFile] = File(default=None),
    source_url: Optional[str] = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    await _verify_chatbot_ownership(chatbot_id, current_user.id, db)

    if not file and not source_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a file upload or a source_url must be provided"
        )

    if file:
        filename = file.filename or "uploaded_file"
        file_ext = filename.split(".")[-1].lower() if "." in filename else ""
        if file_ext not in ALLOWED_EXTENSIONS or file_ext == "url":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '.{file_ext}'. Allowed: PDF, DOCX, TXT."
            )
        
        contents = await file.read()
        file_size = len(contents)
        file_type = file_ext
    else:
        filename = None
        file_ext = "url"
        file_size = 1024  # Nominal size for URL indexing
        contents = None
        file_type = "url"

    # Enforce 10MB storage limit
    if current_user.storage_used_bytes + file_size > MAX_USER_STORAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Storage limit exceeded (maximum 10 MB per user)"
        )

    doc = Document(
        chatbot_id=chatbot_id,
        filename=filename,
        source_url=source_url,
        file_type=file_type,
        size_bytes=file_size,
        status="pending",
    )
    db.add(doc)

    # Update user storage usage
    current_user.storage_used_bytes += file_size
    db.add(current_user)

    await db.commit()
    await db.refresh(doc)

    # Trigger Celery ingestion task (or process inline if Celery broker unavailable during dev/test)
    try:
        ingest_document_task.delay(str(doc.id), contents)
    except Exception:
        # Fallback to direct async processing if Celery worker is offline during local test runs
        from app.tasks.ingest_task import _process_ingestion
        import asyncio
        asyncio.create_task(_process_ingestion(doc.id, contents))

    return doc


@router.get("/{chatbot_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    chatbot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> list[DocumentResponse]:
    await _verify_chatbot_ownership(chatbot_id, current_user.id, db)

    statement = select(Document).where(Document.chatbot_id == chatbot_id)
    result = await db.execute(statement)
    return list(result.scalars().all())


@router.get("/{chatbot_id}/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    chatbot_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DocumentResponse:
    await _verify_chatbot_ownership(chatbot_id, current_user.id, db)

    statement = select(Document).where(Document.id == doc_id, Document.chatbot_id == chatbot_id)
    result = await db.execute(statement)
    doc = result.scalars().first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return doc


@router.delete("/{chatbot_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    chatbot_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    await _verify_chatbot_ownership(chatbot_id, current_user.id, db)

    statement = select(Document).where(Document.id == doc_id, Document.chatbot_id == chatbot_id)
    result = await db.execute(statement)
    doc = result.scalars().first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Reclaim user storage
    current_user.storage_used_bytes = max(0, current_user.storage_used_bytes - doc.size_bytes)
    db.add(current_user)

    # Delete vector chunks & document record
    await db.execute(delete(Chunk).where(Chunk.document_id == doc_id))
    await db.delete(doc)
    await db.commit()
