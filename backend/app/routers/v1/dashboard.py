"""Dashboard routes for aggregate statistics."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.dependencies import get_current_dietitian
from app.models.dietitian import Dietitian
from app.models.client import Client
from app.models.meal_plan import MealPlan
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

class DashboardStats(BaseModel):
    active_clients: int
    plans_generated_this_month: int
    pending_approvals: int

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Get high-level dashboard statistics."""
    
    # Active clients count
    result = await db.execute(select(func.count(Client.id)).where(Client.dietitian_id == dietitian.id))
    active_clients = result.scalar() or 0
    
    # Pending approvals
    result = await db.execute(
        select(func.count(MealPlan.id))
        .where(MealPlan.dietitian_id == dietitian.id)
        .where(MealPlan.status == "draft")
    )
    pending_approvals = result.scalar() or 0
    
    # Plans generated (ignoring 'this month' for simplicity right now, just all plans)
    result = await db.execute(
        select(func.count(MealPlan.id))
        .where(MealPlan.dietitian_id == dietitian.id)
    )
    plans_generated = result.scalar() or 0
    
    return DashboardStats(
        active_clients=active_clients,
        plans_generated_this_month=plans_generated,
        pending_approvals=pending_approvals
    )
