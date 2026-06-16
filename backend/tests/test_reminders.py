"""Tests for scheduled WhatsApp reminders."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.client import Client
from app.models.dietitian import Dietitian
from app.models.meal_log import MealLog
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanItem
from app.scheduler.reminders import start_scheduler, stop_scheduler
from app.services.reminder_service import send_morning_reminders, send_weekly_summaries
from app.whatsapp.message_formatter import format_weekly_summary

import app.models  # noqa: F401
from tests.conftest import _make_sqlite_compatible

_make_sqlite_compatible()


@pytest_asyncio.fixture
async def reminder_db():
    """SQLite DB with dietitian, active client, delivered plan, and meal logs."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        dietitian = Dietitian(
            email="reminders@nutriplan.in",
            password_hash="hash",
            full_name="Dr. Reminder",
            slug="dr-reminder",
        )
        session.add(dietitian)
        await session.flush()

        client = Client(
            dietitian_id=dietitian.id,
            full_name="Priya Sharma",
            whatsapp_number="+919888877777",
            status="active",
        )
        session.add(client)
        await session.flush()

        plan = MealPlan(
            client_id=client.id,
            dietitian_id=dietitian.id,
            title="Week 1",
            week_start_date=date.today(),
            status="delivered",
        )
        session.add(plan)
        await session.flush()

        day = MealPlanDay(
            meal_plan_id=plan.id,
            day_number=1,
            day_label="Today",
            total_calories=500,
        )
        session.add(day)
        await session.flush()

        session.add(
            MealPlanItem(
                meal_plan_day_id=day.id,
                meal_type="breakfast",
                sort_order=1,
                food_name="Poha",
                portion_description="1 bowl",
                calories=250,
                protein_g=8,
            )
        )

        log_date = date.today() - timedelta(days=1)
        session.add_all(
            [
                MealLog(
                    client_id=client.id,
                    log_date=log_date,
                    meal_type="breakfast",
                    status="completed",
                ),
                MealLog(
                    client_id=client.id,
                    log_date=log_date,
                    meal_type="lunch",
                    status="skipped",
                ),
            ]
        )
        await session.commit()

    with patch("app.services.reminder_service.async_session", session_factory):
        yield session_factory

    await engine.dispose()


def test_format_weekly_summary_high_adherence():
    msg = format_weekly_summary("Priya", 28, 2, 1, 90.3)
    assert "Priya" in msg
    assert "90%" in msg
    assert "Great consistency" in msg


def test_format_weekly_summary_low_adherence():
    msg = format_weekly_summary("Rahul", 5, 10, 3, 27.8)
    assert "Rahul" in msg
    assert "today" in msg.lower()


@pytest.mark.asyncio
async def test_send_morning_reminders_sends_for_delivered_plan(reminder_db):
    with patch(
        "app.services.reminder_service.whatsapp_service.send_text_message",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:
        sent = await send_morning_reminders()

    assert sent == 1
    mock_send.assert_called_once()
    message = mock_send.call_args.args[1]
    assert "Good morning" in message
    assert "Poha" in message


@pytest.mark.asyncio
async def test_send_morning_reminders_skips_without_delivered_plan(reminder_db):
    async with reminder_db() as session:
        result = await session.execute(select(MealPlan))
        plan = result.scalars().first()
        plan.status = "draft"
        await session.commit()

    with patch(
        "app.services.reminder_service.whatsapp_service.send_text_message",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:
        sent = await send_morning_reminders()

    assert sent == 0
    mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_send_weekly_summaries_sends_when_logs_exist(reminder_db):
    with patch(
        "app.services.reminder_service.whatsapp_service.send_text_message",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:
        sent = await send_weekly_summaries()

    assert sent == 1
    mock_send.assert_called_once()
    message = mock_send.call_args.args[1]
    assert "Weekly Check-in" in message
    assert "Priya" in message


@pytest.mark.asyncio
async def test_send_weekly_summaries_skips_without_logs(reminder_db):
    async with reminder_db() as session:
        await session.execute(delete(MealLog))
        await session.commit()

    with patch(
        "app.services.reminder_service.whatsapp_service.send_text_message",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:
        sent = await send_weekly_summaries()

    assert sent == 0
    mock_send.assert_not_called()


def test_start_scheduler_disabled(monkeypatch):
    stop_scheduler()
    monkeypatch.setattr("app.scheduler.reminders.settings.ENABLE_SCHEDULER", False)
    assert start_scheduler() is None


def test_start_scheduler_registers_jobs(monkeypatch):
    stop_scheduler()
    monkeypatch.setattr("app.scheduler.reminders.settings.ENABLE_SCHEDULER", True)
    scheduler = start_scheduler()
    try:
        assert scheduler is not None
        job_ids = {job.id for job in scheduler.get_jobs()}
        assert job_ids == {"morning_reminders", "weekly_summaries"}
    finally:
        stop_scheduler()
