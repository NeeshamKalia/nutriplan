"""Pydantic schemas for meal adherence stats."""

from datetime import date, datetime

from pydantic import BaseModel


class MealTypeStats(BaseModel):
    meal_type: str
    completed: int
    skipped: int
    deviated: int


class DailyAdherence(BaseModel):
    date: date
    completed: int
    skipped: int
    deviated: int
    adherence_pct: float


class RecentMealLog(BaseModel):
    log_date: date
    meal_type: str
    status: str
    deviation_note: str | None = None
    logged_at: datetime | None = None


class ClientAdherenceResponse(BaseModel):
    client_id: str
    period_days: int
    total_completed: int
    total_skipped: int
    total_deviated: int
    adherence_pct: float
    daily: list[DailyAdherence]
    by_meal_type: list[MealTypeStats]
    recent_logs: list[RecentMealLog]


class AttentionClient(BaseModel):
    id: str
    name: str
    adherence_pct: float
    last_interaction: date | None = None


class RecentActivity(BaseModel):
    type: str
    client: str
    timestamp: datetime
    detail: str | None = None


class DashboardOverview(BaseModel):
    total_clients: int
    active_clients: int
    plans_this_month: int
    pending_approvals: int
    avg_adherence_pct: float
    clients_needing_attention: list[AttentionClient]
    recent_activity: list[RecentActivity]
