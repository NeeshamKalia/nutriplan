"""Shared helpers for WhatsApp meal-tracking handlers."""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client
from app.models.meal_log import MealLog
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanItem

MEAL_TYPES = (
    "breakfast",
    "mid_morning",
    "lunch",
    "evening_snack",
    "dinner",
    "bedtime",
)

# Default hour ranges when client has no meal_timing_preferences
DEFAULT_MEAL_HOURS: dict[str, tuple[int, int]] = {
    "breakfast": (5, 10),
    "mid_morning": (10, 12),
    "lunch": (12, 15),
    "evening_snack": (15, 18),
    "dinner": (18, 22),
    "bedtime": (22, 5),
}

MEAL_TYPE_ALIASES: dict[str, str] = {
    "breakfast": "breakfast",
    "morning": "breakfast",
    "mid morning": "mid_morning",
    "mid_morning": "mid_morning",
    "snack": "evening_snack",
    "evening snack": "evening_snack",
    "evening_snack": "evening_snack",
    "lunch": "lunch",
    "dinner": "dinner",
    "supper": "dinner",
    "bedtime": "bedtime",
    "night": "bedtime",
}


def meal_type_label(meal_type: str) -> str:
    return meal_type.replace("_", " ").title()


def get_day_number(plan: MealPlan, today: date | None = None) -> int:
    today = today or date.today()
    if plan.week_start_date:
        delta = (today - plan.week_start_date).days
        return (delta % 7) + 1
    return today.isoweekday()


def infer_current_meal_type(
    now: datetime | None = None,
    client: Client | None = None,
) -> str:
    """Pick the meal slot most likely being logged right now."""
    now = now or datetime.now()
    hour = now.hour

    if client and client.meal_timing_preferences:
        prefs = client.meal_timing_preferences
        if isinstance(prefs, dict) and prefs:
            current = _meal_from_preferences(hour, prefs)
            if current:
                return current

    for meal_type in reversed(MEAL_TYPES):
        start, end = DEFAULT_MEAL_HOURS[meal_type]
        if start <= end:
            if start <= hour < end:
                return meal_type
        elif hour >= start or hour < end:
            return meal_type

    return "breakfast"


def _meal_from_preferences(hour: int, prefs: dict) -> str | None:
    """Return the most recent meal whose scheduled time has passed today."""
    scheduled: list[tuple[int, str]] = []
    for meal_type in MEAL_TYPES:
        raw = prefs.get(meal_type)
        if not raw:
            continue
        try:
            parts = str(raw).split(":")
            scheduled.append((int(parts[0]), meal_type))
        except (ValueError, IndexError):
            continue

    if not scheduled:
        return None

    scheduled.sort()
    current = scheduled[0][1]
    for meal_hour, meal_type in scheduled:
        if hour >= meal_hour:
            current = meal_type
    return current


def extract_meal_type_from_text(text: str) -> str | None:
    msg_lower = text.lower()
    for alias, meal_type in sorted(MEAL_TYPE_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias in msg_lower:
            return meal_type
    return None


async def get_active_plan_day(
    db: AsyncSession,
    client: Client,
    today: date | None = None,
) -> tuple[MealPlan, MealPlanDay] | None:
    """Fetch the client's delivered plan and today's day record."""
    today = today or date.today()

    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.client_id == client.id)
        .where(MealPlan.status == "delivered")
        .order_by(MealPlan.created_at.desc())
    )
    plan = result.scalars().first()
    if not plan:
        return None

    day_num = get_day_number(plan, today)
    result = await db.execute(
        select(MealPlanDay)
        .options(selectinload(MealPlanDay.items))
        .where(MealPlanDay.meal_plan_id == plan.id)
        .where(MealPlanDay.day_number == day_num)
    )
    day = result.scalars().first()
    if not day:
        return None

    return plan, day


def find_plan_item(day: MealPlanDay, meal_type: str) -> MealPlanItem | None:
    items = sorted(day.items, key=lambda x: x.sort_order) if day.items else []
    for item in items:
        if item.meal_type == meal_type:
            return item
    return None


def planned_meal_types(day: MealPlanDay) -> list[str]:
    items = day.items or []
    seen: set[str] = set()
    ordered: list[str] = []
    for meal_type in MEAL_TYPES:
        if any(item.meal_type == meal_type for item in items) and meal_type not in seen:
            seen.add(meal_type)
            ordered.append(meal_type)
    return ordered


async def get_existing_log(
    db: AsyncSession,
    client_id,
    log_date: date,
    meal_type: str,
) -> MealLog | None:
    result = await db.execute(
        select(MealLog).where(
            MealLog.client_id == client_id,
            MealLog.log_date == log_date,
            MealLog.meal_type == meal_type,
        )
    )
    return result.scalars().first()


async def count_completed_meals(
    db: AsyncSession,
    client_id,
    log_date: date,
    meal_types: list[str],
) -> int:
    if not meal_types:
        return 0

    result = await db.execute(
        select(MealLog).where(
            MealLog.client_id == client_id,
            MealLog.log_date == log_date,
            MealLog.meal_type.in_(meal_types),
            MealLog.status == "completed",
        )
    )
    return len(result.scalars().all())
