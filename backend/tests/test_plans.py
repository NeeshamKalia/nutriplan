"""Tests for meal plan management."""

import pytest

async def _register_and_get_token(client, email="neha@nutriplan.in", name="Dr. Neha Sharma"):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": name},
    )
    return resp.json()["access_token"]


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


async def _create_client(client, token):
    resp = await client.post(
        "/api/v1/clients",
        json={
            "full_name": "Test Client",
            "whatsapp_number": "+919999999999",
            "primary_goal": "weight_loss"
        },
        headers=_auth_header(token)
    )
    return resp.json()["id"]


PLAN_DATA = {
    "title": "Week 1 - PCOS Friendly",
    "week_start_date": "2026-06-15",
    "custom_instructions": "Drink 3L water daily.",
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
                    "calories": 250.5,
                    "protein_g": 10.2,
                    "carbs_g": 35.0,
                    "fat_g": 5.0,
                    "preparation_notes": "Use less oil"
                },
                {
                    "meal_type": "lunch",
                    "food_name": "Dal Makhani",
                    "portion_description": "1 bowl",
                    "portion_grams": 150,
                    "calories": 300,
                    "protein_g": 15.0,
                    "carbs_g": 40.0,
                    "fat_g": 8.0,
                    "preparation_notes": ""
                }
            ]
        },
        {
            "day_number": 2,
            "day_label": "Tuesday",
            "items": [
                {
                    "meal_type": "breakfast",
                    "food_name": "Poha",
                    "portion_description": "1 plate",
                    "portion_grams": 150,
                    "calories": 280,
                    "protein_g": 8.0,
                    "carbs_g": 45.0,
                    "fat_g": 6.0,
                    "preparation_notes": "Add peanuts"
                }
            ]
        }
    ]
}


@pytest.mark.asyncio
async def test_create_plan(client):
    """Test creating a plan calculates correct totals and averages."""
    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)

    response = await client.post(
        f"/api/v1/clients/{client_id}/plans",
        json=PLAN_DATA,
        headers=_auth_header(token)
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Week 1 - PCOS Friendly"
    assert data["status"] == "draft"
    assert len(data["days"]) == 2
    
    # Day 1: 250.5 + 300 = 550.5 cals
    assert data["days"][0]["total_calories"] == 550.5
    assert data["days"][0]["total_protein_g"] == 25.2
    
    # Day 2: 280 cals
    assert data["days"][1]["total_calories"] == 280
    
    # Plan averages: (550.5 + 280) / 2 = 415.25
    assert data["avg_daily_calories"] == 415.25
    assert data["avg_daily_protein_g"] == 16.6  # (25.2 + 8) / 2


@pytest.mark.asyncio
async def test_list_plans(client):
    """List plans for client."""
    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)

    await client.post(f"/api/v1/clients/{client_id}/plans", json=PLAN_DATA, headers=_auth_header(token))
    await client.post(f"/api/v1/clients/{client_id}/plans", json={**PLAN_DATA, "title": "Week 2"}, headers=_auth_header(token))

    response = await client.get(f"/api/v1/clients/{client_id}/plans", headers=_auth_header(token))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["plans"]) == 2
    # Verify summary fields are present
    assert "status" in data["plans"][0]
    assert "avg_daily_calories" in data["plans"][0]
    # Detailed fields should NOT be in the list view
    assert "days" not in data["plans"][0]


@pytest.mark.asyncio
async def test_get_plan_detail(client):
    """Get specific plan detail."""
    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)

    create_resp = await client.post(f"/api/v1/clients/{client_id}/plans", json=PLAN_DATA, headers=_auth_header(token))
    plan_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/plans/{plan_id}", headers=_auth_header(token))
    assert response.status_code == 200
    assert response.json()["title"] == "Week 1 - PCOS Friendly"
    assert len(response.json()["days"]) == 2


@pytest.mark.asyncio
async def test_update_plan(client):
    """Test updating a plan recalculates totals."""
    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)

    create_resp = await client.post(f"/api/v1/clients/{client_id}/plans", json=PLAN_DATA, headers=_auth_header(token))
    plan_id = create_resp.json()["id"]

    # Update: Replace days with only 1 day and 1 item (500 cals)
    update_data = {
        "title": "Updated Title",
        "days": [
            {
                "day_number": 1,
                "day_label": "Only Day",
                "items": [
                    {
                        "meal_type": "lunch",
                        "food_name": "Pizza",
                        "portion_description": "1 slice",
                        "calories": 500,
                        "protein_g": 20,
                        "carbs_g": 50,
                        "fat_g": 25
                    }
                ]
            }
        ]
    }

    response = await client.put(f"/api/v1/plans/{plan_id}", json=update_data, headers=_auth_header(token))
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert len(data["days"]) == 1
    assert data["avg_daily_calories"] == 500
    assert data["avg_daily_protein_g"] == 20


@pytest.mark.asyncio
async def test_approve_plan(client, monkeypatch):
    """Approve a plan delivers via WhatsApp when send succeeds."""
    async def mock_send(*args, **kwargs):
        return {"messages": [{"id": "wamid.test"}]}

    monkeypatch.setattr(
        "app.services.plan_service.whatsapp_service.send_text_message",
        mock_send,
    )

    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)

    create_resp = await client.post(f"/api/v1/clients/{client_id}/plans", json=PLAN_DATA, headers=_auth_header(token))
    plan_id = create_resp.json()["id"]

    response = await client.post(f"/api/v1/plans/{plan_id}/approve", headers=_auth_header(token))
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "delivered"
    assert data["approved_at"] is not None
    assert data["delivered_at"] is not None


@pytest.mark.asyncio
async def test_approve_plan_stays_approved_when_whatsapp_fails(client, monkeypatch):
    """Plan stays approved (not delivered) when WhatsApp send is skipped."""
    async def mock_send(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.services.plan_service.whatsapp_service.send_text_message",
        mock_send,
    )

    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)

    create_resp = await client.post(f"/api/v1/clients/{client_id}/plans", json=PLAN_DATA, headers=_auth_header(token))
    plan_id = create_resp.json()["id"]

    response = await client.post(f"/api/v1/plans/{plan_id}/approve", headers=_auth_header(token))
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["approved_at"] is not None
    assert data["delivered_at"] is None


MOCK_AI_PLAN = {
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
                },
                {
                    "meal_type": "lunch",
                    "food_name": "Moong Dal",
                    "portion_description": "1 bowl",
                    "portion_grams": 150,
                    "calories": 180,
                    "protein_g": 10,
                    "carbs_g": 25,
                    "fat_g": 3,
                },
            ],
        }
        for i in range(1, 8)
    ]
}

MOCK_AI_METADATA = {
    "model": "test-model",
    "tokens_used": 500,
    "cost_usd": 0.0,
    "duration_ms": 100,
}


@pytest.mark.asyncio
async def test_get_plan_validations(client, monkeypatch):
    async def mock_generate(*args, **kwargs):
        return MOCK_AI_PLAN, MOCK_AI_METADATA

    monkeypatch.setattr(
        "app.services.plan_service.generate_meal_plan",
        mock_generate,
    )

    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)

    gen_resp = await client.post(
        f"/api/v1/clients/{client_id}/plans/generate",
        headers=_auth_header(token),
        json={"week_start_date": "2026-06-16"},
    )
    plan_id = gen_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/plans/{plan_id}/validations",
        headers=_auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["validations"]) >= 1


@pytest.mark.asyncio
async def test_regenerate_draft_plan(client, monkeypatch):
    call_count = 0

    async def mock_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        plan = MOCK_AI_PLAN.copy()
        plan["days"] = [
            {**day, "day_label": f"Regenerated Day {day['day_number']}"}
            for day in MOCK_AI_PLAN["days"]
        ]
        return plan, MOCK_AI_METADATA

    monkeypatch.setattr(
        "app.services.plan_service.generate_meal_plan",
        mock_generate,
    )

    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)

    gen_resp = await client.post(
        f"/api/v1/clients/{client_id}/plans/generate",
        headers=_auth_header(token),
        json={"week_start_date": "2026-06-16"},
    )
    plan_id = gen_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/plans/{plan_id}/regenerate",
        headers=_auth_header(token),
        json={"custom_instructions": "More dal please"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"
    assert "Regenerated Day 1" in resp.json()["days"][0]["day_label"]
    assert call_count == 2


@pytest.mark.asyncio
async def test_regenerate_non_draft_fails(client, monkeypatch):
    async def mock_generate(*args, **kwargs):
        return MOCK_AI_PLAN, MOCK_AI_METADATA

    async def mock_send(*args, **kwargs):
        return {"messages": [{"id": "wamid.test"}]}

    monkeypatch.setattr(
        "app.services.plan_service.generate_meal_plan",
        mock_generate,
    )
    monkeypatch.setattr(
        "app.services.plan_service.whatsapp_service.send_text_message",
        mock_send,
    )

    token = await _register_and_get_token(client)
    client_id = await _create_client(client, token)

    gen_resp = await client.post(
        f"/api/v1/clients/{client_id}/plans/generate",
        headers=_auth_header(token),
        json={"week_start_date": "2026-06-16"},
    )
    plan_id = gen_resp.json()["id"]

    await client.post(f"/api/v1/plans/{plan_id}/approve", headers=_auth_header(token))

    resp = await client.post(
        f"/api/v1/plans/{plan_id}/regenerate",
        headers=_auth_header(token),
        json={"custom_instructions": "Try again"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_plan_multi_tenant_isolation(client):
    """Dietitian B cannot access Dietitian A's plans."""
    token_a = await _register_and_get_token(client, email="a@test.com", name="Alice")
    token_b = await _register_and_get_token(client, email="b@test.com", name="Bob")

    client_id_a = await _create_client(client, token_a)
    
    create_resp = await client.post(f"/api/v1/clients/{client_id_a}/plans", json=PLAN_DATA, headers=_auth_header(token_a))
    plan_id_a = create_resp.json()["id"]

    # Dietitian B tries to fetch Dietitian A's plan -> 404
    response = await client.get(f"/api/v1/plans/{plan_id_a}", headers=_auth_header(token_b))
    assert response.status_code == 404
