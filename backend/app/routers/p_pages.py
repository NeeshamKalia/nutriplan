"""Spec-aligned public page routes (non-versioned /p/* paths)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.public import IntakeResponse, IntakeSubmit
from app.services import intake_service

router = APIRouter(tags=["public-pages"])


@router.post("/p/{slug}/intake", response_model=IntakeResponse, status_code=201)
async def submit_intake(
    slug: str, data: IntakeSubmit, db: AsyncSession = Depends(get_db)
):
    """Spec-aligned intake endpoint: POST /p/:slug/intake."""
    return await intake_service.submit_intake(db, slug, data)
