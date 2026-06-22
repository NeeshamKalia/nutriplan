"""Tests for protocol template CRUD and plan integration."""

from unittest.mock import AsyncMock, patch

import pytest


async def _register_and_get_token(client, email="neha@nutriplan.in", name="Dr. Neha Sharma"):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": name},
    )
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _create_client(client, token):
    resp = await client.post(
        "/api/v1/clients",
        json={
            "full_name": "Test Client",
            "whatsapp_number": "+919999999999",
            "primary_goal": "weight_loss",
            "dietary_type": "veg",
            "daily_calorie_target": 1600,
        },
        headers=_auth(token),
    )
    return resp.json()["id"]


PLAN_DATA = {
    "title": "Week 1 - PCOS Friendly",
    "week_start_date": "2026-06-15",
    "days": [
        {
            "day_number": 1,
            "day_label": "Monday",
            "items": [
                {
                    "meal_type": "breakfast",
                    "food_name": "Oats Chilla",
                    "portion_description": "2 medium",
                    "portion_grams": 100,
                    "calories": 250,
                    "protein_g": 10,
                    "carbs_g": 35,
                    "fat_g": 5,
                }
            ],
        }
    ],
}


@pytest.mark.asyncio
async def test_create_protocol(client):
    token = await _register_and_get_token(client)
    resp = await client.post(
        "/api/v1/protocols",
        headers=_auth(token),
        json={
            "name": "PCOS Weight Loss",
            "description": "Moderate carb plan for PCOS",
            "target_conditions": ["PCOS"],
            "target_goals": ["weight_loss"],
            "calorie_range_min": 1400,
            "calorie_range_max": 1700,
            "general_guidelines": "Focus on low-GI foods",
            "preferred_foods": ["methi", "flaxseeds"],
            "avoided_foods": ["maida", "refined sugar"],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "PCOS Weight Loss"
    assert data["target_conditions"] == ["PCOS"]
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_and_get_protocol(client):
    token = await _register_and_get_token(client)
    created = await client.post(
        "/api/v1/protocols",
        headers=_auth(token),
        json={"name": "Diabetes Friendly", "general_guidelines": "Low sugar"},
    )
    protocol_id = created.json()["id"]

    listed = await client.get("/api/v1/protocols", headers=_auth(token))
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    detail = await client.get(f"/api/v1/protocols/{protocol_id}", headers=_auth(token))
    assert detail.status_code == 200
    assert detail.json()["name"] == "Diabetes Friendly"


@pytest.mark.asyncio
async def test_update_and_delete_protocol(client):
    token = await _register_and_get_token(client)
    created = await client.post(
        "/api/v1/protocols",
        headers=_auth(token),
        json={"name": "Original Name"},
    )
    protocol_id = created.json()["id"]

    updated = await client.put(
        f"/api/v1/protocols/{protocol_id}",
        headers=_auth(token),
        json={"name": "Updated Name", "general_guidelines": "New rules"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Name"

    deleted = await client.delete(
        f"/api/v1/protocols/{protocol_id}", headers=_auth(token)
    )
    assert deleted.status_code == 204

    missing = await client.get(
        f"/api/v1/protocols/{protocol_id}", headers=_auth(token)
    )
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_protocol_multi_tenant_isolation(client):
    token_a = await _register_and_get_token(client, "a@test.com", "Dr. A")
    token_b = await _register_and_get_token(client, "b@test.com", "Dr. B")

    created = await client.post(
        "/api/v1/protocols",
        headers=_auth(token_a),
        json={"name": "Private Protocol"},
    )
    protocol_id = created.json()["id"]

    resp = await client.get(
        f"/api/v1/protocols/{protocol_id}", headers=_auth(token_b)
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_save_plan_as_protocol(client):
    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)
    plan_resp = await client.post(
        f"/api/v1/clients/{client_id}/plans",
        json=PLAN_DATA,
        headers=_auth(token),
    )
    plan_id = plan_resp.json()["id"]

    saved = await client.post(
        f"/api/v1/plans/{plan_id}/save-as-protocol",
        headers=_auth(token),
        json={
            "name": "Saved PCOS Template",
            "general_guidelines": "Use this as a starting point",
        },
    )
    assert saved.status_code == 201
    data = saved.json()
    assert data["name"] == "Saved PCOS Template"
    assert data["sample_plan"] is not None
    assert len(data["sample_plan"]["days"]) == 1


@pytest.mark.asyncio
async def test_generate_plan_with_protocol_id(client):
    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)

    protocol_resp = await client.post(
        "/api/v1/protocols",
        headers=_auth(token),
        json={
            "name": "Veg Weight Loss",
            "general_guidelines": "High protein vegetarian meals",
        },
    )
    protocol_id = protocol_resp.json()["id"]

    valid_plan = {
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

    with patch(
        "app.ai.plan_generator_langgraph._call_provider",
        new=AsyncMock(return_value=(valid_plan, {"model": "test", "provider": "mock"})),
    ):
        resp = await client.post(
            f"/api/v1/clients/{client_id}/plans/generate",
            headers=_auth(token),
            json={
                "week_start_date": "2026-06-16",
                "protocol_id": protocol_id,
            },
        )

    assert resp.status_code == 201
    assert resp.json()["status"] == "draft"
