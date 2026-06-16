import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.substitution import suggest_alternatives
from app.models.client import Client
from app.services.whatsapp_service import whatsapp_service
from app.whatsapp.meal_context import (
    find_plan_item,
    get_active_plan_day,
    infer_current_meal_type,
    meal_type_label,
)

SWAP_PREFIX = re.compile(
    r"^(?:swap|replace|i don'?t have|i dont have)\s+",
    re.IGNORECASE,
)


def extract_food_item(message: str) -> str | None:
    text = message.strip()
    if not text:
        return None

    cleaned = SWAP_PREFIX.sub("", text).strip(" .!?")
    if cleaned:
        return cleaned

    # Fallback: last word chunk after swap keywords anywhere in message
    match = re.search(
        r"(?:swap|replace|don'?t have|dont have)\s+(.+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip(" .!?")

    return None


async def handle_swap(
    db: AsyncSession,
    client: Client,
    to_number: str,
    message: str,
) -> None:
    food_name = extract_food_item(message)
    if not food_name:
        await whatsapp_service.send_text_message(
            to_number,
            "Which food do you want to swap? Try: *SWAP paneer*",
            db=db,
            client_id=client.id,
            dietitian_id=client.dietitian_id,
        )
        return

    meal_context = None
    plan_day = await get_active_plan_day(db, client)
    if plan_day:
        _, day = plan_day
        meal_type = infer_current_meal_type(client=client)
        plan_item = find_plan_item(day, meal_type)
        if plan_item:
            meal_context = (
                f"{meal_type_label(meal_type)}: {plan_item.food_name} "
                f"({plan_item.portion_description})"
            )

    reply = await suggest_alternatives(client, food_name, meal_context)
    await whatsapp_service.send_text_message(
        to_number,
        reply,
        db=db,
        client_id=client.id,
        dietitian_id=client.dietitian_id,
    )
