"""Meal Plan routes.

All routes require authentication and enforce multi-tenant isolation.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_dietitian
from app.models.dietitian import Dietitian
from app.schemas.meal_plan import (
    MealPlanCreate,
    MealPlanListCollection,
    MealPlanResponse,
    MealPlanUpdate,
)
from app.services import plan_service

router = APIRouter(tags=["plans"])

# Create prefix for client-scoped routes
clients_router = APIRouter(prefix="/clients/{client_id}/plans", tags=["plans"])
# Create prefix for plan-scoped routes
plans_router = APIRouter(prefix="/plans", tags=["plans"])


@clients_router.post("", response_model=MealPlanResponse, status_code=201)
async def create_plan(
    client_id: uuid.UUID,
    data: MealPlanCreate,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Create a new meal plan for a client."""
    return await plan_service.create_plan(db, dietitian.id, client_id, data)


@clients_router.get("", response_model=MealPlanListCollection)
async def list_plans(
    client_id: uuid.UUID,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """List all meal plans for a client."""
    plans, total = await plan_service.list_plans(db, dietitian.id, client_id)
    return {"plans": plans, "total": total}


@plans_router.get("/{plan_id}", response_model=MealPlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Get a single meal plan by ID with all days and items."""
    return await plan_service.get_plan(db, dietitian.id, plan_id)


@plans_router.put("/{plan_id}", response_model=MealPlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    data: MealPlanUpdate,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Update a meal plan (full replacement of days/items if provided)."""
    return await plan_service.update_plan(db, dietitian.id, plan_id, data)


@plans_router.post("/{plan_id}/approve", response_model=MealPlanResponse)
async def approve_plan(
    plan_id: uuid.UUID,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Approve a meal plan."""
    return await plan_service.approve_plan(db, dietitian.id, plan_id)
