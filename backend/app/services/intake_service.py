"""Public intake form — creates lead clients from landing page."""

import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.models.audit_log import AuditLog
from app.models.client import Client
from app.models.dietitian import Dietitian
from app.schemas.public import IntakeResponse, IntakeSubmit

logger = get_logger(__name__)


def _normalize_whatsapp(number: str) -> str:
    """Normalize to +91XXXXXXXXXX style."""
    cleaned = re.sub(r"[^\d+]", "", number.strip())
    if cleaned.startswith("+"):
        return cleaned
    if cleaned.startswith("91") and len(cleaned) >= 12:
        return f"+{cleaned}"
    if len(cleaned) == 10:
        return f"+91{cleaned}"
    return f"+{cleaned}" if not cleaned.startswith("+") else cleaned


async def submit_intake(
    db: AsyncSession, slug: str, data: IntakeSubmit
) -> IntakeResponse:
    """Create a lead client from a public intake form."""
    result = await db.execute(
        select(Dietitian).where(Dietitian.slug == slug, Dietitian.is_active)
    )
    dietitian = result.scalar_one_or_none()
    if not dietitian:
        raise HTTPException(status_code=404, detail="Dietitian not found")

    whatsapp = _normalize_whatsapp(data.whatsapp_number)

    existing = await db.execute(
        select(Client).where(
            Client.dietitian_id == dietitian.id,
            Client.whatsapp_number == whatsapp,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A profile with this WhatsApp number already exists. "
            "Your dietitian will be in touch!",
        )

    client = Client(
        dietitian_id=dietitian.id,
        full_name=data.full_name.strip(),
        whatsapp_number=whatsapp,
        email=data.email,
        age=data.age,
        primary_goal=data.primary_goal,
        dietary_type=data.dietary_type,
        notes=data.notes,
        status="lead",
    )
    db.add(client)
    await db.flush()

    db.add(
        AuditLog(
            dietitian_id=dietitian.id,
            action="client_intake",
            entity_type="client",
            entity_id=client.id,
        )
    )
    await db.commit()

    logger.info(
        "Intake submitted",
        extra={
            "client_id": str(client.id),
            "dietitian_id": str(dietitian.id),
            "slug": slug,
        },
    )

    return IntakeResponse(
        message="Thank you! Your dietitian will contact you soon on WhatsApp.",
        client_id=str(client.id),
    )
