from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProgressLogBase(BaseModel):
    log_date: date
    weight_kg: Optional[float] = None
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    notes: Optional[str] = None


class ProgressLogCreate(ProgressLogBase):
    logged_via: Optional[str] = "dashboard"


class ProgressLogUpdate(BaseModel):
    weight_kg: Optional[float] = None
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    notes: Optional[str] = None


class ProgressLogResponse(ProgressLogBase):
    id: UUID
    client_id: UUID
    logged_via: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
