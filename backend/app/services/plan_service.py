import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logger import get_logger
from app.models.client import Client
from app.models.food_item import FoodItem
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanItem, MealPlanValidation
from app.schemas.meal_plan import (
    MealPlanCreate,
    MealPlanUpdate,
    GeneratePlanRequest,
    RegeneratePlanRequest,
    MealPlanValidationResponse,
)
from app.ai.plan_generator import generate_meal_plan
from app.ai.plan_judge import judge_meal_plan
from app.ai.plan_validator import run_all_validations
from app.services import protocol_service, cache_service
from app.services.whatsapp_service import whatsapp_service
from app.whatsapp.message_formatter import format_daily_plan

logger = get_logger(__name__)

# Valid plan status transitions
_VALID_TRANSITIONS = {
    "draft": {"approved"},
    "approved": {"delivered"},
    "delivered": {"expired"},
}


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
            selectinload(MealPlan.days).selectinload(MealPlanDay.items),
            selectinload(MealPlan.validations)
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


async def _fetch_food_items(db: AsyncSession, dietitian_id: uuid.UUID) -> list[FoodItem]:
    from sqlalchemy import or_

    cache_key = cache_service.food_fetch_key(str(dietitian_id))
    cached = await cache_service.cache_get(cache_key)
    if cached is not None:
        food_ids = cached.get("ids", [])
        if not food_ids:
            return []
        result = await db.execute(select(FoodItem).where(FoodItem.id.in_(food_ids)))
        return list(result.scalars().all())

    stmt = (
        select(FoodItem)
        .where(
            or_(
                FoodItem.dietitian_id.is_(None),
                FoodItem.dietitian_id == dietitian_id,
            )
        )
        .limit(200)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    await cache_service.cache_set(cache_key, {"ids": [str(i.id) for i in items]})
    return items


async def _fetch_generation_context(
    db: AsyncSession,
    dietitian_id: uuid.UUID,
    client: Client,
    protocol_id: uuid.UUID | None = None,
) -> tuple[str, str]:
    """Load protocol guidelines and recent plan summaries for AI generation."""
    if protocol_id:
        protocol_context = await protocol_service.get_protocol_context(
            db, dietitian_id, protocol_id
        )
    else:
        from app.models.protocol import Protocol

        protocol_context = ""
        result = await db.execute(
            select(Protocol)
            .where(Protocol.dietitian_id == dietitian_id, Protocol.is_active.is_(True))
            .order_by(Protocol.updated_at.desc())
            .limit(3)
        )
        protocols = result.scalars().all()
        if protocols:
            protocol_context = "\n\n".join(
                protocol_service.format_protocol_context(p) for p in protocols
            )

    previous_plans_context = ""
    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.client_id == client.id, MealPlan.dietitian_id == dietitian_id)
        .order_by(MealPlan.created_at.desc())
        .limit(2)
    )
    previous_plans = result.scalars().all()
    if previous_plans:
        previous_plans_context = "\n".join(
            f"- {p.title or 'Untitled'} ({p.status}, "
            f"avg {int(p.avg_daily_calories or 0)} kcal/day)"
            for p in previous_plans
        )

    return protocol_context, previous_plans_context


def _apply_ai_plan_data(
    plan: MealPlan, plan_data: dict, client: Client
) -> None:
    """Populate plan days and validations from validated AI output."""
    validations = run_all_validations(plan_data, client)

    plan.days = []
    plan.validations = []

    for day_data in plan_data.get("days", []):
        day = MealPlanDay(
            day_number=day_data.get("day_number", 1),
            day_label=day_data.get("day_label", ""),
            items=[],
        )
        for item_data in day_data.get("items", []):
            item = MealPlanItem(
                meal_type=item_data.get("meal_type", "unknown"),
                food_name=item_data.get("food_name", "Unknown"),
                portion_description=item_data.get("portion_description", ""),
                portion_grams=item_data.get("portion_grams"),
                calories=item_data.get("calories", 0),
                protein_g=item_data.get("protein_g", 0.0),
                carbs_g=item_data.get("carbs_g", 0.0),
                fat_g=item_data.get("fat_g", 0.0),
                preparation_notes=item_data.get("preparation_notes"),
            )
            day.items.append(item)
        plan.days.append(day)

    for val in validations:
        v = MealPlanValidation(
            validation_type=val["type"],
            passed=val["passed"],
            severity=val["severity"],
            message=val["message"],
        )
        plan.validations.append(v)

    _calculate_totals(plan)


async def _apply_llm_judge_validations(
    plan: MealPlan, plan_data: dict, client: Client
) -> None:
    """Append LLM-as-judge scores to plan validations."""
    judge_results = await judge_meal_plan(plan_data, client)
    for val in judge_results:
        plan.validations.append(
            MealPlanValidation(
                validation_type=val["type"],
                passed=val["passed"],
                severity=val["severity"],
                message=val["message"],
                details=val.get("details"),
            )
        )


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
    """Approve a plan and attempt WhatsApp delivery.

    State guard: only 'draft' plans can be approved.
    WhatsApp delivery is attempted inline but failure does NOT block approval.
    If delivery fails, plan stays 'approved' (not 'delivered') so the
    dietitian can see and retry.
    """
    plan = await _get_plan_with_auth(db, dietitian_id, plan_id)

    # State guard: only draft plans can be approved
    if plan.status != "draft":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve a plan with status '{plan.status}'. "
                   f"Only 'draft' plans can be approved.",
        )

    plan.status = "approved"
    plan.approved_at = datetime.now(timezone.utc)
    plan.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # Tenant-scoped client lookup for WhatsApp delivery
    result = await db.execute(
        select(Client).where(
            Client.id == plan.client_id,
            Client.dietitian_id == dietitian_id,
        )
    )
    client = result.scalar_one_or_none()
    to_number = client.whatsapp_number if client else None

    if to_number:
        try:
            # 1. Send announcement
            announcement = await whatsapp_service.send_text_message(
                to_number,
                f"🎉 Great news! Your new meal plan '{plan.title}' is ready!",
                db=db,
                client_id=client.id,
                dietitian_id=dietitian_id,
            )
            if not announcement:
                logger.warning(
                    f"WhatsApp announcement skipped/failed for plan {plan.id}. "
                    f"Plan remains 'approved'."
                )
                return await _get_plan_with_auth(db, dietitian_id, plan_id)

            # 2. Send Day 1 detailed meals
            day_1 = next((d for d in plan.days if d.day_number == 1), None)
            if day_1:
                msg = format_daily_plan(day_1)
                day_result = await whatsapp_service.send_text_message(
                    to_number,
                    msg,
                    db=db,
                    client_id=client.id,
                    dietitian_id=dietitian_id,
                )
                if not day_result:
                    logger.warning(
                        f"WhatsApp day-1 plan send failed for plan {plan.id}. "
                        f"Plan remains 'approved'."
                    )
                    return await _get_plan_with_auth(db, dietitian_id, plan_id)

            # 3. Mark as delivered only after all sends succeed
            plan.status = "delivered"
            plan.delivered_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info(f"Plan {plan.id} delivered to {to_number}")

        except Exception as e:
            # Plan stays 'approved' — dietitian can see delivery failed
            logger.error(
                f"WhatsApp delivery failed for plan {plan.id}: {e}. "
                f"Plan remains 'approved' — delivery can be retried."
            )
    else:
        logger.warning(
            f"No WhatsApp number for plan {plan.id} client. "
            f"Plan approved but not delivered."
        )

    return await _get_plan_with_auth(db, dietitian_id, plan_id)


async def generate_plan_for_client(
    db: AsyncSession, dietitian_id: uuid.UUID, client_id: uuid.UUID, data: GeneratePlanRequest
) -> MealPlan:
    """Generate a meal plan using AI."""
    client = await _verify_client_access(db, dietitian_id, client_id)
    food_items = await _fetch_food_items(db, dietitian_id)
    protocol_context, previous_plans_context = await _fetch_generation_context(
        db, dietitian_id, client, data.protocol_id
    )

    plan_data, metadata = await generate_meal_plan(
        client_profile=client,
        food_items=food_items,
        custom_instructions=data.custom_instructions,
        protocol_context=protocol_context,
        previous_plans_context=previous_plans_context,
    )

    plan = MealPlan(
        client_id=client_id,
        dietitian_id=dietitian_id,
        title=f"AI Generated Plan - {data.week_start_date}",
        week_start_date=data.week_start_date,
        custom_instructions=data.custom_instructions,
        protocol_id=data.protocol_id,
        status="draft",
        generation_model=metadata.get("model"),
        generation_tokens_used=metadata.get("tokens_used"),
        generation_cost_usd=metadata.get("cost_usd"),
        generation_duration_ms=metadata.get("duration_ms"),
        days=[],
        validations=[],
    )

    _apply_ai_plan_data(plan, plan_data, client)
    await _apply_llm_judge_validations(plan, plan_data, client)
    db.add(plan)
    await db.commit()

    return await _get_plan_with_auth(db, dietitian_id, plan.id)


async def get_plan_validations(
    db: AsyncSession, dietitian_id: uuid.UUID, plan_id: uuid.UUID
) -> list[MealPlanValidationResponse]:
    """Return validation results for a plan."""
    plan = await _get_plan_with_auth(db, dietitian_id, plan_id)
    return [
        MealPlanValidationResponse(
            id=v.id,
            validation_type=v.validation_type,
            passed=v.passed,
            severity=v.severity,
            message=v.message,
        )
        for v in plan.validations
    ]


async def regenerate_plan(
    db: AsyncSession,
    dietitian_id: uuid.UUID,
    plan_id: uuid.UUID,
    data: RegeneratePlanRequest,
) -> MealPlan:
    """Regenerate an existing draft plan with new AI output."""
    plan = await _get_plan_with_auth(db, dietitian_id, plan_id)

    if plan.status != "draft":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot regenerate a plan with status '{plan.status}'. "
            "Only draft plans can be regenerated.",
        )

    client = await _verify_client_access(db, dietitian_id, plan.client_id)
    food_items = await _fetch_food_items(db, dietitian_id)
    protocol_id = data.protocol_id or plan.protocol_id
    protocol_context, previous_plans_context = await _fetch_generation_context(
        db, dietitian_id, client, protocol_id
    )

    instructions = (
        data.custom_instructions
        if data.custom_instructions is not None
        else plan.custom_instructions
    )
    if data.week_start_date:
        plan.week_start_date = data.week_start_date
        plan.title = f"AI Generated Plan - {data.week_start_date}"

    plan_data, metadata = await generate_meal_plan(
        client_profile=client,
        food_items=food_items,
        custom_instructions=instructions,
        protocol_context=protocol_context,
        previous_plans_context=previous_plans_context,
    )
    if protocol_id:
        plan.protocol_id = protocol_id

    plan.custom_instructions = instructions
    plan.generation_model = metadata.get("model")
    plan.generation_tokens_used = metadata.get("tokens_used")
    plan.generation_cost_usd = metadata.get("cost_usd")
    plan.generation_duration_ms = metadata.get("duration_ms")
    plan.updated_at = datetime.now(timezone.utc)

    _apply_ai_plan_data(plan, plan_data, client)
    await _apply_llm_judge_validations(plan, plan_data, client)
    await db.commit()

    return await _get_plan_with_auth(db, dietitian_id, plan.id)

