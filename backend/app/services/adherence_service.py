"""Meal adherence statistics for dietitian dashboard and client detail."""

import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.meal_log import MealLog
from app.models.meal_plan import MealPlan
from app.schemas.adherence import (
    AttentionClient,
    ClientAdherenceResponse,
    DailyAdherence,
    DashboardOverview,
    MealTypeStats,
    RecentActivity,
    RecentMealLog,
)

LOOKBACK_DAYS = 7
ATTENTION_THRESHOLD_PCT = 60


def _adherence_pct(completed: int, skipped: int, deviated: int) -> float:
    total = completed + skipped + deviated
    if total == 0:
        return 0.0
    return round((completed / total) * 100, 1)


async def _get_client_or_404(
    db: AsyncSession, dietitian_id: uuid.UUID, client_id: uuid.UUID
) -> Client:
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.dietitian_id == dietitian_id,
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return client


async def get_client_adherence(
    db: AsyncSession,
    dietitian_id: uuid.UUID,
    client_id: uuid.UUID,
    days: int = LOOKBACK_DAYS,
) -> ClientAdherenceResponse:
    """Return adherence stats for a single client over the lookback window."""
    await _get_client_or_404(db, dietitian_id, client_id)

    start_date = date.today() - timedelta(days=days - 1)
    result = await db.execute(
        select(MealLog)
        .where(
            MealLog.client_id == client_id,
            MealLog.log_date >= start_date,
        )
        .order_by(MealLog.log_date.desc(), MealLog.logged_at.desc())
    )
    logs = result.scalars().all()

    total_completed = sum(1 for log in logs if log.status == "completed")
    total_skipped = sum(1 for log in logs if log.status == "skipped")
    total_deviated = sum(1 for log in logs if log.status == "deviated")

    daily_map: dict[date, dict[str, int]] = defaultdict(
        lambda: {"completed": 0, "skipped": 0, "deviated": 0}
    )
    meal_type_map: dict[str, dict[str, int]] = defaultdict(
        lambda: {"completed": 0, "skipped": 0, "deviated": 0}
    )

    for log in logs:
        daily_map[log.log_date][log.status] += 1
        meal_type_map[log.meal_type][log.status] += 1

    daily: list[DailyAdherence] = []
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        counts = daily_map.get(day, {"completed": 0, "skipped": 0, "deviated": 0})
        daily.append(
            DailyAdherence(
                date=day,
                completed=counts["completed"],
                skipped=counts["skipped"],
                deviated=counts["deviated"],
                adherence_pct=_adherence_pct(
                    counts["completed"], counts["skipped"], counts["deviated"]
                ),
            )
        )

    by_meal_type = [
        MealTypeStats(
            meal_type=meal_type,
            completed=counts["completed"],
            skipped=counts["skipped"],
            deviated=counts["deviated"],
        )
        for meal_type, counts in sorted(meal_type_map.items())
    ]

    recent_logs = [
        RecentMealLog(
            log_date=log.log_date,
            meal_type=log.meal_type,
            status=log.status,
            deviation_note=log.deviation_note,
            logged_at=log.logged_at,
        )
        for log in logs[:20]
    ]

    return ClientAdherenceResponse(
        client_id=str(client_id),
        period_days=days,
        total_completed=total_completed,
        total_skipped=total_skipped,
        total_deviated=total_deviated,
        adherence_pct=_adherence_pct(total_completed, total_skipped, total_deviated),
        daily=daily,
        by_meal_type=by_meal_type,
        recent_logs=recent_logs,
    )


async def _client_adherence_summary(
    db: AsyncSession,
    client_id: uuid.UUID,
    days: int = LOOKBACK_DAYS,
) -> tuple[int, int, int, date | None]:
    """Return completed/skipped/deviated counts and last log date for a client."""
    start_date = date.today() - timedelta(days=days - 1)
    result = await db.execute(
        select(MealLog).where(
            MealLog.client_id == client_id,
            MealLog.log_date >= start_date,
        )
    )
    logs = result.scalars().all()
    if not logs:
        return 0, 0, 0, None

    completed = sum(1 for log in logs if log.status == "completed")
    skipped = sum(1 for log in logs if log.status == "skipped")
    deviated = sum(1 for log in logs if log.status == "deviated")
    last_date = max(log.log_date for log in logs)
    return completed, skipped, deviated, last_date


async def get_dashboard_overview(
    db: AsyncSession,
    dietitian_id: uuid.UUID,
) -> DashboardOverview:
    """Aggregate practice-wide stats including adherence and attention list."""
    result = await db.execute(
        select(Client).where(Client.dietitian_id == dietitian_id)
    )
    all_clients = result.scalars().all()
    total_clients = len(all_clients)
    active_clients = sum(1 for c in all_clients if c.status == "active")

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(func.count(MealPlan.id))
        .where(MealPlan.dietitian_id == dietitian_id)
        .where(MealPlan.created_at >= month_start)
    )
    plans_this_month = result.scalar() or 0

    result = await db.execute(
        select(func.count(MealPlan.id))
        .where(MealPlan.dietitian_id == dietitian_id)
        .where(MealPlan.status == "draft")
    )
    pending_approvals = result.scalar() or 0

    adherence_scores: list[float] = []
    attention_clients: list[AttentionClient] = []

    for client in all_clients:
        if client.status != "active":
            continue

        completed, skipped, deviated, last_date = await _client_adherence_summary(
            db, client.id
        )
        total_logged = completed + skipped + deviated
        if total_logged == 0:
            continue

        pct = _adherence_pct(completed, skipped, deviated)
        adherence_scores.append(pct)

        if pct < ATTENTION_THRESHOLD_PCT:
            attention_clients.append(
                AttentionClient(
                    id=str(client.id),
                    name=client.full_name,
                    adherence_pct=pct,
                    last_interaction=last_date,
                )
            )

    avg_adherence = (
        round(sum(adherence_scores) / len(adherence_scores), 1)
        if adherence_scores
        else 0.0
    )
    attention_clients.sort(key=lambda c: c.adherence_pct)

    recent_activity = await _get_recent_activity(db, dietitian_id)

    return DashboardOverview(
        total_clients=total_clients,
        active_clients=active_clients,
        plans_this_month=plans_this_month,
        pending_approvals=pending_approvals,
        avg_adherence_pct=avg_adherence,
        clients_needing_attention=attention_clients[:10],
        recent_activity=recent_activity,
    )


async def _get_recent_activity(
    db: AsyncSession,
    dietitian_id: uuid.UUID,
    limit: int = 10,
) -> list[RecentActivity]:
    """Build a mixed feed of recent meal logs and plan deliveries."""
    activities: list[RecentActivity] = []

    result = await db.execute(
        select(MealLog, Client.full_name)
        .join(Client, MealLog.client_id == Client.id)
        .where(Client.dietitian_id == dietitian_id)
        .order_by(MealLog.logged_at.desc())
        .limit(limit)
    )
    for log, client_name in result.all():
        activities.append(
            RecentActivity(
                type="meal_logged",
                client=client_name,
                timestamp=log.logged_at or datetime.now(timezone.utc),
                detail=f"{log.meal_type.replace('_', ' ')} — {log.status}",
            )
        )

    result = await db.execute(
        select(MealPlan, Client.full_name)
        .join(Client, MealPlan.client_id == Client.id)
        .where(Client.dietitian_id == dietitian_id)
        .where(MealPlan.status == "delivered")
        .where(MealPlan.delivered_at.isnot(None))
        .order_by(MealPlan.delivered_at.desc())
        .limit(limit)
    )
    for plan, client_name in result.all():
        activities.append(
            RecentActivity(
                type="plan_delivered",
                client=client_name,
                timestamp=plan.delivered_at,
                detail=plan.title,
            )
        )

    activities.sort(key=lambda a: a.timestamp, reverse=True)
    return activities[:limit]
