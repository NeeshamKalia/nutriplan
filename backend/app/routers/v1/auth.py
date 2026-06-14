"""Authentication routes — register, login, refresh, logout, me."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_dietitian
from app.models.dietitian import Dietitian
from app.schemas.auth import (
    AuthResponse,
    DietitianResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new dietitian account."""
    return await auth_service.register(db, data)


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    return await auth_service.login(db, data)


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a refresh token."""
    return await auth_service.refresh(db, data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Logout by revoking the refresh token."""
    await auth_service.logout(db, data.refresh_token)


@router.get("/me", response_model=DietitianResponse)
async def get_me(dietitian: Dietitian = Depends(get_current_dietitian)):
    """Get the current authenticated dietitian's profile."""
    return DietitianResponse(
        id=str(dietitian.id),
        email=dietitian.email,
        full_name=dietitian.full_name,
        slug=dietitian.slug,
        phone=dietitian.phone,
        specializations=dietitian.specializations,
        practice_name=dietitian.practice_name,
        has_whatsapp_setup=bool(dietitian.whatsapp_phone_number_id),
    )
