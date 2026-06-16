"""Strict Pydantic schema for AI-generated meal plan JSON."""

from pydantic import BaseModel, Field


class GeneratedMealItem(BaseModel):
    meal_type: str = Field(..., min_length=1)
    food_name: str = Field(..., min_length=1)
    portion_description: str = Field(..., min_length=1)
    portion_grams: float | None = None
    calories: float = Field(default=0, ge=0)
    protein_g: float = Field(default=0, ge=0)
    carbs_g: float = Field(default=0, ge=0)
    fat_g: float = Field(default=0, ge=0)
    preparation_notes: str | None = None


class GeneratedMealDay(BaseModel):
    day_number: int = Field(..., ge=1, le=7)
    day_label: str = Field(..., min_length=1)
    items: list[GeneratedMealItem] = Field(..., min_length=1)


class GeneratedPlanSchema(BaseModel):
    """AI output must contain exactly 7 days of meals."""

    days: list[GeneratedMealDay] = Field(..., min_length=7, max_length=7)
