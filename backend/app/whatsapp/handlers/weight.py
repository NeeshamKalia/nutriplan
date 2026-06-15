import datetime
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.models.client import Client
from app.schemas.progress import ProgressLogCreate
from app.services.progress_service import create_or_update_progress_log
from app.services.whatsapp_service import whatsapp_service

logger = get_logger(__name__)


async def handle_weight(
    db: AsyncSession, client: Client, to_number: str, message_body: str
):
    """Handle weight logging via WhatsApp."""

    # Extract weight from message
    match = re.search(r"(\d+(\.\d+)?)", message_body)
    if not match:
        await whatsapp_service.send_text_message(
            to_number,
            "I couldn't understand the weight. Please send it like 'weight 70.5' or '70.5 kg'.",
        )
        return

    weight_val = float(match.group(1))

    try:
        data = ProgressLogCreate(
            log_date=datetime.date.today(),
            weight_kg=weight_val,
            notes="Logged via WhatsApp",
            logged_via="whatsapp",
        )
        
        await create_or_update_progress_log(db, client.dietitian_id, client.id, data)

        await whatsapp_service.send_text_message(
            to_number, f"📊 Weight logged: {weight_val} kg. Keep going 💪"
        )
    except Exception as e:
        logger.error(f"Failed to log weight from whatsapp: {e}")
        await whatsapp_service.send_text_message(
            to_number,
            "Sorry, there was an issue logging your weight. Please try again later.",
        )
