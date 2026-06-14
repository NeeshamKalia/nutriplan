import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanItem
from app.schemas.meal_plan import MealPlanCreate, MealPlanUpdate


async def _verify_client_access(db: AsyncSession, dietitian_id: uuid.UUID, client_id: uuid.UUID) -> Client:
    """Ensure the client belongs to the requesting dietitian."""
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.dietitian_id == dietitian_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


async def _get_plan_with_auth(db: AsyncSession, dietitian_id: uuid.UUID, plan_id: uuid.UUID) -> MealPlan:
    """Fetch plan with days/items and verify dietitian access."""
    result = await db.execute(
        select(MealPlan)
        .options(
            selectinload(MealPlan.days).selectinload(MealPlanDay.items)
        )
        .where(MealPlan.id == plan_id, MealPlan.dietitian_id == dietitian_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return plan


def _calculate_totals(plan: MealPlan) -> None:
    """Calculate daily totals and plan averages."""
    total_days = len(plan.days)
    if total_days == 0:
        plan.avg_daily_calories = 0
        plan.avg_daily_protein_g = 0
        plan.avg_daily_carbs_g = 0
        plan.avg_daily_fat_g = 0
        return

    plan_cals = 0.0
    plan_prot = 0.0
    plan_carbs = 0.0
    plan_fat = 0.0

    for day in plan.days:
        day.total_calories = sum(item.calories for item in day.items)
        day.total_protein_g = sum(item.protein_g for item in day.items)
        day.total_carbs_g = sum(item.carbs_g for item in day.items)
        day.total_fat_g = sum(item.fat_g for item in day.items)

        plan_cals += day.total_calories
        plan_prot += day.total_protein_g
        plan_carbs += day.total_carbs_g
        plan_fat += day.total_fat_g

    plan.avg_daily_calories = plan_cals / total_days
    plan.avg_daily_protein_g = plan_prot / total_days
    plan.avg_daily_carbs_g = plan_carbs / total_days
    plan.avg_daily_fat_g = plan_fat / total_days


async def create_plan(
    db: AsyncSession, dietitian_id: uuid.UUID, client_id: uuid.UUID, data: MealPlanCreate
) -> MealPlan:
    """Create a new meal plan with its days and items."""
    await _verify_client_access(db, dietitian_id, client_id)

    plan = MealPlan(
        client_id=client_id,
        dietitian_id=dietitian_id,
        title=data.title,
        week_start_date=data.week_start_date,
        custom_instructions=data.custom_instructions,
        status="draft",
        days=[]
    )

    for day_data in data.days:
        day = MealPlanDay(
            day_number=day_data.day_number,
            day_label=day_data.day_label,
            items=[]
        )
        for item_data in day_data.items:
            item = MealPlanItem(**item_data.model_dump())
            day.items.append(item)
        plan.days.append(day)

    _calculate_totals(plan)

    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    
    # We must explicitly re-load with relationships for the response
    return await _get_plan_with_auth(db, dietitian_id, plan.id)


async def list_plans(
    db: AsyncSession, dietitian_id: uuid.UUID, client_id: uuid.UUID
) -> tuple[list[MealPlan], int]:
    """List plans for a specific client."""
    await _verify_client_access(db, dietitian_id, client_id)

    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.client_id == client_id, MealPlan.dietitian_id == dietitian_id)
        .order_by(MealPlan.created_at.desc())
    )
    plans = result.scalars().all()
    
    # To conform to standard list return we could count, but since it's unpaginated for a client:
    return list(plans), len(plans)


async def get_plan(db: AsyncSession, dietitian_id: uuid.UUID, plan_id: uuid.UUID) -> MealPlan:
    """Get full details of a specific plan."""
    return await _get_plan_with_auth(db, dietitian_id, plan_id)


async def update_plan(
    db: AsyncSession, dietitian_id: uuid.UUID, plan_id: uuid.UUID, data: MealPlanUpdate
) -> MealPlan:
    """Update a plan. For simplicity, days/items are fully replaced if provided."""
    plan = await _get_plan_with_auth(db, dietitian_id, plan_id)

    if data.title is not None:
        plan.title = data.title
    if data.custom_instructions is not None:
        plan.custom_instructions = data.custom_instructions

    if data.days is not None:
        # Full replacement of days
        for existing_day in plan.days:
            await db.delete(existing_day)
        
        plan.days = []
        for day_data in data.days:
            day = MealPlanDay(
                day_number=day_data.day_number,
                day_label=day_data.day_label,
                items=[]
            )
            for item_data in day_data.items:
                item = MealPlanItem(**item_data.model_dump())
                day.items.append(item)
            plan.days.append(day)

    _calculate_totals(plan)
    plan.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    return await _get_plan_with_auth(db, dietitian_id, plan_id)


async def approve_plan(db: AsyncSession, dietitian_id: uuid.UUID, plan_id: uuid.UUID) -> MealPlan:
    """Mark a plan as approved by the dietitian."""
    plan = await _get_plan_with_auth(db, dietitian_id, plan_id)
    
    plan.status = "approved"
    plan.approved_at = datetime.now(timezone.utc)
    plan.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    return plan
