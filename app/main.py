# RAG based chatbot saas app
from sqlmodel import SQLModel
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.db import engine
from app.models.models import Chatbot, User, Message, Platform
from app.api.auth import router as auth_router


######## Table creation on startup ########
@asynccontextmanager
async def lifespan(app: FastAPI):
    # create tables 
    SQLModel.metadata.create_all(engine, checkfirst=True)

    yield

# app init
app = FastAPI(lifespan=lifespan)



############### ROUTES #################

# Register routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

######## Other Important routes ########
# health check
@app.get("/health")
def greet():
    '''health check route'''
    return {
        "msg" : "health ok!"
    }


############# setup frontend ###########
app.mount("/", StaticFiles(directory="app/ui/dist", html=True), name="frontend")