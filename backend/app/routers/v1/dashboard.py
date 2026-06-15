"""Dashboard routes for aggregate statistics."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_dietitian
from app.models.dietitian import Dietitian
from app.schemas.adherence import DashboardOverview
from app.services import adherence_service
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    active_clients: int
    plans_generated_this_month: int
    pending_approvals: int


@router.get("", response_model=DashboardOverview)
async def get_dashboard(
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Get full dashboard overview including adherence stats."""
    return await adherence_service.get_dashboard_overview(db, dietitian.id)


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Get high-level dashboard statistics (legacy endpoint)."""
    overview = await adherence_service.get_dashboard_overview(db, dietitian.id)
    return DashboardStats(
        active_clients=overview.active_clients,
        plans_generated_this_month=overview.plans_this_month,
        pending_approvals=overview.pending_approvals,
    )
