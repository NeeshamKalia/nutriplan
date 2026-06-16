"""AI meal plan generation — Phase 10 LangGraph workflow.

Multi-step StateGraph: parse profile → retrieve context → generate → validate safety
→ retry with constraints (max 2) → format output.

LangGraph vs LangChain (Phase 9) vs simple (Phase 4):
  LangGraph adds: explicit workflow nodes, conditional retry on safety failures,
                  separate context retrieval step, traceable graph execution in LangSmith.
  LangChain adds: composable chains, easier model swap, LangSmith tracing.
  Simple adds: fewest dependencies, direct token metadata, easiest to debug locally.
  LangGraph costs: graph boilerplate, harder to unit-test without mocking nodes.
"""

from __future__ import annotations

import json
from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import ValidationError

from app.ai.plan_generator import _call_provider, _configure_langsmith
from app.ai.plan_generator_simple import (
    MAX_SCHEMA_RETRIES,
    _RETRY_HINT,
    _validate_plan_data,
)
from app.ai.plan_validator import run_all_validations
from app.ai.prompts.plan_generation import build_client_context
from app.core.logger import get_logger
from app.models.client import Client
from app.models.food_item import FoodItem

logger = get_logger(__name__)

MAX_SAFETY_RETRIES = 2


class PlanGenerationState(TypedDict, total=False):
    client_profile: Client
    food_items: list[FoodItem]
    custom_instructions: str | None
    protocol_context: str
    previous_plans_context: str
    user_prompt: str
    plan_data: dict | None
    validations: list[dict]
    safety_retry_count: int
    schema_attempt: int
    metadata: dict
    formatted_plan: dict | None
    error: str | None


def parse_profile(state: PlanGenerationState) -> PlanGenerationState:
    """Node 1: Build base user prompt from client profile and food database."""
    client = state["client_profile"]
    food_items = state["food_items"]
    context = build_client_context(client, food_items)

    user_prompt = f"Generate a 7-day meal plan for this client:\n\n{context}"
    custom = state.get("custom_instructions")
    if custom:
        user_prompt += f"\n\nAdditional instructions from dietitian: {custom}"

    return {
        **state,
        "user_prompt": user_prompt,
        "safety_retry_count": state.get("safety_retry_count", 0),
        "schema_attempt": state.get("schema_attempt", 0),
    }


def retrieve_context(state: PlanGenerationState) -> PlanGenerationState:
    """Node 2: Append protocol and previous-plan context when available."""
    user_prompt = state["user_prompt"]
    protocol_context = state.get("protocol_context", "")
    previous_plans_context = state.get("previous_plans_context", "")

    if protocol_context:
        user_prompt += f"\n\nPROTOCOL GUIDELINES:\n{protocol_context}"
    if previous_plans_context:
        user_prompt += f"\n\nPREVIOUS PLANS (avoid repetition):\n{previous_plans_context}"

    return {**state, "user_prompt": user_prompt}


async def generate_plan(state: PlanGenerationState) -> PlanGenerationState:
    """Node 3: LLM call via LangChain provider chain."""
    _configure_langsmith()
    prompt = state["user_prompt"]
    schema_attempt = state.get("schema_attempt", 0)
    if schema_attempt > 0:
        prompt += _RETRY_HINT

    raw_data, metadata = await _call_provider(prompt)
    return {
        **state,
        "plan_data": raw_data,
        "metadata": {**metadata, "framework": "langgraph"},
    }


def validate_safety(state: PlanGenerationState) -> PlanGenerationState:
    """Node 4: Rule-based allergen, calorie, and dietary checks."""
    client = state["client_profile"]
    plan_data = state.get("plan_data") or {}
    validations = run_all_validations(plan_data, client)
    return {**state, "validations": validations}


def prepare_safety_retry(state: PlanGenerationState) -> PlanGenerationState:
    """Inject failed validation messages before regenerating."""
    failures = [v for v in state.get("validations", []) if not v["passed"]]
    constraints = "\n".join(f"- {v['message']}" for v in failures)
    user_prompt = state["user_prompt"] + (
        "\n\nPREVIOUS ATTEMPT FAILED SAFETY CHECKS. Fix these issues:\n"
        f"{constraints}"
    )
    return {
        **state,
        "user_prompt": user_prompt,
        "safety_retry_count": state.get("safety_retry_count", 0) + 1,
        "plan_data": None,
        "validations": [],
    }


def format_output(state: PlanGenerationState) -> PlanGenerationState:
    """Node 5: Final schema validation and normalization."""
    plan_data = state.get("plan_data")
    if not plan_data:
        return {**state, "error": "No plan data produced by workflow"}

    try:
        formatted = _validate_plan_data(plan_data)
    except ValidationError as exc:
        schema_attempt = state.get("schema_attempt", 0)
        if schema_attempt < MAX_SCHEMA_RETRIES:
            logger.warning(
                "LangGraph schema validation failed (attempt %s), will retry generate",
                schema_attempt + 1,
            )
            return {
                **state,
                "schema_attempt": schema_attempt + 1,
                "plan_data": None,
                "error": str(exc),
            }
        return {**state, "error": f"Invalid plan schema after retries: {exc}"}

    metadata = state.get("metadata", {})
    metadata["safety_retries"] = state.get("safety_retry_count", 0)
    metadata["schema_attempts"] = state.get("schema_attempt", 0) + 1
    return {**state, "formatted_plan": formatted, "metadata": metadata, "error": None}


def route_after_safety(
    state: PlanGenerationState,
) -> Literal["prepare_retry", "format_output"]:
    """Retry generation when critical/high safety checks fail (max 2 retries)."""
    validations = state.get("validations", [])
    blocking = [
        v
        for v in validations
        if not v["passed"] and v["severity"] in ("critical", "high")
    ]
    if blocking and state.get("safety_retry_count", 0) < MAX_SAFETY_RETRIES:
        return "prepare_retry"
    return "format_output"


def route_after_format(
    state: PlanGenerationState,
) -> Literal["generate_plan", "end"]:
    """Retry LLM when schema validation fails inside format_output."""
    if state.get("formatted_plan"):
        return "end"
    if state.get("schema_attempt", 0) <= MAX_SCHEMA_RETRIES and state.get("error"):
        return "generate_plan"
    return "end"


def build_plan_generation_graph():
    """Compile the LangGraph workflow."""
    graph = StateGraph(PlanGenerationState)

    graph.add_node("parse_profile", parse_profile)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_plan", generate_plan)
    graph.add_node("validate_safety", validate_safety)
    graph.add_node("prepare_safety_retry", prepare_safety_retry)
    graph.add_node("format_output", format_output)

    graph.set_entry_point("parse_profile")
    graph.add_edge("parse_profile", "retrieve_context")
    graph.add_edge("retrieve_context", "generate_plan")
    graph.add_edge("generate_plan", "validate_safety")
    graph.add_conditional_edges(
        "validate_safety",
        route_after_safety,
        {
            "prepare_retry": "prepare_safety_retry",
            "format_output": "format_output",
        },
    )
    graph.add_edge("prepare_safety_retry", "generate_plan")
    graph.add_conditional_edges(
        "format_output",
        route_after_format,
        {
            "generate_plan": "generate_plan",
            "end": END,
        },
    )

    return graph.compile()


_plan_graph = None


def get_plan_generation_graph():
    global _plan_graph
    if _plan_graph is None:
        _plan_graph = build_plan_generation_graph()
    return _plan_graph


async def generate_meal_plan(
    client_profile: Client,
    food_items: list[FoodItem],
    custom_instructions: str | None = None,
    protocol_context: str = "",
    previous_plans_context: str = "",
) -> tuple[dict, dict]:
    """Generate a 7-day meal plan using the LangGraph multi-step workflow."""
    initial_state: PlanGenerationState = {
        "client_profile": client_profile,
        "food_items": food_items,
        "custom_instructions": custom_instructions,
        "protocol_context": protocol_context,
        "previous_plans_context": previous_plans_context,
        "safety_retry_count": 0,
        "schema_attempt": 0,
    }

    graph = get_plan_generation_graph()
    final_state = await graph.ainvoke(initial_state)

    formatted = final_state.get("formatted_plan")
    metadata = final_state.get("metadata") or {}
    error = final_state.get("error")

    if not formatted:
        raise ValueError(error or "LangGraph plan generation failed")

    logger.info(
        "LangGraph plan generated (safety_retries=%s, schema_attempts=%s)",
        metadata.get("safety_retries", 0),
        metadata.get("schema_attempts", 1),
    )
    return formatted, metadata
