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
    MealPlanValidationsList,
    GeneratePlanRequest,
    RegeneratePlanRequest,
)
from app.schemas.protocol import ProtocolResponse, SavePlanAsProtocolRequest
from app.services import plan_service, protocol_service

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


@plans_router.get("/{plan_id}/validations", response_model=MealPlanValidationsList)
async def get_plan_validations(
    plan_id: uuid.UUID,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Get AI validation results for a meal plan."""
    validations = await plan_service.get_plan_validations(
        db, dietitian.id, plan_id
    )
    return {"validations": validations, "total": len(validations)}


@plans_router.post("/{plan_id}/regenerate", response_model=MealPlanResponse)
async def regenerate_plan(
    plan_id: uuid.UUID,
    data: RegeneratePlanRequest,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a draft plan with AI using optional new instructions."""
    return await plan_service.regenerate_plan(db, dietitian.id, plan_id, data)


@clients_router.post("/generate", response_model=MealPlanResponse, status_code=201)
async def generate_plan(
    client_id: uuid.UUID,
    data: GeneratePlanRequest,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new meal plan using AI."""
    return await plan_service.generate_plan_for_client(db, dietitian.id, client_id, data)


@plans_router.post("/{plan_id}/save-as-protocol", response_model=ProtocolResponse, status_code=201)
async def save_plan_as_protocol(
    plan_id: uuid.UUID,
    data: SavePlanAsProtocolRequest,
    dietitian: Dietitian = Depends(get_current_dietitian),
    db: AsyncSession = Depends(get_db),
):
    """Save an existing meal plan as a reusable protocol template."""
    return await protocol_service.save_plan_as_protocol(
        db, dietitian.id, plan_id, data
    )
