"""Tests for progress tracking endpoints."""

import pytest


async def _register_and_get_token(client, email="neha@nutriplan.in", name="Dr. Neha Sharma"):
    """Helper: register a dietitian and return the access token."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": name},
    )
    return resp.json()["access_token"]


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


CLIENT_DATA = {
    "full_name": "Priya Kapoor",
    "whatsapp_number": "+919876543210",
    "age": 28,
    "gender": "female",
    "height_cm": 162,
    "weight_kg": 72,
    "target_weight_kg": 60,
    "activity_level": "light",
    "medical_conditions": ["PCOS"],
    "allergies": ["peanuts"],
    "dietary_type": "veg",
    "cuisine_preference": "north_indian",
    "primary_goal": "weight_loss",
    "monthly_food_budget_inr": 8000,
}


@pytest.mark.asyncio
async def test_progress_crud(client):
    token = await _register_and_get_token(client)
    
    # Create client
    create_resp = await client.post(
        "/api/v1/clients", json=CLIENT_DATA, headers=_auth_header(token)
    )
    client_id = create_resp.json()["id"]

    # Log progress
    log_data = {
        "log_date": "2026-06-15",
        "weight_kg": 71.5,
        "waist_cm": 80.0,
        "notes": "Feeling good"
    }
    
    resp = await client.post(
        f"/api/v1/clients/{client_id}/progress",
        json=log_data,
        headers=_auth_header(token)
    )
    assert resp.status_code == 201
    created_log = resp.json()
    assert created_log["weight_kg"] == 71.5
    assert created_log["log_date"] == "2026-06-15"
    log_id = created_log["id"]
    
    # List progress
    resp = await client.get(
        f"/api/v1/clients/{client_id}/progress",
        headers=_auth_header(token)
    )
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) == 1
    
    # Update progress
    resp = await client.put(
        f"/api/v1/clients/{client_id}/progress/{log_id}",
        json={"weight_kg": 71.0},
        headers=_auth_header(token)
    )
    assert resp.status_code == 200
    updated_log = resp.json()
    assert updated_log["weight_kg"] == 71.0
    assert updated_log["notes"] == "Feeling good"
    
    # Delete progress
    resp = await client.delete(
        f"/api/v1/clients/{client_id}/progress/{log_id}",
        headers=_auth_header(token)
    )
    assert resp.status_code == 204
    
    # List progress -> empty
    resp = await client.get(
        f"/api/v1/clients/{client_id}/progress",
        headers=_auth_header(token)
    )
    assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_progress_multi_tenant(client):
    token_a = await _register_and_get_token(client, email="a@test.com")
    token_b = await _register_and_get_token(client, email="b@test.com")
    
    create_resp = await client.post(
        "/api/v1/clients", json=CLIENT_DATA, headers=_auth_header(token_a)
    )
    client_id = create_resp.json()["id"]

    log_data = {"log_date": "2026-06-15", "weight_kg": 71.5}
    await client.post(
        f"/api/v1/clients/{client_id}/progress",
        json=log_data,
        headers=_auth_header(token_a)
    )
    
    # Dietitian B tries to list progress
    resp = await client.get(
        f"/api/v1/clients/{client_id}/progress",
        headers=_auth_header(token_b)
    )
    assert resp.status_code == 404
