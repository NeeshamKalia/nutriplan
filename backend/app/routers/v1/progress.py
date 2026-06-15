import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_dietitian
from app.models.dietitian import Dietitian
from app.schemas.progress import (
    ProgressLogCreate,
    ProgressLogResponse,
    ProgressLogUpdate,
)
from app.services import progress_service

router = APIRouter(prefix="/clients/{client_id}/progress", tags=["progress"])


@router.post(
    "",
    response_model=ProgressLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def log_progress(
    client_id: uuid.UUID,
    data: ProgressLogCreate,
    db: AsyncSession = Depends(get_db),
    dietitian: Dietitian = Depends(get_current_dietitian),
):
    return await progress_service.create_or_update_progress_log(
        db, dietitian.id, client_id, data
    )


@router.get("", response_model=List[ProgressLogResponse])
async def list_progress_logs(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    dietitian: Dietitian = Depends(get_current_dietitian),
):
    return await progress_service.list_progress_logs(db, dietitian.id, client_id)


@router.put("/{log_id}", response_model=ProgressLogResponse)
async def update_progress_log(
    client_id: uuid.UUID,
    log_id: uuid.UUID,
    data: ProgressLogUpdate,
    db: AsyncSession = Depends(get_db),
    dietitian: Dietitian = Depends(get_current_dietitian),
):
    return await progress_service.update_progress_log(
        db, dietitian.id, client_id, log_id, data
    )


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_progress_log(
    client_id: uuid.UUID,
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    dietitian: Dietitian = Depends(get_current_dietitian),
):
    await progress_service.delete_progress_log(
        db, dietitian.id, client_id, log_id
    )
