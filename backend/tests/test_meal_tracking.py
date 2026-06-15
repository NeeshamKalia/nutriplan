"""Tests for WhatsApp meal tracking handlers."""

from datetime import date, datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.client import Client
from app.models.dietitian import Dietitian
from app.models.meal_log import MealLog
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanItem
from app.whatsapp.handlers.deviation import handle_deviation, parse_deviation
from app.whatsapp.handlers.done import handle_done
from app.whatsapp.handlers.swap import extract_food_item, handle_swap
from app.whatsapp.meal_context import infer_current_meal_type, meal_type_label

import app.models  # noqa: F401
from tests.conftest import _make_sqlite_compatible

_make_sqlite_compatible()


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        dietitian = Dietitian(
            email="diet@nutriplan.in",
            password_hash="hash",
            full_name="Dr. Neha",
            slug="dr-neha",
        )
        session.add(dietitian)
        await session.flush()

        client = Client(
            dietitian_id=dietitian.id,
            full_name="Riya",
            whatsapp_number="+919999999999",
            dietary_type="vegetarian",
            allergies=["peanuts"],
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
            day_label="Monday",
            total_calories=550,
        )
        session.add(day)
        await session.flush()

        breakfast = MealPlanItem(
            meal_plan_day_id=day.id,
            meal_type="breakfast",
            sort_order=1,
            food_name="Oats Chilla",
            portion_description="2 medium",
            calories=250,
            protein_g=10,
        )
        lunch = MealPlanItem(
            meal_plan_day_id=day.id,
            meal_type="lunch",
            sort_order=2,
            food_name="Dal Makhani",
            portion_description="1 bowl",
            calories=300,
            protein_g=15,
        )
        session.add_all([breakfast, lunch])
        await session.commit()

        yield session, client, breakfast, lunch

    await engine.dispose()


def test_infer_current_meal_type_defaults():
    assert infer_current_meal_type(datetime(2026, 6, 15, 8, 0)) == "breakfast"
    assert infer_current_meal_type(datetime(2026, 6, 15, 13, 0)) == "lunch"
    assert infer_current_meal_type(datetime(2026, 6, 15, 20, 0)) == "dinner"


def test_parse_deviation():
    assert parse_deviation("Had pizza for dinner") == ("deviated", "dinner")
    assert parse_deviation("Skipped lunch") == ("skipped", "lunch")
    assert parse_deviation("Ate biryani instead") == ("deviated", None)


def test_extract_food_item():
    assert extract_food_item("Swap paneer") == "paneer"
    assert extract_food_item("I don't have tofu") == "tofu"
    assert extract_food_item("replace dal makhani") == "dal makhani"


@pytest.mark.asyncio
async def test_handle_done_logs_completed_meal(db_session):
    db, client, breakfast, _ = db_session

    with patch(
        "app.whatsapp.handlers.done.whatsapp_service.send_text_message",
        new_callable=AsyncMock,
    ) as send_mock:
        with patch(
            "app.whatsapp.handlers.done.infer_current_meal_type",
            return_value="breakfast",
        ):
            await handle_done(db, client, "919999999999")

    send_mock.assert_awaited_once()
    assert "Breakfast logged" in send_mock.await_args.args[1]

    result = await db.execute(
        MealLog.__table__.select().where(MealLog.client_id == client.id)
    )
    logs = result.fetchall()
    assert len(logs) == 1
    assert logs[0].status == "completed"
    assert logs[0].meal_type == "breakfast"
    assert logs[0].meal_plan_item_id == breakfast.id


@pytest.mark.asyncio
async def test_handle_done_all_meals_completed_message(db_session):
    db, client, breakfast, lunch = db_session

    db.add(
        MealLog(
            client_id=client.id,
            meal_plan_item_id=lunch.id,
            log_date=date.today(),
            meal_type="lunch",
            status="completed",
            logged_via="whatsapp",
        )
    )
    await db.commit()

    with patch(
        "app.whatsapp.handlers.done.whatsapp_service.send_text_message",
        new_callable=AsyncMock,
    ) as send_mock:
        with patch(
            "app.whatsapp.handlers.done.infer_current_meal_type",
            return_value="breakfast",
        ):
            await handle_done(db, client, "919999999999")

    assert "All meals completed" in send_mock.await_args.args[1]


@pytest.mark.asyncio
async def test_handle_deviation_logs_skipped_meal(db_session):
    db, client, _, lunch = db_session

    with patch(
        "app.whatsapp.handlers.deviation.whatsapp_service.send_text_message",
        new_callable=AsyncMock,
    ) as send_mock:
        with patch(
            "app.whatsapp.handlers.deviation.infer_current_meal_type",
            return_value="lunch",
        ):
            await handle_deviation(db, client, "919999999999", "Skipped lunch")

    send_mock.assert_awaited_once()
    assert "skipped" in send_mock.await_args.args[1].lower()

    result = await db.execute(
        MealLog.__table__.select().where(MealLog.client_id == client.id)
    )
    log = result.fetchone()
    assert log.status == "skipped"
    assert log.meal_type == "lunch"
    assert log.deviation_note == "Skipped lunch"


@pytest.mark.asyncio
async def test_handle_deviation_logs_food_swap_note(db_session):
    db, client, _, _ = db_session

    with patch(
        "app.whatsapp.handlers.deviation.whatsapp_service.send_text_message",
        new_callable=AsyncMock,
    ):
        with patch(
            "app.whatsapp.handlers.deviation.infer_current_meal_type",
            return_value="dinner",
        ):
            await handle_deviation(
                db, client, "919999999999", "Had pizza for dinner"
            )

    result = await db.execute(
        MealLog.__table__.select().where(MealLog.client_id == client.id)
    )
    log = result.fetchone()
    assert log.status == "deviated"
    assert log.meal_type == "dinner"


@pytest.mark.asyncio
async def test_handle_swap_sends_alternatives(db_session):
    db, client, _, _ = db_session

    with patch(
        "app.whatsapp.handlers.swap.suggest_alternatives",
        new_callable=AsyncMock,
        return_value="Try tofu instead.",
    ) as suggest_mock:
        with patch(
            "app.whatsapp.handlers.swap.whatsapp_service.send_text_message",
            new_callable=AsyncMock,
        ) as send_mock:
            await handle_swap(db, client, "919999999999", "Swap paneer")

    suggest_mock.assert_awaited_once()
    assert suggest_mock.await_args.args[0] == client
    assert suggest_mock.await_args.args[1] == "paneer"
    send_mock.assert_awaited_once_with("919999999999", "Try tofu instead.")


def test_meal_type_label():
    assert meal_type_label("evening_snack") == "Evening Snack"
