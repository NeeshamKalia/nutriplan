"""Tests for adherence stats and dashboard overview."""

import pytest


async def _register_and_get_token(client, email="neha@nutriplan.in"):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Dr. Neha"},
    )
    return resp.json()["access_token"]


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


async def _create_client(client, token, name="Priya Kapoor", phone="+919876543210"):
    resp = await client.post(
        "/api/v1/clients",
        json={
            "full_name": name,
            "whatsapp_number": phone,
            "primary_goal": "weight_loss",
        },
        headers=_auth_header(token),
    )
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_client_adherence_stats(client):
    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)

    # Seed meal logs directly via DB session override isn't easy in HTTP tests,
    # so we use the adherence endpoint with empty logs first.
    response = await client.get(
        f"/api/v1/clients/{client_id}/adherence",
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] == client_id
    assert data["period_days"] == 7
    assert data["total_completed"] == 0
    assert data["adherence_pct"] == 0
    assert len(data["daily"]) == 7


@pytest.mark.asyncio
async def test_client_adherence_tenant_isolation(client):
    token_a = await _register_and_get_token(client, "a@nutriplan.in")
    token_b = await _register_and_get_token(client, "b@nutriplan.in")
    client_id = await _create_client(client, token_a)

    response = await client.get(
        f"/api/v1/clients/{client_id}/adherence",
        headers=_auth_header(token_b),
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_overview(client):
    token = await _register_and_get_token(client)
    await _create_client(client, token)

    response = await client.get("/api/v1/dashboard", headers=_auth_header(token))
    assert response.status_code == 200
    data = response.json()
    assert data["total_clients"] == 1
    assert data["active_clients"] == 1
    assert "avg_adherence_pct" in data
    assert "clients_needing_attention" in data
    assert "recent_activity" in data


@pytest.mark.asyncio
async def test_dashboard_stats_legacy_endpoint(client):
    token = await _register_and_get_token(client)
    await _create_client(client, token)

    response = await client.get("/api/v1/dashboard/stats", headers=_auth_header(token))
    assert response.status_code == 200
    data = response.json()
    assert data["active_clients"] == 1
