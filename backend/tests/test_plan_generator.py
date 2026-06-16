"""Tests for plan generator schema validation and retry."""

import pytest
from pydantic import ValidationError

from app.ai.plan_generator_simple import _validate_plan_data, MAX_SCHEMA_RETRIES


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


def test_validate_plan_data_accepts_valid_output():
    result = _validate_plan_data(_valid_plan())
    assert len(result["days"]) == 7


def test_validate_plan_data_rejects_invalid_output():
    with pytest.raises(ValidationError):
        _validate_plan_data({"days": []})


def test_max_schema_retries_is_one():
    assert MAX_SCHEMA_RETRIES == 1
