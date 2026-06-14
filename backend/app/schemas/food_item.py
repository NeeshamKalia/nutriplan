import uuid
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class FoodItemResponse(BaseModel):
    id: uuid.UUID
    name: str
    name_hindi: str | None = None
    category: str
    subcategory: str | None = None
    calories_per_100g: int
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    fiber_per_100g: float | None = None
    default_serving_description: str | None = None
    default_serving_grams: float | None = None
    is_vegetarian: bool
    is_vegan: bool
    is_gluten_free: bool
    common_allergens: List[str] = []
    approx_cost_per_kg_inr: float | None = None

    model_config = ConfigDict(from_attributes=True)


class FoodItemList(BaseModel):
    items: List[FoodItemResponse]
    total: int
