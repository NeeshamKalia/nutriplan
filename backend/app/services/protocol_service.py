"""Protocol template service — CRUD with multi-tenant isolation."""

import uuid as uuid_mod
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.meal_plan import MealPlan, MealPlanDay
from app.models.protocol import Protocol
from app.schemas.protocol import (
    ProtocolCreate,
    ProtocolListResponse,
    ProtocolResponse,
    ProtocolUpdate,
    SavePlanAsProtocolRequest,
)


def _to_list(val):
    if isinstance(val, list):
        return val
    if isinstance(val, str) and val:
        try:
            import json

            return json.loads(val)
        except (ValueError, TypeError):
            return [s.strip() for s in val.split(",") if s.strip()]
    return None


def _to_dict(val):
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and val:
        try:
            import json

            return json.loads(val)
        except (ValueError, TypeError):
            return None
    return None


def _protocol_to_response(protocol: Protocol) -> ProtocolResponse:
    return ProtocolResponse(
        id=str(protocol.id),
        dietitian_id=str(protocol.dietitian_id),
        name=protocol.name,
        description=protocol.description,
        target_conditions=_to_list(protocol.target_conditions),
        target_goals=_to_list(protocol.target_goals),
        calorie_range_min=protocol.calorie_range_min,
        calorie_range_max=protocol.calorie_range_max,
        macro_split=_to_dict(protocol.macro_split),
        general_guidelines=protocol.general_guidelines,
        preferred_foods=_to_list(protocol.preferred_foods),
        avoided_foods=_to_list(protocol.avoided_foods),
        sample_plan=_to_dict(protocol.sample_plan),
        is_active=protocol.is_active if protocol.is_active is not None else True,
        created_at=protocol.created_at,
        updated_at=protocol.updated_at,
    )


def format_protocol_context(protocol: Protocol) -> str:
    """Build AI prompt context from a protocol template."""
    lines = [f"Protocol: {protocol.name}"]

    if protocol.description:
        lines.append(f"Description: {protocol.description}")
    if protocol.target_conditions:
        conditions = _to_list(protocol.target_conditions) or []
        lines.append(f"Target conditions: {', '.join(conditions)}")
    if protocol.target_goals:
        goals = _to_list(protocol.target_goals) or []
        lines.append(f"Target goals: {', '.join(goals)}")
    if protocol.calorie_range_min or protocol.calorie_range_max:
        lines.append(
            f"Calorie range: {protocol.calorie_range_min or '?'}–"
            f"{protocol.calorie_range_max or '?'} kcal/day"
        )
    macro = _to_dict(protocol.macro_split)
    if macro:
        lines.append(
            "Macro split: "
            f"P {macro.get('protein_pct', '?')}% / "
            f"C {macro.get('carbs_pct', '?')}% / "
            f"F {macro.get('fat_pct', '?')}%"
        )
    if protocol.general_guidelines:
        lines.append(f"Guidelines: {protocol.general_guidelines}")
    if protocol.preferred_foods:
        foods = _to_list(protocol.preferred_foods) or []
        lines.append(f"Preferred foods: {', '.join(foods)}")
    if protocol.avoided_foods:
        foods = _to_list(protocol.avoided_foods) or []
        lines.append(f"Avoid: {', '.join(foods)}")

    return "\n".join(lines)


def _plan_to_sample_plan(plan: MealPlan) -> dict:
    return {
        "days": [
            {
                "day_number": day.day_number,
                "day_label": day.day_label,
                "items": [
                    {
                        "meal_type": item.meal_type,
                        "food_name": item.food_name,
                        "portion_description": item.portion_description,
                        "portion_grams": float(item.portion_grams)
                        if item.portion_grams is not None
                        else None,
                        "calories": float(item.calories or 0),
                        "protein_g": float(item.protein_g or 0),
                        "carbs_g": float(item.carbs_g or 0),
                        "fat_g": float(item.fat_g or 0),
                        "preparation_notes": item.preparation_notes,
                    }
                    for item in day.items
                ],
            }
            for day in sorted(plan.days, key=lambda d: d.day_number)
        ]
    }


async def _get_protocol_or_404(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, protocol_id: uuid_mod.UUID
) -> Protocol:
    result = await db.execute(
        select(Protocol).where(
            Protocol.id == protocol_id,
            Protocol.dietitian_id == dietitian_id,
        )
    )
    protocol = result.scalar_one_or_none()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return protocol


async def create_protocol(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, data: ProtocolCreate
) -> ProtocolResponse:
    macro_split = (
        data.macro_split.model_dump()
        if hasattr(data.macro_split, "model_dump")
        else data.macro_split
    )

    protocol = Protocol(
        dietitian_id=dietitian_id,
        name=data.name,
        description=data.description,
        target_conditions=data.target_conditions,
        target_goals=data.target_goals,
        calorie_range_min=data.calorie_range_min,
        calorie_range_max=data.calorie_range_max,
        macro_split=macro_split,
        general_guidelines=data.general_guidelines,
        preferred_foods=data.preferred_foods,
        avoided_foods=data.avoided_foods,
        sample_plan=data.sample_plan,
        is_active=data.is_active,
    )
    db.add(protocol)
    await db.commit()
    await db.refresh(protocol)
    return _protocol_to_response(protocol)


async def list_protocols(
    db: AsyncSession,
    dietitian_id: uuid_mod.UUID,
    search: str | None = None,
    active_only: bool = True,
) -> ProtocolListResponse:
    stmt = select(Protocol).where(Protocol.dietitian_id == dietitian_id)
    if active_only:
        stmt = stmt.where(Protocol.is_active.is_(True))
    if search:
        stmt = stmt.where(Protocol.name.ilike(f"%{search}%"))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    result = await db.execute(stmt.order_by(Protocol.updated_at.desc()))
    protocols = [_protocol_to_response(p) for p in result.scalars().all()]
    return ProtocolListResponse(protocols=protocols, total=total)


async def get_protocol(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, protocol_id: uuid_mod.UUID
) -> ProtocolResponse:
    protocol = await _get_protocol_or_404(db, dietitian_id, protocol_id)
    return _protocol_to_response(protocol)


async def update_protocol(
    db: AsyncSession,
    dietitian_id: uuid_mod.UUID,
    protocol_id: uuid_mod.UUID,
    data: ProtocolUpdate,
) -> ProtocolResponse:
    protocol = await _get_protocol_or_404(db, dietitian_id, protocol_id)
    updates = data.model_dump(exclude_unset=True)

    if "macro_split" in updates and updates["macro_split"] is not None:
        macro = updates["macro_split"]
        if hasattr(macro, "model_dump"):
            updates["macro_split"] = macro.model_dump()

    for field, value in updates.items():
        setattr(protocol, field, value)

    protocol.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(protocol)
    return _protocol_to_response(protocol)


async def delete_protocol(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, protocol_id: uuid_mod.UUID
) -> None:
    protocol = await _get_protocol_or_404(db, dietitian_id, protocol_id)
    await db.delete(protocol)
    await db.commit()


async def save_plan_as_protocol(
    db: AsyncSession,
    dietitian_id: uuid_mod.UUID,
    plan_id: uuid_mod.UUID,
    data: SavePlanAsProtocolRequest,
) -> ProtocolResponse:
    result = await db.execute(
        select(MealPlan)
        .options(selectinload(MealPlan.days).selectinload(MealPlanDay.items))
        .where(MealPlan.id == plan_id, MealPlan.dietitian_id == dietitian_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    sample_plan = _plan_to_sample_plan(plan)
    calorie_min = int(plan.avg_daily_calories * 0.9) if plan.avg_daily_calories else None
    calorie_max = int(plan.avg_daily_calories * 1.1) if plan.avg_daily_calories else None

    protocol = Protocol(
        dietitian_id=dietitian_id,
        name=data.name,
        description=data.description or f"Saved from plan: {plan.title or 'Untitled'}",
        target_conditions=data.target_conditions,
        target_goals=data.target_goals,
        calorie_range_min=calorie_min,
        calorie_range_max=calorie_max,
        general_guidelines=data.general_guidelines,
        sample_plan=sample_plan,
        is_active=True,
    )
    db.add(protocol)
    await db.commit()
    await db.refresh(protocol)
    return _protocol_to_response(protocol)


async def get_protocol_context(
    db: AsyncSession,
    dietitian_id: uuid_mod.UUID,
    protocol_id: uuid_mod.UUID | None,
) -> str:
    """Fetch formatted context for a specific protocol."""
    if not protocol_id:
        return ""
    protocol = await _get_protocol_or_404(db, dietitian_id, protocol_id)
    return format_protocol_context(protocol)
