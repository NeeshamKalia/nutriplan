"""Authentication routes — register, login, refresh, logout, me."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_dietitian
from app.models.dietitian import Dietitian
from app.schemas.auth import (
    AuthResponse,
    DietitianProfileUpdate,
    DietitianResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    WhatsAppSetupRequest,
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
    return auth_service._build_dietitian_response(dietitian)


@router.put("/me", response_model=DietitianResponse)
async def update_me(
    data: DietitianProfileUpdate,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Update the current dietitian's practice profile."""
    return await auth_service.update_profile(db, dietitian, data)


@router.put("/me/whatsapp", response_model=DietitianResponse)
async def setup_whatsapp(
    data: WhatsAppSetupRequest,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Configure WhatsApp Business API credentials for this dietitian."""
    return await auth_service.setup_whatsapp(db, dietitian, data)
