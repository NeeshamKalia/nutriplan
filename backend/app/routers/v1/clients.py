"""Client management routes.

All routes require authentication and enforce multi-tenant isolation.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_dietitian
from app.models.dietitian import Dietitian
from app.schemas.client import (
    ClientCreate,
    ClientListResponse,
    ClientResponse,
    ClientUpdate,
)
from app.services import client_service

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(
    data: ClientCreate,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client with health profile."""
    return await client_service.create_client(db, dietitian.id, data)


@router.get("", response_model=ClientListResponse)
async def list_clients(
    search: str | None = Query(None, description="Search by name"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """List clients with optional search and status filter."""
    return await client_service.list_clients(
        db, dietitian.id, search=search, client_status=status, limit=limit, offset=offset
    )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Get a single client by ID."""
    return await client_service.get_client(db, dietitian.id, client_id)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Update client profile (partial update)."""
    return await client_service.update_client(db, dietitian.id, client_id, data)


@router.delete("/{client_id}", response_model=ClientResponse)
async def archive_client(
    client_id: uuid.UUID,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Archive a client (soft delete)."""
    return await client_service.archive_client(db, dietitian.id, client_id)
