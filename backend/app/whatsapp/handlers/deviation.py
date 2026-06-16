import re
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.meal_log import MealLog
from app.services.whatsapp_service import whatsapp_service
from app.whatsapp.meal_context import (
    extract_meal_type_from_text,
    find_plan_item,
    get_active_plan_day,
    get_existing_log,
    infer_current_meal_type,
    meal_type_label,
)

SKIP_PATTERNS = re.compile(
    r"\b(skipped?|missed|didn'?t eat|did not eat|no\s+\w+\s+today)\b",
    re.IGNORECASE,
)
DEVIATION_PATTERNS = re.compile(
    r"\b(had|ate|instead|replaced|swapped)\b",
    re.IGNORECASE,
)


def parse_deviation(message: str) -> tuple[str, str | None]:
    """Return (status, meal_type_hint) from free-text deviation messages."""
    meal_type = extract_meal_type_from_text(message)

    if SKIP_PATTERNS.search(message):
        return "skipped", meal_type

    if DEVIATION_PATTERNS.search(message):
        return "deviated", meal_type

    return "deviated", meal_type


async def handle_deviation(
    db: AsyncSession,
    client: Client,
    to_number: str,
    message: str,
) -> None:
    today = date.today()
    plan_day = await get_active_plan_day(db, client, today)
    if not plan_day:
        await whatsapp_service.send_text_message(
            to_number,
            "You don't have an active meal plan yet.",
            db=db,
            client_id=client.id,
            dietitian_id=client.dietitian_id,
        )
        return

    _, day = plan_day
    status, meal_hint = parse_deviation(message)
    meal_type = meal_hint or infer_current_meal_type(client=client)
    label = meal_type_label(meal_type)

    existing = await get_existing_log(db, client.id, today, meal_type)
    if existing:
        await whatsapp_service.send_text_message(
            to_number,
            f"Already noted for {label} today. Your dietitian can see the update.",
            db=db,
            client_id=client.id,
            dietitian_id=client.dietitian_id,
        )
        return

    plan_item = find_plan_item(day, meal_type)
    log = MealLog(
        client_id=client.id,
        meal_plan_item_id=plan_item.id if plan_item else None,
        log_date=today,
        meal_type=meal_type,
        status=status,
        deviation_note=message.strip(),
        logged_via="whatsapp",
    )
    db.add(log)
    await db.commit()

    if status == "skipped":
        reply = f"Noted — {label} marked as skipped. No worries, tomorrow is a fresh start. 🌱"
    else:
        reply = f"Got it — {label} deviation logged. Thanks for being honest! Your dietitian will see this. 👍"

    await whatsapp_service.send_text_message(
        to_number,
        reply,
        db=db,
        client_id=client.id,
        dietitian_id=client.dietitian_id,
    )
