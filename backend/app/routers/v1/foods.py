import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_dietitian
from app.models.dietitian import Dietitian
from app.models.food_item import FoodItem
from app.schemas.food_item import FoodItemList

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("", response_model=FoodItemList)
async def list_foods(
    q: Optional[str] = Query(None, description="Search by name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_vegetarian: Optional[bool] = Query(None, description="Filter by vegetarian"),
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """List and search food items."""
    stmt = select(FoodItem).where(
        or_(
            FoodItem.dietitian_id.is_(None),
            FoodItem.dietitian_id == dietitian.id
        )
    )

    if q:
        search = f"%{q}%"
        stmt = stmt.where(
            or_(
                FoodItem.name.ilike(search),
                FoodItem.name_hindi.ilike(search)
            )
        )
    if category:
        stmt = stmt.where(FoodItem.category == category)
    if is_vegetarian is not None:
        stmt = stmt.where(FoodItem.is_vegetarian == is_vegetarian)
        
    stmt = stmt.order_by(FoodItem.name)
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    return {"items": list(items), "total": len(items)}
