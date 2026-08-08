from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.core.db import get_db_session
from app.models.models import User
from app.utils import (
    get_user,
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from pydantic import BaseModel, EmailStr

router = APIRouter()


# Pydantic schemas for request validation and response serialization
class UserSignup(BaseModel):
    email: EmailStr
    password: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_admin: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(data: UserSignup, session: Session = Depends(get_db_session)):
    """
    Register a new user with email and password.
    Checks if the email is already in use.
    """
    existing_user = get_user(session, data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_password = get_password_hash(data.password)
    
    new_user = User(
        email=data.email,
        password=hashed_password,
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return TokenResponse(access_token=create_access_token(data={"sub": new_user.email}), token_type="bearer")



@router.post("/login", response_model=TokenResponse)
def login(data: UserLoginRequest, session: Session = Depends(get_db_session)):
    """
    Authenticate a user and return a JWT access token.
    """
    user = get_user(session, data.email)
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    return TokenResponse(access_token=create_access_token(data={"sub": user.email}), token_type="bearer")


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """
    Get details of the currently authenticated user.
    """
    return current_user


@router.post("/logout")
def logout():
    """
    Logout the user (client-side action for JWT).
    """
    return {"detail": "Successfully logged out"}
