import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_dietitian
from app.models.dietitian import Dietitian
from app.schemas.food_item import (
    FoodItemCreate,
    FoodItemList,
    FoodItemResponse,
    FoodItemUpdate,
)
from app.services import food_service

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("", response_model=FoodItemList)
async def list_foods(
    q: Optional[str] = Query(None, description="Search by name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_vegetarian: Optional[bool] = Query(None, description="Filter by vegetarian"),
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """List and search food items (cached)."""
    return await food_service.search_foods(
        db, dietitian.id, q=q, category=category, is_vegetarian=is_vegetarian
    )


@router.post("", response_model=FoodItemResponse, status_code=201)
async def create_food(
    data: FoodItemCreate,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Add a custom food item for this dietitian."""
    return await food_service.create_food(db, dietitian.id, data)


@router.get("/{food_id}", response_model=FoodItemResponse)
async def get_food(
    food_id: uuid.UUID,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Get a single food item by ID."""
    return await food_service.get_food(db, dietitian.id, food_id)


@router.put("/{food_id}", response_model=FoodItemResponse)
async def update_food(
    food_id: uuid.UUID,
    data: FoodItemUpdate,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Update a dietitian-owned custom food item."""
    return await food_service.update_food(db, dietitian.id, food_id, data)
