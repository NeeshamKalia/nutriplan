"""Tests for AI plan JSON schema validation."""

import pytest
from pydantic import ValidationError

from app.ai.plan_schema import GeneratedPlanSchema


def _valid_day(day_number: int) -> dict:
    return {
        "day_number": day_number,
        "day_label": f"Day {day_number}",
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


def test_valid_plan_schema_accepts_seven_days():
    data = {"days": [_valid_day(i) for i in range(1, 8)]}
    plan = GeneratedPlanSchema.model_validate(data)
    assert len(plan.days) == 7


def test_plan_schema_rejects_fewer_than_seven_days():
    data = {"days": [_valid_day(i) for i in range(1, 4)]}
    with pytest.raises(ValidationError):
        GeneratedPlanSchema.model_validate(data)


def test_plan_schema_rejects_missing_required_fields():
    data = {
        "days": [
            {
                "day_number": 1,
                "day_label": "Day 1",
                "items": [{"meal_type": "breakfast", "food_name": "Roti"}],
            }
        ]
    }
    with pytest.raises(ValidationError):
        GeneratedPlanSchema.model_validate(data)
