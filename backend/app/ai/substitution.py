"""AI food substitution for WhatsApp SWAP commands.

Phase 6 (MVP): Direct Gemini API call with structured JSON output.
"""

import json

from google import genai
from google.genai import types

from app.config import settings
from app.core.logger import get_logger
from app.models.client import Client

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a nutrition assistant for Indian meal plans.
Suggest 2-3 culturally appropriate food substitutions for Indian clients.
Respect allergies, dietary type (vegetarian/vegan/non-veg), and budget.
Return valid JSON only."""


def _build_prompt(client: Client, food_name: str, meal_context: str | None) -> str:
    allergies = ", ".join(client.allergies or []) or "none"
    dietary = client.dietary_type or "not specified"
    cuisine = client.cuisine_preference or "Indian"
    budget = client.monthly_food_budget_inr

    context_line = f"Meal context: {meal_context}\n" if meal_context else ""
    budget_line = f"Monthly food budget (INR): {budget}\n" if budget else ""

    return (
        f"Client cannot use: {food_name}\n"
        f"{context_line}"
        f"Dietary type: {dietary}\n"
        f"Allergies: {allergies}\n"
        f"Cuisine preference: {cuisine}\n"
        f"{budget_line}\n"
        "Return JSON with this schema:\n"
        "{\n"
        '  "alternatives": [\n'
        '    {"name": "food name", "reason": "why it works", "calories": 0, "protein_g": 0}\n'
        "  ],\n"
        '  "tip": "one short encouraging line"\n'
        "}"
    )


def _format_response(food_name: str, data: dict) -> str:
    alternatives = data.get("alternatives", [])
    if not alternatives:
        return (
            f"I couldn't find a good swap for {food_name} right now. "
            "Please check with your dietitian."
        )

    lines = [f"🔄 *Alternatives for {food_name}*\n"]
    for alt in alternatives[:3]:
        name = alt.get("name", "Option")
        reason = alt.get("reason", "")
        calories = alt.get("calories")
        protein = alt.get("protein_g")
        macro = ""
        if calories is not None and protein is not None:
            macro = f" (~{calories} kcal, {protein}g protein)"
        lines.append(f"• *{name}*{macro}")
        if reason:
            lines.append(f"  _{reason}_")

    tip = data.get("tip")
    if tip:
        lines.append(f"\n💡 {tip}")

    lines.append("\nWant your dietitian to update the plan? Just let them know.")
    return "\n".join(lines)


async def suggest_alternatives(
    client: Client,
    food_name: str,
    meal_context: str | None = None,
) -> str:
    """Generate substitution suggestions for a missing or unwanted food item."""
    if not settings.GEMINI_API_KEY and not settings.OPENAI_API_KEY:
        return (
            f"Swap suggestions aren't available right now. "
            f"Tell your dietitian you need an alternative to {food_name}."
        )

    prompt = _build_prompt(client, food_name, meal_context)

    try:
        if settings.GEMINI_API_KEY:
            data = await _generate_with_gemini(prompt)
        else:
            data = await _generate_with_openai(prompt)
        return _format_response(food_name, data)
    except Exception as e:
        logger.error(f"Substitution generation failed: {e}")
        return (
            f"I had trouble finding swaps for {food_name}. "
            "Please ask your dietitian for a quick alternative."
        )


async def _generate_with_gemini(prompt: str) -> dict:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = await client.aio.models.generate_content(
        model=settings.GEMINI_CHEAP_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.5,
            max_output_tokens=800,
        ),
    )
    return json.loads(response.text)


async def _generate_with_openai(prompt: str) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.OPENAI_CHEAP_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.5,
        max_tokens=800,
    )
    return json.loads(response.choices[0].message.content)
