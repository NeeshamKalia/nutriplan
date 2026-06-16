"""Scheduled WhatsApp reminders — morning plan and weekly adherence summary."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logger import get_logger
from app.database import async_session
from app.models.client import Client
from app.models.meal_log import MealLog
from app.models.meal_plan import MealPlan, MealPlanDay
from app.services.adherence_service import _adherence_pct
from app.services.whatsapp_service import whatsapp_service
from app.whatsapp.message_formatter import format_daily_plan, format_weekly_summary

logger = get_logger(__name__)


async def _get_today_day_number(plan: MealPlan) -> int:
    today = date.today()
    if plan.week_start_date:
        delta = (today - plan.week_start_date).days
        return (delta % 7) + 1
    return today.isoweekday()


async def send_morning_reminders() -> int:
    """Send today's meal plan to all active clients with a delivered plan."""
    sent = 0
    async with async_session() as db:
        result = await db.execute(
            select(Client).where(
                Client.status == "active",
                Client.whatsapp_number.isnot(None),
            )
        )
        clients = result.scalars().all()

        for client in clients:
            try:
                greeting = f"🌅 Good morning, {client.full_name.split()[0]}!\n\n"
                plan_result = await db.execute(
                    select(MealPlan)
                    .where(
                        MealPlan.client_id == client.id,
                        MealPlan.status == "delivered",
                    )
                    .order_by(MealPlan.created_at.desc())
                )
                plan = plan_result.scalars().first()
                if not plan:
                    continue

                day_num = await _get_today_day_number(plan)
                day_result = await db.execute(
                    select(MealPlanDay)
                    .options(selectinload(MealPlanDay.items))
                    .where(
                        MealPlanDay.meal_plan_id == plan.id,
                        MealPlanDay.day_number == day_num,
                    )
                )
                day = day_result.scalars().first()
                if not day:
                    continue

                msg = greeting + format_daily_plan(day)
                ok = await whatsapp_service.send_text_message(
                    client.whatsapp_number,
                    msg,
                    db=db,
                    client_id=client.id,
                    dietitian_id=client.dietitian_id,
                )
                if ok:
                    sent += 1
            except Exception as exc:
                logger.error(
                    "Morning reminder failed for client %s: %s",
                    client.id,
                    exc,
                )

    logger.info("Morning reminders sent to %s clients", sent)
    return sent


async def send_weekly_summaries() -> int:
    """Send 7-day adherence summary to active clients."""
    sent = 0
    start_date = date.today() - timedelta(days=6)

    async with async_session() as db:
        result = await db.execute(
            select(Client).where(
                Client.status == "active",
                Client.whatsapp_number.isnot(None),
            )
        )
        clients = result.scalars().all()

        for client in clients:
            try:
                logs_result = await db.execute(
                    select(MealLog).where(
                        MealLog.client_id == client.id,
                        MealLog.log_date >= start_date,
                    )
                )
                logs = logs_result.scalars().all()
                completed = sum(1 for log in logs if log.status == "completed")
                skipped = sum(1 for log in logs if log.status == "skipped")
                deviated = sum(1 for log in logs if log.status == "deviated")
                pct = _adherence_pct(completed, skipped, deviated)

                if completed + skipped + deviated == 0:
                    continue

                msg = format_weekly_summary(
                    client.full_name.split()[0],
                    completed,
                    skipped,
                    deviated,
                    pct,
                )
                ok = await whatsapp_service.send_text_message(
                    client.whatsapp_number,
                    msg,
                    db=db,
                    client_id=client.id,
                    dietitian_id=client.dietitian_id,
                )
                if ok:
                    sent += 1
            except Exception as exc:
                logger.error(
                    "Weekly summary failed for client %s: %s",
                    client.id,
                    exc,
                )

    logger.info("Weekly summaries sent to %s clients", sent)
    return sent
