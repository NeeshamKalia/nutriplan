import uuid
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.progress_log import ProgressLog
from app.schemas.progress import ProgressLogCreate, ProgressLogUpdate


async def _verify_client_access(db: AsyncSession, dietitian_id: uuid.UUID, client_id: uuid.UUID) -> None:
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.dietitian_id == dietitian_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )


async def create_or_update_progress_log(
    db: AsyncSession,
    dietitian_id: uuid.UUID,
    client_id: uuid.UUID,
    data: ProgressLogCreate,
) -> ProgressLog:
    await _verify_client_access(db, dietitian_id, client_id)

    # Check if a log for this date already exists
    result = await db.execute(
        select(ProgressLog).where(
            ProgressLog.client_id == client_id,
            ProgressLog.log_date == data.log_date
        )
    )
    existing_log = result.scalar_one_or_none()

    if existing_log:
        for key, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(existing_log, key, value)
        await db.commit()
        await db.refresh(existing_log)
        return existing_log
    else:
        new_log = ProgressLog(
            client_id=client_id,
            **data.model_dump()
        )
        db.add(new_log)
        await db.commit()
        await db.refresh(new_log)
        return new_log


async def list_progress_logs(
    db: AsyncSession, dietitian_id: uuid.UUID, client_id: uuid.UUID
) -> Sequence[ProgressLog]:
    await _verify_client_access(db, dietitian_id, client_id)

    result = await db.execute(
        select(ProgressLog)
        .where(ProgressLog.client_id == client_id)
        .order_by(ProgressLog.log_date.asc())
    )
    return result.scalars().all()


async def update_progress_log(
    db: AsyncSession,
    dietitian_id: uuid.UUID,
    client_id: uuid.UUID,
    log_id: uuid.UUID,
    data: ProgressLogUpdate,
) -> ProgressLog:
    await _verify_client_access(db, dietitian_id, client_id)

    result = await db.execute(
        select(ProgressLog).where(
            ProgressLog.id == log_id, ProgressLog.client_id == client_id
        )
    )
    progress_log = result.scalar_one_or_none()
    if not progress_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Progress log not found"
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(progress_log, key, value)

    await db.commit()
    await db.refresh(progress_log)
    return progress_log


async def delete_progress_log(
    db: AsyncSession, dietitian_id: uuid.UUID, client_id: uuid.UUID, log_id: uuid.UUID
) -> None:
    await _verify_client_access(db, dietitian_id, client_id)

    result = await db.execute(
        select(ProgressLog).where(
            ProgressLog.id == log_id, ProgressLog.client_id == client_id
        )
    )
    progress_log = result.scalar_one_or_none()
    if not progress_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Progress log not found"
        )

    await db.delete(progress_log)
    await db.commit()
