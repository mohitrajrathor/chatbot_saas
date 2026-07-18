# database init and session maker
from sqlmodel import SQLModel, create_engine, Session
from app.core.configs import settings

engine = create_engine(settings.DATABASE_URL, echo=True)

def get_db_session():
    '''
    initiaze an database session
    '''
    with Session(engine) as session:
        yield session

