"""Pydantic schemas for protocol templates."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MacroSplit(BaseModel):
    protein_pct: int | None = None
    carbs_pct: int | None = None
    fat_pct: int | None = None


class ProtocolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    target_conditions: list[str] | None = None
    target_goals: list[str] | None = None
    calorie_range_min: int | None = None
    calorie_range_max: int | None = None
    macro_split: MacroSplit | dict[str, Any] | None = None
    general_guidelines: str | None = None
    preferred_foods: list[str] | None = None
    avoided_foods: list[str] | None = None
    sample_plan: dict[str, Any] | None = None
    is_active: bool = True


class ProtocolUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    target_conditions: list[str] | None = None
    target_goals: list[str] | None = None
    calorie_range_min: int | None = None
    calorie_range_max: int | None = None
    macro_split: MacroSplit | dict[str, Any] | None = None
    general_guidelines: str | None = None
    preferred_foods: list[str] | None = None
    avoided_foods: list[str] | None = None
    sample_plan: dict[str, Any] | None = None
    is_active: bool | None = None


class ProtocolResponse(BaseModel):
    id: str
    dietitian_id: str
    name: str
    description: str | None = None
    target_conditions: list[str] | None = None
    target_goals: list[str] | None = None
    calorie_range_min: int | None = None
    calorie_range_max: int | None = None
    macro_split: dict[str, Any] | None = None
    general_guidelines: str | None = None
    preferred_foods: list[str] | None = None
    avoided_foods: list[str] | None = None
    sample_plan: dict[str, Any] | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProtocolListResponse(BaseModel):
    protocols: list[ProtocolResponse]
    total: int


class SavePlanAsProtocolRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    general_guidelines: str | None = None
    target_conditions: list[str] | None = None
    target_goals: list[str] | None = None
