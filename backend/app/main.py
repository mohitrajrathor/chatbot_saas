import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.database import engine
import app.models  # Register SQLModel metadata

from app.api.routes.auth import router as auth_router
from app.api.routes.chatbots import router as chatbots_router
from app.api.routes.api_keys import router as api_keys_router
from app.api.routes.documents import router as documents_router
from app.api.routes.chat import router as chat_router
from app.api.routes.eval import router as eval_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create extension and database tables on startup if not already created
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response


# Include API Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(chatbots_router, prefix=f"{settings.API_V1_STR}/chatbots", tags=["Chatbots"])
app.include_router(api_keys_router, prefix=f"{settings.API_V1_STR}/chatbots", tags=["API Keys"])
app.include_router(documents_router, prefix=f"{settings.API_V1_STR}/chatbots", tags=["Documents"])
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(eval_router, prefix=f"{settings.API_V1_STR}/chatbots", tags=["Evaluation"])


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "project": settings.PROJECT_NAME}