"""Protocol template management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_dietitian
from app.models.dietitian import Dietitian
from app.schemas.protocol import (
    ProtocolCreate,
    ProtocolListResponse,
    ProtocolResponse,
    ProtocolUpdate,
)
from app.services import protocol_service

router = APIRouter(prefix="/protocols", tags=["protocols"])


@router.post("", response_model=ProtocolResponse, status_code=201)
async def create_protocol(
    data: ProtocolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    return await protocol_service.create_protocol(db, current_user.id, data)


@router.get("", response_model=ProtocolListResponse)
async def list_protocols(
    search: str | None = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    return await protocol_service.list_protocols(
        db, current_user.id, search=search, active_only=active_only
    )


@router.get("/{protocol_id}", response_model=ProtocolResponse)
async def get_protocol(
    protocol_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    return await protocol_service.get_protocol(db, current_user.id, protocol_id)


@router.put("/{protocol_id}", response_model=ProtocolResponse)
async def update_protocol(
    protocol_id: UUID,
    data: ProtocolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    return await protocol_service.update_protocol(
        db, current_user.id, protocol_id, data
    )


@router.delete("/{protocol_id}", status_code=204)
async def delete_protocol(
    protocol_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dietitian = Depends(get_current_dietitian),
):
    await protocol_service.delete_protocol(db, current_user.id, protocol_id)
