"""Client management service — CRUD with multi-tenant isolation.

CRITICAL: Every query filters by dietitian_id. A dietitian must NEVER
see another dietitian's clients.
"""

import uuid as uuid_mod
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.models.audit_log import AuditLog
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientListResponse, ClientResponse, ClientUpdate

logger = get_logger(__name__)


def _client_to_response(client: Client) -> ClientResponse:
    """Convert a Client model instance to a ClientResponse.

    Handles ARRAY columns that may come back as strings from SQLite.
    """
    def _to_list(val):
        if isinstance(val, list):
            return val
        if isinstance(val, str) and val:
            return [s.strip() for s in val.split(",")]
        return None

    return ClientResponse(
        id=str(client.id),
        dietitian_id=str(client.dietitian_id),
        full_name=client.full_name,
        whatsapp_number=client.whatsapp_number,
        email=client.email,
        age=client.age,
        gender=client.gender,
        height_cm=float(client.height_cm) if client.height_cm else None,
        weight_kg=float(client.weight_kg) if client.weight_kg else None,
        target_weight_kg=float(client.target_weight_kg) if client.target_weight_kg else None,
        activity_level=client.activity_level,
        medical_conditions=_to_list(client.medical_conditions),
        allergies=_to_list(client.allergies),
        food_preferences=_to_list(client.food_preferences),
        cuisine_preference=client.cuisine_preference,
        dietary_type=client.dietary_type,
        primary_goal=client.primary_goal,
        monthly_food_budget_inr=client.monthly_food_budget_inr,
        daily_calorie_target=client.daily_calorie_target,
        meals_per_day=client.meals_per_day,
        meal_timing_preferences=client.meal_timing_preferences,
        notes=client.notes,
        lifestyle_notes=client.lifestyle_notes,
        status=client.status,
        archived_at=client.archived_at,
        onboarded_at=client.onboarded_at,
        created_at=client.created_at,
        updated_at=client.updated_at,
    )


async def create_client(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, data: ClientCreate
) -> ClientResponse:
    """Create a new client, checking WhatsApp number uniqueness per dietitian."""
    # Check unique WhatsApp within this dietitian
    result = await db.execute(
        select(Client).where(
            Client.dietitian_id == dietitian_id,
            Client.whatsapp_number == data.whatsapp_number,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Client with WhatsApp number {data.whatsapp_number} already exists",
        )

    client = Client(
        dietitian_id=dietitian_id,
        **data.model_dump(exclude_none=True),
    )
    db.add(client)

    # Audit log
    await db.flush()
    db.add(
        AuditLog(
            dietitian_id=dietitian_id,
            action="client_created",
            entity_type="client",
            entity_id=client.id,
        )
    )

    await db.commit()
    await db.refresh(client)

    logger.info(
        "Client created",
        extra={"client_id": str(client.id), "dietitian_id": str(dietitian_id)},
    )
    return _client_to_response(client)


async def list_clients(
    db: AsyncSession,
    dietitian_id: uuid_mod.UUID,
    search: str | None = None,
    client_status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> ClientListResponse:
    """List clients for a dietitian with optional search and status filter."""
    # Base query — always filter by dietitian_id (multi-tenant)
    base_query = select(Client).where(Client.dietitian_id == dietitian_id)

    if client_status:
        base_query = base_query.where(Client.status == client_status)

    if search:
        search_term = f"%{search}%"
        base_query = base_query.where(Client.full_name.ilike(search_term))

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = base_query.order_by(Client.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    clients = result.scalars().all()

    return ClientListResponse(
        clients=[_client_to_response(c) for c in clients],
        total=total,
        limit=limit,
        offset=offset,
    )


async def get_client(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, client_id: uuid_mod.UUID
) -> ClientResponse:
    """Get a single client by ID, enforcing tenant isolation."""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.dietitian_id == dietitian_id,
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return _client_to_response(client)


async def update_client(
    db: AsyncSession,
    dietitian_id: uuid_mod.UUID,
    client_id: uuid_mod.UUID,
    data: ClientUpdate,
) -> ClientResponse:
    """Partially update a client profile."""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.dietitian_id == dietitian_id,
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Check unique WhatsApp if being changed
    update_data = data.model_dump(exclude_unset=True)
    if "whatsapp_number" in update_data and update_data["whatsapp_number"] != client.whatsapp_number:
        existing = await db.execute(
            select(Client).where(
                Client.dietitian_id == dietitian_id,
                Client.whatsapp_number == update_data["whatsapp_number"],
                Client.id != client_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another client with WhatsApp number {update_data['whatsapp_number']} already exists",
            )

    for field, value in update_data.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)

    logger.info(
        "Client updated",
        extra={"client_id": str(client_id), "dietitian_id": str(dietitian_id)},
    )
    return _client_to_response(client)


async def archive_client(
    db: AsyncSession, dietitian_id: uuid_mod.UUID, client_id: uuid_mod.UUID
) -> ClientResponse:
    """Soft-delete a client by setting status='archived' and archived_at."""
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.dietitian_id == dietitian_id,
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    client.status = "archived"
    client.archived_at = datetime.now(timezone.utc)

    # Audit log
    db.add(
        AuditLog(
            dietitian_id=dietitian_id,
            action="client_archived",
            entity_type="client",
            entity_id=client.id,
        )
    )

    await db.commit()
    await db.refresh(client)

    logger.info(
        "Client archived",
        extra={"client_id": str(client_id), "dietitian_id": str(dietitian_id)},
    )
    return _client_to_response(client)
