"""AI meal plan generation service — Phase 9 LangChain implementation.

Uses LangChain ChatGoogleGenerativeAI + PromptTemplate with optional LangSmith tracing.
The Phase 4 direct-API baseline lives in plan_generator_simple.py for A/B comparison.

LangChain vs simple (Phase 4):
  Improved: composable prompt | model | parser chains; LangSmith trace per run;
            easier to swap models and add retrieval steps in Phase 9 RAG / Phase 10 graph.
  Complicated: extra dependencies and abstraction layers; token metadata parsing
               is less direct than google-genai usage_metadata.
"""

import json
import os
import time

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from app.config import settings
from app.core.logger import get_logger
from app.models.client import Client
from app.models.food_item import FoodItem
from app.ai.plan_generator_simple import (
    MAX_SCHEMA_RETRIES,
    _RETRY_HINT,
    _validate_plan_data,
)
from app.ai.prompts.plan_generation import SYSTEM_PROMPT, build_client_context

logger = get_logger(__name__)

_langsmith_configured = False


def _configure_langsmith() -> None:
    """Ensure LangSmith tracing env vars are set.

    SD-007: Env vars are now configured at startup in main.py lifespan.
    This function exists for backward compatibility and is a safe no-op
    if env vars are already set.
    """
    global _langsmith_configured
    if _langsmith_configured:
        return
    if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
        # Env vars should already be set by main.py, but set defensively
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGCHAIN_API_KEY)
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGCHAIN_PROJECT)
    _langsmith_configured = True


def _build_prompt_template() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{user_prompt}"),
        ]
    )


def _build_gemini_chain():
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.7,
        max_output_tokens=4000,
    )
    return _build_prompt_template() | llm.bind(response_mime_type="application/json") | JsonOutputParser()


def _build_openai_chain():
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
        max_tokens=4000,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    return _build_prompt_template() | llm | JsonOutputParser()


async def _invoke_chain(chain, user_prompt: str, provider: str, model: str) -> tuple[dict, dict]:
    start = time.time()
    result = await chain.ainvoke({"user_prompt": user_prompt})
    duration_ms = int((time.time() - start) * 1000)

    if isinstance(result, dict):
        metadata = {
            "model": model,
            "provider": provider,
            "tokens_used": 0,
            "cost_usd": 0.0,
            "duration_ms": duration_ms,
            "framework": "langchain",
        }
        return result, metadata

    raise TypeError(f"Unexpected chain output type: {type(result)}")


async def _generate_with_gemini(user_prompt: str) -> tuple[dict, dict]:
    chain = _build_gemini_chain()
    plan_data, metadata = await _invoke_chain(
        chain, user_prompt, provider="gemini", model=settings.GEMINI_MODEL
    )
    return plan_data, metadata


async def _generate_with_openai(user_prompt: str) -> tuple[dict, dict]:
    chain = _build_openai_chain()
    plan_data, metadata = await _invoke_chain(
        chain, user_prompt, provider="openai", model=settings.OPENAI_MODEL
    )
    if metadata["tokens_used"] == 0:
        metadata["cost_usd"] = 0.0
    return plan_data, metadata


async def _call_provider(user_prompt: str) -> tuple[dict, dict]:
    """Call Gemini via LangChain first, fall back to OpenAI."""
    _configure_langsmith()

    if settings.GEMINI_API_KEY:
        try:
            logger.info("Generating meal plan with LangChain + Gemini (primary)")
            return await _generate_with_gemini(user_prompt)
        except Exception as e:
            logger.warning(f"LangChain Gemini generation failed, falling back to OpenAI: {e}")

    if settings.OPENAI_API_KEY:
        logger.info("Generating meal plan with LangChain + OpenAI (fallback)")
        return await _generate_with_openai(user_prompt)

    raise ValueError(
        "No AI provider configured. Set GEMINI_API_KEY (recommended, free tier) "
        "or OPENAI_API_KEY in your environment."
    )


async def generate_meal_plan(
    client_profile: Client,
    food_items: list[FoodItem],
    custom_instructions: str | None = None,
    protocol_context: str = "",
    previous_plans_context: str = "",
) -> tuple[dict, dict]:
    """Route to the configured plan generator backend."""
    from app.config import settings

    if settings.PLAN_GENERATOR_BACKEND == "simple":
        from app.ai.plan_generator_simple import generate_meal_plan as _generate

        return await _generate(client_profile, food_items, custom_instructions)

    if settings.PLAN_GENERATOR_BACKEND == "langgraph":
        from app.ai.plan_generator_langgraph import generate_meal_plan as _generate

        return await _generate(
            client_profile,
            food_items,
            custom_instructions,
            protocol_context=protocol_context,
            previous_plans_context=previous_plans_context,
        )

    return await _generate_meal_plan_langchain(
        client_profile,
        food_items,
        custom_instructions,
    )


async def _generate_meal_plan_langchain(
    client_profile: Client,
    food_items: list[FoodItem],
    custom_instructions: str | None = None,
) -> tuple[dict, dict]:
    """Generate a 7-day meal plan using LangChain with schema validation and retry."""
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
