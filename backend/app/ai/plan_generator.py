"""AI meal plan generation service."""

import json
import time
from typing import Any
from openai import AsyncOpenAI

from app.config import settings
from app.models.client import Client
from app.models.food_item import FoodItem
from app.ai.prompts.plan_generation import SYSTEM_PROMPT, build_client_context

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

def calculate_cost(usage: Any) -> float:
    # A simple estimation
    prompt_tokens = usage.prompt_tokens
    completion_tokens = usage.completion_tokens
    # Assuming GPT-4o-mini pricing roughly, $0.15/1M input, $0.6/1M output
    if "mini" in settings.OPENAI_MODEL:
        return (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.6 / 1_000_000)
    # GPT-4o pricing roughly
    return (prompt_tokens * 5.0 / 1_000_000) + (completion_tokens * 15.0 / 1_000_000)

async def generate_meal_plan(
    client_profile: Client,
    food_items: list[FoodItem],
    custom_instructions: str | None = None
) -> tuple[dict, dict]:
    """
    Generate a 7-day meal plan using simple prompt -> OpenAI -> structured JSON.
    Returns: (plan_data: dict, metadata: dict)
    """
    context = build_client_context(client_profile, food_items)
    
    user_prompt = f"Generate a 7-day meal plan for this client:\n\n{context}"
    if custom_instructions:
        user_prompt += f"\n\nAdditional instructions from dietitian: {custom_instructions}"
    
    start = time.time()
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        max_tokens=4000
    )
    duration_ms = int((time.time() - start) * 1000)
    
    plan_data = json.loads(response.choices[0].message.content)
    
    metadata = {
        "model": settings.OPENAI_MODEL,
        "tokens_used": response.usage.total_tokens,
        "cost_usd": calculate_cost(response.usage),
        "duration_ms": duration_ms
    }
    
    return plan_data, metadata
