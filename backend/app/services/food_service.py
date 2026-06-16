"""Food item write operations — custom items scoped per dietitian."""

import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food_item import FoodItem
from app.schemas.food_item import FoodItemCreate, FoodItemList, FoodItemResponse, FoodItemUpdate
from app.services import cache_service


def _to_response(item: FoodItem) -> FoodItemResponse:
    return FoodItemResponse(
        id=item.id,
        name=item.name,
        name_hindi=item.name_hindi,
        category=item.category,
        subcategory=item.subcategory,
        calories_per_100g=item.calories_per_100g,
        protein_per_100g=float(item.protein_per_100g or 0),
        carbs_per_100g=float(item.carbs_per_100g or 0),
        fat_per_100g=float(item.fat_per_100g or 0),
        fiber_per_100g=float(item.fiber_per_100g) if item.fiber_per_100g else None,
        default_serving_description=item.default_serving_description,
        default_serving_grams=float(item.default_serving_grams)
        if item.default_serving_grams
        else None,
        is_vegetarian=item.is_vegetarian,
        is_vegan=item.is_vegan,
        is_gluten_free=item.is_gluten_free,
        common_allergens=list(item.common_allergens or []),
        approx_cost_per_kg_inr=float(item.approx_cost_per_kg_inr)
        if item.approx_cost_per_kg_inr
        else None,
    )


async def _get_accessible_food(
    db: AsyncSession, dietitian_id: uuid.UUID, food_id: uuid.UUID
) -> FoodItem:
    result = await db.execute(
        select(FoodItem).where(
            FoodItem.id == food_id,
            or_(
                FoodItem.dietitian_id.is_(None),
                FoodItem.dietitian_id == dietitian_id,
            ),
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Food item not found")
    return item


async def search_foods(
    db: AsyncSession,
    dietitian_id: uuid.UUID,
    q: Optional[str] = None,
    category: Optional[str] = None,
    is_vegetarian: Optional[bool] = None,
) -> FoodItemList:
    """Search food items with Redis caching."""
    cache_key = cache_service.food_search_key(
        str(dietitian_id), q, category, is_vegetarian
    )
    cached = await cache_service.cache_get(cache_key)
    if cached is not None:
        return FoodItemList(**cached)

    stmt = select(FoodItem).where(
        or_(
            FoodItem.dietitian_id.is_(None),
            FoodItem.dietitian_id == dietitian_id,
        )
    )
    if q:
        search = f"%{q}%"
        stmt = stmt.where(
            or_(
                FoodItem.name.ilike(search),
                FoodItem.name_hindi.ilike(search),
            )
        )
    if category:
        stmt = stmt.where(FoodItem.category == category)
    if is_vegetarian is not None:
        stmt = stmt.where(FoodItem.is_vegetarian == is_vegetarian)

    stmt = stmt.order_by(FoodItem.name)
    result = await db.execute(stmt)
    items = [_to_response(item) for item in result.scalars().all()]
    payload = FoodItemList(items=items, total=len(items)).model_dump(mode="json")
    await cache_service.cache_set(cache_key, payload)
    return FoodItemList(items=items, total=len(items))


async def get_food(
    db: AsyncSession, dietitian_id: uuid.UUID, food_id: uuid.UUID
) -> FoodItemResponse:
    item = await _get_accessible_food(db, dietitian_id, food_id)
    return _to_response(item)


async def create_food(
    db: AsyncSession, dietitian_id: uuid.UUID, data: FoodItemCreate
) -> FoodItemResponse:
    item = FoodItem(dietitian_id=dietitian_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    await cache_service.cache_delete_prefix(f"foods:search:{str(dietitian_id)}")
    await cache_service.cache_delete(cache_service.food_fetch_key(str(dietitian_id)))
    return _to_response(item)


async def update_food(
    db: AsyncSession,
    dietitian_id: uuid.UUID,
    food_id: uuid.UUID,
    data: FoodItemUpdate,
) -> FoodItemResponse:
    result = await db.execute(
        select(FoodItem).where(
            FoodItem.id == food_id,
            FoodItem.dietitian_id == dietitian_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=404,
            detail="Custom food item not found or not owned by you",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    await cache_service.cache_delete_prefix(f"foods:search:{str(dietitian_id)}")
    await cache_service.cache_delete(cache_service.food_fetch_key(str(dietitian_id)))
    return _to_response(item)
