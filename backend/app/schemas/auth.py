"""Pydantic schemas for authentication requests and responses."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Dietitian registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2)
    phone: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one number")
        return v


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
    photo_url: str | None = None
    bio: str | None = None
    specializations: list[str] | None = None
    qualifications: str | None = None
    practice_name: str | None = None
    has_whatsapp_setup: bool = False

    model_config = ConfigDict(from_attributes=True)


class DietitianProfileUpdate(BaseModel):
    """Update dietitian practice profile."""

    full_name: str | None = Field(None, min_length=2, max_length=255)
    phone: str | None = Field(None, max_length=20)
    photo_url: str | None = None
    bio: str | None = Field(None, max_length=5000)
    specializations: list[str] | None = None
    qualifications: str | None = Field(None, max_length=1000)
    practice_name: str | None = Field(None, max_length=255)


class WhatsAppSetupRequest(BaseModel):
    """Configure per-dietitian WhatsApp Business credentials."""

    whatsapp_phone_number_id: str = Field(..., min_length=1, max_length=50)
    whatsapp_business_account_id: str | None = Field(None, max_length=50)
    whatsapp_access_token: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    """Authentication response with tokens and profile."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    dietitian: DietitianResponse
