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
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(kg|k|lbs|lb)?", message_body, re.IGNORECASE)
    if not matches:
        await whatsapp_service.send_text_message(
            to_number,
            "I couldn't understand the weight. Please send it like 'weight 70.5' or '70.5 kg'.",
            db=db,
            client_id=client.id,
            dietitian_id=client.dietitian_id,
        )
        return

    weight_str, unit = matches[-1]
    weight_val = float(weight_str)
    
    unit = unit.lower() if unit else ""
    if unit in ("lbs", "lb"):
        weight_val = weight_val * 0.453592
        weight_val = round(weight_val, 2)

    try:
        data = ProgressLogCreate(
            log_date=datetime.date.today(),
            weight_kg=weight_val,
            notes="Logged via WhatsApp",
            logged_via="whatsapp",
        )
        
        await create_or_update_progress_log(db, client.dietitian_id, client.id, data)

        await whatsapp_service.send_text_message(
            to_number,
            f"📊 Weight logged: {weight_val} kg. Keep going 💪",
            db=db,
            client_id=client.id,
            dietitian_id=client.dietitian_id,
        )
    except Exception as e:
        logger.error(f"Failed to log weight from whatsapp: {e}")
        await whatsapp_service.send_text_message(
            to_number,
            "Sorry, there was an issue logging your weight. Please try again later.",
            db=db,
            client_id=client.id,
            dietitian_id=client.dietitian_id,
        )
