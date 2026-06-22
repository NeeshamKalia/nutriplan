"""Tests for authentication endpoints.

Tests cover: register, login, refresh, logout, /me
Uses fixtures from conftest.py (in-memory SQLite with type patching).
"""

import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    """Register a new dietitian -> returns tokens + profile."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "neha@nutriplan.in",
            "password": "password123",
            "full_name": "Dr. Neha Sharma",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["dietitian"]["email"] == "neha@nutriplan.in"
    assert data["dietitian"]["slug"] == "dr-neha-sharma"
    assert data["dietitian"]["full_name"] == "Dr. Neha Sharma"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Registering with an existing email -> 409."""
    payload = {
        "email": "neha@nutriplan.in",
        "password": "password123",
        "full_name": "Dr. Neha Sharma",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client):
    """Password less than 8 chars -> 422 validation error."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@test.com",
            "password": "short",
            "full_name": "Test User",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    """Login with correct credentials -> returns tokens."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "neha@nutriplan.in",
            "password": "password123",
            "full_name": "Dr. Neha Sharma",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "neha@nutriplan.in", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["dietitian"]["email"] == "neha@nutriplan.in"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Login with wrong password -> 401."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "neha@nutriplan.in",
            "password": "password123",
            "full_name": "Dr. Neha Sharma",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "neha@nutriplan.in", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    """Login with unknown email -> 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "password123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client):
    """GET /me with valid access token -> returns profile."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "neha@nutriplan.in",
            "password": "password123",
            "full_name": "Dr. Neha Sharma",
        },
    )
    token = reg.json()["access_token"]
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "neha@nutriplan.in"
    assert data["slug"] == "dr-neha-sharma"


@pytest.mark.asyncio
async def test_me_without_token(client):
    """GET /me without token -> 403."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_me_with_invalid_token(client):
    """GET /me with garbage token -> 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    """Refresh with valid refresh token -> new token pair."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "neha@nutriplan.in",
            "password": "password123",
            "full_name": "Dr. Neha Sharma",
        },
    )
    refresh = reg.json()["refresh_token"]
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] != refresh


@pytest.mark.asyncio
async def test_refresh_token_reuse_detected(client):
    """Using a refresh token twice -> second time rejected (theft detection)."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "neha@nutriplan.in",
            "password": "password123",
            "full_name": "Dr. Neha Sharma",
        },
    )
    refresh = reg.json()["refresh_token"]
    await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_theft_revokes_all_tokens(client):
    """Full theft detection scenario:

    1. User registers → gets refresh_token_A
    2. User refreshes → gets refresh_token_B (A is revoked normally)
    3. Attacker uses stolen refresh_token_A (already revoked)
       → THEFT DETECTED → ALL tokens for this user are revoked
    4. User tries refresh_token_B → REJECTED (even though B was valid)

    This proves the entire token family is invalidated when theft is detected.
    """
    # Step 1: Register
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "neha@nutriplan.in",
            "password": "password123",
            "full_name": "Dr. Neha Sharma",
        },
    )
    token_a = reg.json()["refresh_token"]

    # Step 2: Legitimate refresh → token_a revoked, token_b created
    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": token_a}
    )
    assert refresh_response.status_code == 200
    token_b = refresh_response.json()["refresh_token"]
    assert token_b != token_a  # New token issued

    # Step 3: Attacker uses stolen token_a (already revoked) → THEFT
    theft_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": token_a}
    )
    assert theft_response.status_code == 401
    assert "revoked" in theft_response.json()["detail"].lower()

    # Step 4: Legitimate user's token_b is NOW ALSO INVALID
    # This is the critical security assertion — the entire family is dead
    legit_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": token_b}
    )
    assert legit_response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(client):
    """PUT /me updates practice profile fields."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "neha@nutriplan.in",
            "password": "password123",
            "full_name": "Dr. Neha Sharma",
        },
    )
    token = reg.json()["access_token"]
    response = await client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "practice_name": "Neha Nutrition Clinic",
            "bio": "PCOS and weight management specialist.",
            "specializations": ["PCOS", "Weight Loss"],
            "phone": "+919876543210",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["practice_name"] == "Neha Nutrition Clinic"
    assert data["bio"] == "PCOS and weight management specialist."
    assert data["specializations"] == ["PCOS", "Weight Loss"]
    assert data["phone"] == "+919876543210"


@pytest.mark.asyncio
async def test_setup_whatsapp(client):
    """PUT /me/whatsapp stores WhatsApp Business credentials."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "neha@nutriplan.in",
            "password": "password123",
            "full_name": "Dr. Neha Sharma",
        },
    )
    token = reg.json()["access_token"]
    response = await client.put(
        "/api/v1/auth/me/whatsapp",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "whatsapp_phone_number_id": "123456789",
            "whatsapp_access_token": "test-token",
            "whatsapp_business_account_id": "waba-1",
        },
    )
    assert response.status_code == 200
    assert response.json()["has_whatsapp_setup"] is True


@pytest.mark.asyncio
async def test_logout(client):
    """Logout revokes refresh token -> subsequent refresh fails."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "neha@nutriplan.in",
            "password": "password123",
            "full_name": "Dr. Neha Sharma",
        },
    )
    refresh = reg.json()["refresh_token"]
    response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": refresh}
    )
    assert response.status_code == 204
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh}
    )
    assert response.status_code == 401
