"""Tests for public intake form."""

import pytest


@pytest.mark.asyncio
async def test_intake_creates_lead_client(client):
    """POST intake creates a client with status=lead."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "neha@nutriplan.in",
            "password": "password123",
            "full_name": "Dr. Neha Sharma",
        },
    )
    slug = reg.json()["dietitian"]["slug"]

    resp = await client.post(
        f"/api/v1/public/dietitians/{slug}/intake",
        json={
            "full_name": "Priya Kapoor",
            "whatsapp_number": "9876543210",
            "primary_goal": "weight_loss",
            "dietary_type": "vegetarian",
            "notes": "Interested in PCOS plan",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "client_id" in data
    assert "Thank you" in data["message"]

    token = reg.json()["access_token"]
    clients = await client.get(
        "/api/v1/clients",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert clients.status_code == 200
    items = clients.json()["clients"]
    lead = next(c for c in items if c["full_name"] == "Priya Kapoor")
    assert lead["status"] == "lead"
    assert lead["whatsapp_number"] == "+919876543210"


@pytest.mark.asyncio
async def test_intake_spec_path(client):
    """POST /p/:slug/intake works per technical spec."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "spec@nutriplan.in",
            "password": "password123",
            "full_name": "Spec Dietitian",
        },
    )
    slug = reg.json()["dietitian"]["slug"]

    resp = await client.post(
        f"/p/{slug}/intake",
        json={
            "full_name": "Lead User",
            "whatsapp_number": "+919111111111",
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_intake_duplicate_whatsapp(client):
    """Duplicate WhatsApp on same dietitian -> 409."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@nutriplan.in",
            "password": "password123",
            "full_name": "Dup Dietitian",
        },
    )
    slug = reg.json()["dietitian"]["slug"]
    payload = {"full_name": "First Lead", "whatsapp_number": "9998887776"}

    await client.post(f"/api/v1/public/dietitians/{slug}/intake", json=payload)
    resp = await client.post(f"/api/v1/public/dietitians/{slug}/intake", json=payload)
    assert resp.status_code == 409
