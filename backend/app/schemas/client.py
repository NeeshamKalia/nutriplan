"""Pydantic schemas for client management."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ClientCreate(BaseModel):
    """Create a new client with health profile."""

    full_name: str = Field(..., min_length=1, max_length=255)
    whatsapp_number: str = Field(..., min_length=10, max_length=20)
    email: str | None = None
    age: int | None = Field(None, ge=1, le=120)
    gender: str | None = None
    height_cm: Decimal | None = Field(None, ge=30, le=300)
    weight_kg: Decimal | None = Field(None, ge=10, le=500)
    target_weight_kg: Decimal | None = Field(None, ge=10, le=500)
    activity_level: str | None = None

    # Health profile
    medical_conditions: list[str] | None = None
    allergies: list[str] | None = None
    food_preferences: list[str] | None = None
    cuisine_preference: str | None = None
    dietary_type: str | None = None

    # Goals & constraints
    primary_goal: str | None = None
    monthly_food_budget_inr: int | None = Field(None, ge=0)
    daily_calorie_target: int | None = Field(None, ge=500, le=10000)
    meals_per_day: int | None = Field(None, ge=1, le=10)
    meal_timing_preferences: dict | None = None

    # Notes
    notes: str | None = None
    lifestyle_notes: str | None = None


class ClientUpdate(BaseModel):
    """Partial update of client profile — all fields optional."""

    full_name: str | None = Field(None, min_length=1, max_length=255)
    whatsapp_number: str | None = Field(None, min_length=10, max_length=20)
    email: str | None = None
    age: int | None = Field(None, ge=1, le=120)
    gender: str | None = None
    height_cm: Decimal | None = Field(None, ge=30, le=300)
    weight_kg: Decimal | None = Field(None, ge=10, le=500)
    target_weight_kg: Decimal | None = Field(None, ge=10, le=500)
    activity_level: str | None = None
    medical_conditions: list[str] | None = None
    allergies: list[str] | None = None
    food_preferences: list[str] | None = None
    cuisine_preference: str | None = None
    dietary_type: str | None = None
    primary_goal: str | None = None
    monthly_food_budget_inr: int | None = Field(None, ge=0)
    daily_calorie_target: int | None = Field(None, ge=500, le=10000)
    meals_per_day: int | None = Field(None, ge=1, le=10)
    meal_timing_preferences: dict | None = None
    notes: str | None = None
    lifestyle_notes: str | None = None


class ClientResponse(BaseModel):
    """Client profile response."""

    id: str
    dietitian_id: str
    full_name: str
    whatsapp_number: str
    email: str | None = None
    age: int | None = None
    gender: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    target_weight_kg: float | None = None
    activity_level: str | None = None
    medical_conditions: list[str] | None = None
    allergies: list[str] | None = None
    food_preferences: list[str] | None = None
    cuisine_preference: str | None = None
    dietary_type: str | None = None
    primary_goal: str | None = None
    monthly_food_budget_inr: int | None = None
    daily_calorie_target: int | None = None
    meals_per_day: int | None = None
    meal_timing_preferences: dict | None = None
    notes: str | None = None
    lifestyle_notes: str | None = None
    status: str = "active"
    archived_at: datetime | None = None
    onboarded_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ClientListResponse(BaseModel):
    """Paginated client list."""

    clients: list[ClientResponse]
    total: int
    limit: int
    offset: int
