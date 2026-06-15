"""AI meal plan generation service.

Phase 4 (MVP): Direct Gemini API calls → structured JSON → rule-based validation.
Uses google-genai as primary (free tier), OpenAI as paid fallback.

Evolution path:
  Phase 4:  Direct API calls (this file)
  Phase 9:  LangChain for composability + LangSmith tracing
  Phase 10: LangGraph for multi-step stateful workflows
"""

import json
import time
from typing import Any

from google import genai
from google.genai import types

from app.config import settings
from app.core.logger import get_logger
from app.models.client import Client
from app.models.food_item import FoodItem
from app.ai.prompts.plan_generation import SYSTEM_PROMPT, build_client_context

logger = get_logger(__name__)


async def _generate_with_gemini(
    user_prompt: str,
) -> tuple[dict, dict]:
    """Generate meal plan using Google Gemini (primary — free tier).

    Uses the google-genai SDK with async interface and structured JSON output.
    """
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

    # Gemini usage metadata
    usage = response.usage_metadata
    tokens_used = (usage.prompt_token_count or 0) + (usage.candidates_token_count or 0) if usage else 0

    metadata = {
        "model": settings.GEMINI_MODEL,
        "provider": "gemini",
        "tokens_used": tokens_used,
        "cost_usd": 0.0,  # Gemini Flash free tier
        "duration_ms": duration_ms,
    }

    return plan_data, metadata


async def _generate_with_openai(
    user_prompt: str,
) -> tuple[dict, dict]:
    """Generate meal plan using OpenAI (fallback — paid).

    Only called when Gemini fails or GEMINI_API_KEY is not configured.
    """
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
        return (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.6 / 1_000_000)
    return (prompt_tokens * 5.0 / 1_000_000) + (completion_tokens * 15.0 / 1_000_000)


async def generate_meal_plan(
    client_profile: Client,
    food_items: list[FoodItem],
    custom_instructions: str | None = None,
) -> tuple[dict, dict]:
    """Generate a 7-day meal plan using AI.

    Strategy: Try Gemini first (free tier), fall back to OpenAI if Gemini
    is unconfigured or fails. This is the Phase 4 MVP approach — direct
    API calls with structured JSON output and rule-based validation.

    Args:
        client_profile: The client's health profile.
        food_items: Available food items for the plan.
        custom_instructions: Optional dietitian-provided instructions.

    Returns:
        Tuple of (plan_data dict, metadata dict).
    """
    context = build_client_context(client_profile, food_items)

    user_prompt = f"Generate a 7-day meal plan for this client:\n\n{context}"
    if custom_instructions:
        user_prompt += f"\n\nAdditional instructions from dietitian: {custom_instructions}"

    # Strategy: Gemini first (free), OpenAI fallback (paid)
    if settings.GEMINI_API_KEY:
        try:
            logger.info("Generating meal plan with Gemini (primary)")
            return await _generate_with_gemini(user_prompt)
        except Exception as e:
            logger.warning(f"Gemini generation failed, falling back to OpenAI: {e}")

    if settings.OPENAI_API_KEY:
        logger.info("Generating meal plan with OpenAI (fallback)")
        return await _generate_with_openai(user_prompt)

    raise ValueError(
        "No AI provider configured. Set GEMINI_API_KEY (recommended, free tier) "
        "or OPENAI_API_KEY in your environment."
    )
