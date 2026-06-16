"""LLM-as-judge evaluation for generated meal plans (Phase 10).

Scores relevance, practicality, and cultural fit for Indian nutrition context.
Runs after rule-based validation; uses the cheap Gemini model when available.
"""

import json
import time

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

from app.config import settings
from app.core.logger import get_logger
from app.models.client import Client

logger = get_logger(__name__)

PASS_THRESHOLD = 6


class JudgeScores(BaseModel):
    relevance_score: int = Field(ge=1, le=10)
    practicality_score: int = Field(ge=1, le=10)
    cultural_fit_score: int = Field(ge=1, le=10)
    overall_score: int = Field(ge=1, le=10)
    summary: str = Field(min_length=1)


JUDGE_PROMPT = """You are an expert Indian clinical nutritionist reviewing an AI-generated meal plan.

Score the plan from 1-10 on:
1. relevance — matches client goals, conditions, allergies, calorie target
2. practicality — realistic home cooking, common ingredients, budget-aware
3. cultural_fit — authentic Indian foods, appropriate portions, regional relevance

Return JSON only:
{
  "relevance_score": 8,
  "practicality_score": 7,
  "cultural_fit_score": 9,
  "overall_score": 8,
  "summary": "One sentence explaining the main strength or concern."
}
"""


def _build_plan_summary(plan_data: dict) -> str:
    lines = []
    for day in plan_data.get("days", [])[:3]:
        foods = [item.get("food_name", "?") for item in day.get("items", [])[:5]]
        lines.append(f"Day {day.get('day_number')}: {', '.join(foods)}")
    if len(plan_data.get("days", [])) > 3:
        lines.append(f"... plus {len(plan_data['days']) - 3} more days")
    return "\n".join(lines)


def _build_client_summary(client: Client) -> str:
    allergies = ", ".join(client.allergies or []) or "none"
    conditions = ", ".join(client.medical_conditions or []) or "none"
    return (
        f"Goal: {client.primary_goal or 'general wellness'}\n"
        f"Diet: {client.dietary_type or 'any'}\n"
        f"Calorie target: {client.daily_calorie_target or 'unspecified'}\n"
        f"Cuisine: {client.cuisine_preference or 'Indian'}\n"
        f"Allergies: {allergies}\n"
        f"Conditions: {conditions}"
    )


def _scores_to_validations(scores: JudgeScores) -> list[dict]:
    passed = scores.overall_score >= PASS_THRESHOLD
    severity = "info" if passed else "medium"
    details = scores.model_dump()

    return [
        {
            "type": "llm_judge_relevance",
            "passed": scores.relevance_score >= PASS_THRESHOLD,
            "severity": "info" if scores.relevance_score >= PASS_THRESHOLD else "medium",
            "message": f"Relevance: {scores.relevance_score}/10",
            "details": details,
        },
        {
            "type": "llm_judge_practicality",
            "passed": scores.practicality_score >= PASS_THRESHOLD,
            "severity": "info" if scores.practicality_score >= PASS_THRESHOLD else "medium",
            "message": f"Practicality: {scores.practicality_score}/10",
            "details": details,
        },
        {
            "type": "llm_judge_cultural_fit",
            "passed": scores.cultural_fit_score >= PASS_THRESHOLD,
            "severity": "info" if scores.cultural_fit_score >= PASS_THRESHOLD else "medium",
            "message": f"Cultural fit: {scores.cultural_fit_score}/10",
            "details": details,
        },
        {
            "type": "llm_judge_overall",
            "passed": passed,
            "severity": severity,
            "message": f"Overall: {scores.overall_score}/10 — {scores.summary}",
            "details": details,
        },
    ]


async def judge_meal_plan(plan_data: dict, client: Client) -> list[dict]:
    """Score a generated plan with a second LLM pass."""
    if not settings.GEMINI_API_KEY:
        return [
            {
                "type": "llm_judge_overall",
                "passed": True,
                "severity": "info",
                "message": "LLM judge skipped (no GEMINI_API_KEY configured).",
                "details": None,
            }
        ]

    user_prompt = (
        f"CLIENT:\n{_build_client_summary(client)}\n\n"
        f"PLAN SAMPLE:\n{_build_plan_summary(plan_data)}\n\n"
        "Score this plan."
    )

    try:
        client_ai = genai.Client(api_key=settings.GEMINI_API_KEY)
        start = time.time()
        response = await client_ai.aio.models.generate_content(
            model=settings.GEMINI_CHEAP_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=JUDGE_PROMPT,
                response_mime_type="application/json",
                temperature=0.2,
                max_output_tokens=500,
            ),
        )
        duration_ms = int((time.time() - start) * 1000)
        raw = json.loads(response.text)
        scores = JudgeScores.model_validate(raw)
        logger.info("LLM judge completed in %sms (overall=%s)", duration_ms, scores.overall_score)
        return _scores_to_validations(scores)
    except (json.JSONDecodeError, ValidationError, Exception) as exc:
        logger.warning("LLM judge failed: %s", exc)
        return [
            {
                "type": "llm_judge_overall",
                "passed": True,
                "severity": "info",
                "message": f"LLM judge unavailable: {exc}",
                "details": None,
            }
        ]
