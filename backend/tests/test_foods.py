"""Tests for food items router."""

import json
from pathlib import Path

import pytest
import pytest_asyncio

from app.database import get_db
from app.main import app
from app.models.food_item import FoodItem


async def _register_and_get_token(client, email="neha@nutriplan.in", name="Dr. Neha Sharma"):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": name},
    )
    return resp.json()["access_token"]


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def seed_foods(client):
    override_gen = app.dependency_overrides[get_db]()
    db_session = await override_gen.__anext__()
    
    foods = [
        FoodItem(
            name="Roti", category="grains", is_vegetarian=True, is_vegan=True,
            is_gluten_free=False, calories_per_100g=297, protein_per_100g=9.0,
            carbs_per_100g=58.0, fat_per_100g=3.0, common_allergens=["wheat"]
        ),
        FoodItem(
            name="Paneer", category="dairy", is_vegetarian=True, is_vegan=False,
            is_gluten_free=True, calories_per_100g=265, protein_per_100g=18.0,
            carbs_per_100g=3.5, fat_per_100g=20.0, common_allergens=["dairy"]
        ),
        FoodItem(
            name="Chicken", category="meat", is_vegetarian=False, is_vegan=False,
            is_gluten_free=True, calories_per_100g=165, protein_per_100g=31.0,
            carbs_per_100g=0.0, fat_per_100g=3.6, common_allergens=[]
        )
    ]
    db_session.add_all(foods)
    await db_session.commit()
    
    # Clean up generator
    try:
        await override_gen.__anext__()
    except StopAsyncIteration:
        pass


@pytest.mark.asyncio
async def test_list_foods_no_filters(client, seed_foods):
    token = await _register_and_get_token(client)
    resp = await client.get("/api/v1/foods", headers=_auth_header(token))
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_foods_search(client, seed_foods):
    token = await _register_and_get_token(client)
    resp = await client.get("/api/v1/foods?q=Paneer", headers=_auth_header(token))
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Paneer"


@pytest.mark.asyncio
async def test_list_foods_filter_category(client, seed_foods):
    token = await _register_and_get_token(client)
    resp = await client.get("/api/v1/foods?category=grains", headers=_auth_header(token))
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Roti"


@pytest.mark.asyncio
async def test_list_foods_filter_veg(client, seed_foods):
    token = await _register_and_get_token(client)
    resp = await client.get("/api/v1/foods?is_vegetarian=true", headers=_auth_header(token))
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    names = [item["name"] for item in data["items"]]
    assert "Roti" in names
    assert "Paneer" in names
    assert "Chicken" not in names


def test_food_seed_meets_mvp_minimum():
    """TASK-302 requires 200+ curated Indian food items in the seed file."""
    seed_file = Path(__file__).resolve().parent.parent / "seed" / "food_items.json"
    data = json.loads(seed_file.read_text(encoding="utf-8"))
    assert len(data) >= 200
    names = [item["name"] for item in data]
    assert len(names) == len(set(names))

    dal_hits = [
        item for item in data
        if item.get("category") == "lentil" or "dal" in item["name"].lower()
    ]
    assert len(dal_hits) >= 5


@pytest.mark.asyncio
async def test_create_custom_food(client, seed_foods):
    token = await _register_and_get_token(client)
    resp = await client.post(
        "/api/v1/foods",
        headers=_auth_header(token),
        json={
            "name": "Custom Protein Shake",
            "category": "beverages",
            "calories_per_100g": 120,
            "protein_per_100g": 20,
            "carbs_per_100g": 5,
            "fat_per_100g": 2,
            "is_vegetarian": True,
            "is_vegan": True,
            "is_gluten_free": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Custom Protein Shake"


@pytest.mark.asyncio
async def test_update_custom_food(client, seed_foods):
    token = await _register_and_get_token(client)
    create = await client.post(
        "/api/v1/foods",
        headers=_auth_header(token),
        json={
            "name": "My Sabzi",
            "category": "vegetables",
            "calories_per_100g": 80,
            "protein_per_100g": 3,
            "carbs_per_100g": 10,
            "fat_per_100g": 4,
            "is_vegetarian": True,
            "is_vegan": True,
            "is_gluten_free": True,
        },
    )
    food_id = create.json()["id"]

    resp = await client.put(
        f"/api/v1/foods/{food_id}",
        headers=_auth_header(token),
        json={"name": "My Updated Sabzi", "calories_per_100g": 90},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "My Updated Sabzi"
    assert resp.json()["calories_per_100g"] == 90


@pytest.mark.asyncio
async def test_cannot_update_system_food(client, seed_foods):
    token = await _register_and_get_token(client)
    list_resp = await client.get("/api/v1/foods?q=Roti", headers=_auth_header(token))
    roti_id = list_resp.json()["items"][0]["id"]

    resp = await client.put(
        f"/api/v1/foods/{roti_id}",
        headers=_auth_header(token),
        json={"name": "Hacked Roti"},
    )
    assert resp.status_code == 404
