from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.meal_log import MealLog
from app.services.whatsapp_service import whatsapp_service
from app.whatsapp.meal_context import (
    count_completed_meals,
    find_plan_item,
    get_active_plan_day,
    get_existing_log,
    infer_current_meal_type,
    meal_type_label,
    planned_meal_types,
)


async def handle_done(db: AsyncSession, client: Client, to_number: str) -> None:
    today = date.today()
    plan_day = await get_active_plan_day(db, client, today)
    if not plan_day:
        await whatsapp_service.send_text_message(
            to_number,
            "You don't have an active meal plan yet.",
        )
        return

    _, day = plan_day
    meal_type = infer_current_meal_type(client=client)
    label = meal_type_label(meal_type)

    existing = await get_existing_log(db, client.id, today, meal_type)
    if existing:
        await whatsapp_service.send_text_message(
            to_number,
            f"You've already logged {label} today ({existing.status}). Send HELP for commands.",
        )
        return

    plan_item = find_plan_item(day, meal_type)
    log = MealLog(
        client_id=client.id,
        meal_plan_item_id=plan_item.id if plan_item else None,
        log_date=today,
        meal_type=meal_type,
        status="completed",
        logged_via="whatsapp",
    )
    db.add(log)
    await db.commit()

    meal_types = planned_meal_types(day)
    completed = await count_completed_meals(db, client.id, today, meal_types)

    if meal_types and completed >= len(meal_types):
        await whatsapp_service.send_text_message(
            to_number,
            "Amazing! All meals completed today! 🎉",
        )
        return

    await whatsapp_service.send_text_message(
        to_number,
        f"✅ {label} logged! Keep it up 💪",
    )
