"""Tests for client management endpoints.

Tests cover: create, list, get, update, delete (archive), multi-tenant isolation.
"""

import pytest


async def _register_and_get_token(client, email="neha@nutriplan.in", name="Dr. Neha Sharma"):
    """Helper: register a dietitian and return the access token."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": name},
    )
    assert resp.status_code == 201
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
async def test_create_client(client):
    """Create a client with health profile -> 201."""
    token = await _register_and_get_token(client)
    response = await client.post(
        "/api/v1/clients",
        json=CLIENT_DATA,
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Priya Kapoor"
    assert data["whatsapp_number"] == "+919876543210"
    assert data["dietary_type"] == "veg"
    assert data["status"] == "active"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_duplicate_whatsapp(client):
    """Creating two clients with same WhatsApp for same dietitian -> 409."""
    token = await _register_and_get_token(client)
    await client.post("/api/v1/clients", json=CLIENT_DATA, headers=_auth_header(token))
    response = await client.post(
        "/api/v1/clients",
        json={**CLIENT_DATA, "full_name": "Another Client"},
        headers=_auth_header(token),
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_clients(client):
    """List clients -> returns only this dietitian's clients."""
    token = await _register_and_get_token(client)
    # Create 2 clients
    await client.post(
        "/api/v1/clients",
        json={**CLIENT_DATA, "full_name": "Client One"},
        headers=_auth_header(token),
    )
    await client.post(
        "/api/v1/clients",
        json={**CLIENT_DATA, "full_name": "Client Two", "whatsapp_number": "+919876543211"},
        headers=_auth_header(token),
    )
    response = await client.get("/api/v1/clients", headers=_auth_header(token))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["clients"]) == 2


@pytest.mark.asyncio
async def test_list_clients_search(client):
    """Search clients by name."""
    token = await _register_and_get_token(client)
    await client.post(
        "/api/v1/clients",
        json={**CLIENT_DATA, "full_name": "Priya Kapoor"},
        headers=_auth_header(token),
    )
    await client.post(
        "/api/v1/clients",
        json={**CLIENT_DATA, "full_name": "Rahul Sharma", "whatsapp_number": "+919876543211"},
        headers=_auth_header(token),
    )
    # Search for "priya"
    response = await client.get(
        "/api/v1/clients?search=priya", headers=_auth_header(token)
    )
    data = response.json()
    assert data["total"] == 1
    assert data["clients"][0]["full_name"] == "Priya Kapoor"


@pytest.mark.asyncio
async def test_get_client(client):
    """Get single client -> returns full profile."""
    token = await _register_and_get_token(client)
    create_resp = await client.post(
        "/api/v1/clients", json=CLIENT_DATA, headers=_auth_header(token)
    )
    client_id = create_resp.json()["id"]
    response = await client.get(
        f"/api/v1/clients/{client_id}", headers=_auth_header(token)
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Priya Kapoor"


@pytest.mark.asyncio
async def test_update_client(client):
    """Partial update -> only specified fields change."""
    token = await _register_and_get_token(client)
    create_resp = await client.post(
        "/api/v1/clients", json=CLIENT_DATA, headers=_auth_header(token)
    )
    client_id = create_resp.json()["id"]
    response = await client.put(
        f"/api/v1/clients/{client_id}",
        json={"weight_kg": 68, "primary_goal": "maintenance"},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["weight_kg"] == 68.0
    assert data["primary_goal"] == "maintenance"
    assert data["full_name"] == "Priya Kapoor"  # Unchanged


@pytest.mark.asyncio
async def test_archive_client(client):
    """Delete (archive) -> status='archived', archived_at set."""
    token = await _register_and_get_token(client)
    create_resp = await client.post(
        "/api/v1/clients", json=CLIENT_DATA, headers=_auth_header(token)
    )
    client_id = create_resp.json()["id"]
    response = await client.delete(
        f"/api/v1/clients/{client_id}", headers=_auth_header(token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "archived"
    assert data["archived_at"] is not None


@pytest.mark.asyncio
async def test_multi_tenant_isolation(client):
    """Dietitian A's client is invisible to Dietitian B -> 404."""
    # Register two dietitians
    token_a = await _register_and_get_token(client, email="a@test.com", name="Dietitian A")
    token_b = await _register_and_get_token(client, email="b@test.com", name="Dietitian B")

    # Dietitian A creates a client
    create_resp = await client.post(
        "/api/v1/clients", json=CLIENT_DATA, headers=_auth_header(token_a)
    )
    client_id = create_resp.json()["id"]

    # Dietitian B tries to access A's client -> 404
    response = await client.get(
        f"/api/v1/clients/{client_id}", headers=_auth_header(token_b)
    )
    assert response.status_code == 404

    # Dietitian B lists their clients -> 0
    response = await client.get("/api/v1/clients", headers=_auth_header(token_b))
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_create_client_no_auth(client):
    """Create client without auth -> 403."""
    response = await client.post("/api/v1/clients", json=CLIENT_DATA)
    assert response.status_code == 403
