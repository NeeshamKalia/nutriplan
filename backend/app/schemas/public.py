"""Schemas for public landing page endpoints."""

from pydantic import BaseModel, Field


class IntakeSubmit(BaseModel):
    """New client intake form from a dietitian's landing page."""

    full_name: str = Field(..., min_length=1, max_length=255)
    whatsapp_number: str = Field(..., min_length=10, max_length=20)
    email: str | None = None
    age: int | None = Field(None, ge=1, le=120)
    primary_goal: str | None = Field(None, max_length=100)
    dietary_type: str | None = Field(None, max_length=50)
    notes: str | None = Field(None, max_length=2000)


class IntakeResponse(BaseModel):
    """Confirmation after intake submission."""

    message: str
    client_id: str
