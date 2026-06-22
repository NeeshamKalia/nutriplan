"""Tests for LangGraph plan generation workflow."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.plan_generator_langgraph import (
    MAX_SAFETY_RETRIES,
    format_output,
    parse_profile,
    retrieve_context,
    route_after_safety,
    validate_safety,
    generate_meal_plan,
)


def _valid_plan() -> dict:
    return {
        "days": [
            {
                "day_number": i,
                "day_label": f"Day {i}",
                "items": [
                    {
                        "meal_type": "breakfast",
                        "food_name": "Roti",
                        "portion_description": "2 medium",
                        "portion_grams": 80,
                        "calories": 200,
                        "protein_g": 6,
                        "carbs_g": 40,
                        "fat_g": 2,
                    }
                ],
            }
            for i in range(1, 8)
        ]
    }


def _mock_client(**overrides):
    defaults = {
        "full_name": "Priya Kapoor",
        "age": 28,
        "gender": "female",
        "weight_kg": 72,
        "target_weight_kg": 60,
        "primary_goal": "weight_loss",
        "daily_calorie_target": 1600,
        "activity_level": "light",
        "dietary_type": "veg",
        "allergies": ["peanuts"],
        "medical_conditions": ["PCOS"],
        "food_preferences": [],
        "cuisine_preference": "north_indian",
        "monthly_food_budget_inr": 8000,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_parse_profile_builds_user_prompt():
    state = parse_profile(
        {
            "client_profile": _mock_client(),
            "food_items": [],
            "custom_instructions": "More protein",
        }
    )
    assert "Priya Kapoor" in state["user_prompt"]
    assert "More protein" in state["user_prompt"]
    assert state["safety_retry_count"] == 0


def test_retrieve_context_appends_protocol_and_history():
    state = retrieve_context(
        {
            "user_prompt": "Base prompt",
            "protocol_context": "PCOS protocol",
            "previous_plans_context": "Last week: dal-roti plan",
        }
    )
    assert "PROTOCOL GUIDELINES" in state["user_prompt"]
    assert "PREVIOUS PLANS" in state["user_prompt"]


def test_validate_safety_detects_allergen_violation():
    bad_plan = _valid_plan()
    bad_plan["days"][0]["items"][0]["food_name"] = "Peanut chutney"

    state = validate_safety(
        {
            "client_profile": _mock_client(allergies=["peanuts"]),
            "plan_data": bad_plan,
        }
    )
    assert any(not v["passed"] for v in state["validations"])


def test_route_after_safety_retries_on_critical_failure():
    validations = [
        {
            "type": "allergens",
            "passed": False,
            "severity": "critical",
            "message": "Allergen found",
        }
    ]
    assert route_after_safety({"validations": validations, "safety_retry_count": 0}) == "prepare_retry"
    # Retries exhausted with critical failures — aborts generation
    assert route_after_safety({"validations": validations, "safety_retry_count": MAX_SAFETY_RETRIES}) == "abort"


def test_format_output_normalizes_valid_plan():
    state = format_output({"plan_data": _valid_plan(), "metadata": {}})
    assert state["formatted_plan"] is not None
    assert len(state["formatted_plan"]["days"]) == 7


@pytest.mark.asyncio
async def test_generate_meal_plan_runs_graph_with_mock_provider():
    client = _mock_client()
    valid = _valid_plan()

    with patch(
        "app.ai.plan_generator_langgraph._call_provider",
        new=AsyncMock(return_value=(valid, {"model": "test", "provider": "mock"})),
    ):
        plan_data, metadata = await generate_meal_plan(client, food_items=[])

    assert len(plan_data["days"]) == 7
    assert metadata["framework"] == "langgraph"
