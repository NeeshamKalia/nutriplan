"""Pydantic schemas for authentication requests and responses."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Dietitian registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2)
    phone: str | None = None


class LoginRequest(BaseModel):
    """Dietitian login request."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class DietitianResponse(BaseModel):
    """Public dietitian profile response."""

    id: str
    email: str
    full_name: str
    slug: str
    phone: str | None = None
    specializations: list[str] | None = None
    practice_name: str | None = None
    has_whatsapp_setup: bool = False

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Authentication response with tokens and profile."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    dietitian: DietitianResponse
