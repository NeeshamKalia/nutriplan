"""AI meal plan generation — Phase 4 simple implementation (kept for comparison).

Direct Gemini/OpenAI API calls → structured JSON → rule-based validation.
Use plan_generator.py (LangChain) in production; this module is the baseline.
"""

import json
import time
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.config import settings
from app.core.logger import get_logger
from app.models.client import Client
from app.models.food_item import FoodItem
from app.ai.plan_schema import GeneratedPlanSchema
from app.ai.prompts.plan_generation import SYSTEM_PROMPT, build_client_context

logger = get_logger(__name__)

MAX_SCHEMA_RETRIES = 1
_RETRY_HINT = (
    "\n\nIMPORTANT: Your previous response was invalid or incomplete. "
    "Return valid JSON with exactly 7 days. Each day must have day_number (1-7), "
    "day_label, and items array. Each item needs meal_type, food_name, "
    "portion_description, calories, protein_g, carbs_g, fat_g."
)


async def _generate_with_gemini(user_prompt: str) -> tuple[dict, dict]:
    """Generate meal plan using Google Gemini (primary — free tier)."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    start = time.time()
    response = await client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.7,
            max_output_tokens=4000,
        ),
    )
    duration_ms = int((time.time() - start) * 1000)

    plan_data = json.loads(response.text)

    usage = response.usage_metadata
    tokens_used = (
        (usage.prompt_token_count or 0) + (usage.candidates_token_count or 0)
        if usage
        else 0
    )

    metadata = {
        "model": settings.GEMINI_MODEL,
        "provider": "gemini",
        "tokens_used": tokens_used,
        "cost_usd": 0.0,
        "duration_ms": duration_ms,
    }

    return plan_data, metadata


async def _generate_with_openai(user_prompt: str) -> tuple[dict, dict]:
    """Generate meal plan using OpenAI (fallback — paid)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    start = time.time()
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=4000,
    )
    duration_ms = int((time.time() - start) * 1000)

    plan_data = json.loads(response.choices[0].message.content)

    usage = response.usage
    cost_usd = _estimate_openai_cost(usage)

    metadata = {
        "model": settings.OPENAI_MODEL,
        "provider": "openai",
        "tokens_used": usage.total_tokens,
        "cost_usd": cost_usd,
        "duration_ms": duration_ms,
    }

    return plan_data, metadata


def _estimate_openai_cost(usage: Any) -> float:
    """Rough cost estimation for OpenAI API calls."""
    prompt_tokens = usage.prompt_tokens
    completion_tokens = usage.completion_tokens
    if "mini" in settings.OPENAI_MODEL:
        return (prompt_tokens * 0.15 / 1_000_000) + (
            completion_tokens * 0.6 / 1_000_000
        )
    return (prompt_tokens * 5.0 / 1_000_000) + (
        completion_tokens * 15.0 / 1_000_000
    )


def _validate_plan_data(plan_data: dict) -> dict:
    """Validate AI output against strict schema; return normalized dict."""
    validated = GeneratedPlanSchema.model_validate(plan_data)
    return validated.model_dump()


async def _call_provider(user_prompt: str) -> tuple[dict, dict]:
    """Call Gemini first, fall back to OpenAI."""
    if settings.GEMINI_API_KEY:
        try:
            logger.info("Generating meal plan with Gemini (primary, simple)")
            return await _generate_with_gemini(user_prompt)
        except Exception as e:
            logger.warning(f"Gemini generation failed, falling back to OpenAI: {e}")

    if settings.OPENAI_API_KEY:
        logger.info("Generating meal plan with OpenAI (fallback, simple)")
        return await _generate_with_openai(user_prompt)

    raise ValueError(
        "No AI provider configured. Set GEMINI_API_KEY (recommended, free tier) "
        "or OPENAI_API_KEY in your environment."
    )


async def generate_meal_plan(
    client_profile: Client,
    food_items: list[FoodItem],
    custom_instructions: str | None = None,
) -> tuple[dict, dict]:
    """Generate a 7-day meal plan using direct API calls (Phase 4 baseline)."""
    context = build_client_context(client_profile, food_items)

    user_prompt = f"Generate a 7-day meal plan for this client:\n\n{context}"
    if custom_instructions:
        user_prompt += (
            f"\n\nAdditional instructions from dietitian: {custom_instructions}"
        )

    last_error: Exception | None = None

    for attempt in range(MAX_SCHEMA_RETRIES + 1):
        prompt = user_prompt if attempt == 0 else user_prompt + _RETRY_HINT
        try:
            raw_data, metadata = await _call_provider(prompt)
            validated = _validate_plan_data(raw_data)
            if attempt > 0:
                logger.info("AI plan validated successfully after retry")
            return validated, metadata
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            last_error = e
            logger.warning(
                f"AI plan schema validation failed (attempt {attempt + 1}): {e}"
            )
            if attempt >= MAX_SCHEMA_RETRIES:
                break

    raise ValueError(
        f"AI returned invalid plan structure after {MAX_SCHEMA_RETRIES + 1} attempts: "
        f"{last_error}"
    ) from last_error
