"""Tests for food items router."""

import pytest

from app.models.food_item import FoodItem
from sqlalchemy.ext.asyncio import AsyncSession


async def _register_and_get_token(client, email="neha@nutriplan.in", name="Dr. Neha Sharma"):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": name},
    )
    return resp.json()["access_token"]


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


from app.main import app
from app.database import get_db

@pytest.fixture
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
