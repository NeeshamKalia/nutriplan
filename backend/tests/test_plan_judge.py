"""Tests for LLM-as-judge plan evaluation."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.plan_judge import _scores_to_validations, judge_meal_plan


def _mock_client():
    return SimpleNamespace(
        primary_goal="weight_loss",
        dietary_type="veg",
        daily_calorie_target=1600,
        cuisine_preference="north_indian",
        allergies=["peanuts"],
        medical_conditions=["PCOS"],
    )


def test_scores_to_validations_pass():
    from app.ai.plan_judge import JudgeScores

    scores = JudgeScores(
        relevance_score=8,
        practicality_score=7,
        cultural_fit_score=9,
        overall_score=8,
        summary="Well-balanced Indian veg plan.",
    )
    results = _scores_to_validations(scores)
    assert len(results) == 4
    assert all(r["passed"] for r in results)
    assert results[-1]["type"] == "llm_judge_overall"


def test_scores_to_validations_fail_below_threshold():
    from app.ai.plan_judge import JudgeScores

    scores = JudgeScores(
        relevance_score=5,
        practicality_score=4,
        cultural_fit_score=5,
        overall_score=4,
        summary="Plan needs improvement.",
    )
    results = _scores_to_validations(scores)
    overall = next(r for r in results if r["type"] == "llm_judge_overall")
    assert overall["passed"] is False


@pytest.mark.asyncio
async def test_judge_meal_plan_without_api_key(monkeypatch):
    monkeypatch.setattr("app.ai.plan_judge.settings.GEMINI_API_KEY", "")
    results = await judge_meal_plan({"days": []}, _mock_client())
    assert len(results) == 1
    assert results[0]["type"] == "llm_judge_overall"
    assert results[0]["passed"] is True


@pytest.mark.asyncio
async def test_judge_meal_plan_parses_gemini_response(monkeypatch):
    monkeypatch.setattr("app.ai.plan_judge.settings.GEMINI_API_KEY", "test-key")

    mock_response = SimpleNamespace(
        text='{"relevance_score":8,"practicality_score":7,"cultural_fit_score":9,"overall_score":8,"summary":"Good plan."}'
    )

    with patch("app.ai.plan_judge.genai.Client") as mock_client_cls:
        mock_client_cls.return_value.aio.models.generate_content = AsyncMock(
            return_value=mock_response
        )
        results = await judge_meal_plan({"days": [{"day_number": 1, "items": []}]}, _mock_client())

    assert any(r["type"] == "llm_judge_overall" and r["passed"] for r in results)
