from datetime import date, datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MealPlanItemBase(BaseModel):
    meal_type: str = Field(..., description="e.g., breakfast, lunch, dinner, snack")
    food_name: str = Field(..., description="Name of the food item")
    portion_description: str = Field(..., description="e.g., '2 pieces', '1 bowl'")
    portion_grams: float | None = None
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    preparation_notes: str | None = None


class MealPlanItemCreate(MealPlanItemBase):
    pass


class MealPlanItemResponse(MealPlanItemBase):
    id: UUID
    meal_plan_day_id: UUID

    model_config = ConfigDict(from_attributes=True)


class MealPlanDayBase(BaseModel):
    day_number: int = Field(..., ge=1, le=7)
    day_label: str = Field(..., description="e.g., 'Monday', 'Day 1'")


class MealPlanDayCreate(MealPlanDayBase):
    items: List[MealPlanItemCreate] = []


class MealPlanDayResponse(MealPlanDayBase):
    id: UUID
    meal_plan_id: UUID
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    items: List[MealPlanItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MealPlanBase(BaseModel):
    title: str = Field(..., description="Name of the meal plan")
    week_start_date: date
    custom_instructions: str | None = None


class MealPlanCreate(MealPlanBase):
    days: List[MealPlanDayCreate] = []


class MealPlanUpdate(BaseModel):
    title: str | None = None
    custom_instructions: str | None = None
    # For MVP, full replacement of days/items is easier than delta updates,
    # but we'll stick to a simpler model where the client can send the full structure
    days: List[MealPlanDayCreate] | None = None


class MealPlanValidationResponse(BaseModel):
    id: UUID
    validation_type: str
    passed: bool
    severity: str | None = None
    message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MealPlanResponse(MealPlanBase):
    id: UUID
    client_id: UUID
    dietitian_id: UUID
    status: str
    avg_daily_calories: float
    avg_daily_protein_g: float
    avg_daily_carbs_g: float
    avg_daily_fat_g: float
    created_at: datetime
    updated_at: datetime | None = None
    approved_at: datetime | None = None
    delivered_at: datetime | None = None
    days: List[MealPlanDayResponse] = []
    validations: List[MealPlanValidationResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MealPlanListResponse(BaseModel):
    id: UUID
    title: str
    week_start_date: date
    status: str
    avg_daily_calories: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MealPlanListCollection(BaseModel):
    plans: List[MealPlanListResponse]
    total: int

class GeneratePlanRequest(BaseModel):
    week_start_date: date
    custom_instructions: str | None = None
    protocol_id: UUID | None = None


class RegeneratePlanRequest(BaseModel):
    custom_instructions: str | None = None
    week_start_date: date | None = None
    protocol_id: UUID | None = None


class MealPlanValidationsList(BaseModel):
    validations: List[MealPlanValidationResponse]
    total: int
