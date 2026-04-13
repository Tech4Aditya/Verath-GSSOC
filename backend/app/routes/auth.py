import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.auth import (
    authenticate_user,
    create_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class UserCredentials(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(credentials: UserCredentials):
    username = credentials.username.lower().strip()
    success = await create_user(username, credentials.password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    return {"message": "User created successfully", "username": username}


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserCredentials):
    username_clean = credentials.username.lower().strip()
    username = await authenticate_user(username_clean, credentials.password)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(username),
        refresh_token=create_refresh_token(username),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    """
    Exchange a valid refresh token for a new access + refresh token pair.
    Refresh token rotation: old refresh token is invalidated on use.
    """
    username = verify_refresh_token(body.refresh_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(username),
        refresh_token=create_refresh_token(username),  # rotate
    )
