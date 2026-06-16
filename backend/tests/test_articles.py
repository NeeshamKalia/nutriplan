"""Tests for article CRUD and public endpoints.

Covers: create, list, get, update, publish, unpublish, delete,
multi-tenant isolation, auto-slug generation, and public access.
"""

import pytest


async def _register_and_get_token(client, email="neha@nutriplan.in", name="Dr. Neha Sharma"):
    """Helper: register a dietitian and return (access_token, dietitian_data)."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": name},
    )
    data = resp.json()
    return data["access_token"], data["dietitian"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_article(client):
    """Create an article -> 201 with auto-generated slug."""
    token, _ = await _register_and_get_token(client)
    resp = await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={
            "title": "Top 10 Indian Superfoods",
            "content": "Turmeric, moringa, amla...",
            "tags": ["nutrition", "superfoods"],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Top 10 Indian Superfoods"
    assert data["slug"] == "top-10-indian-superfoods"
    assert data["status"] == "draft"
    assert data["tags"] == ["nutrition", "superfoods"]


@pytest.mark.asyncio
async def test_create_article_custom_slug(client):
    """Create an article with explicit slug."""
    token, _ = await _register_and_get_token(client)
    resp = await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={
            "title": "My Article",
            "slug": "custom-url",
            "content": "Content here.",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["slug"] == "custom-url"


@pytest.mark.asyncio
async def test_create_article_duplicate_slug_auto_increments(client):
    """Creating two articles with the same title auto-increments slug."""
    token, _ = await _register_and_get_token(client)
    payload = {"title": "Same Title", "content": "Content."}
    r1 = await client.post("/api/v1/articles", headers=_auth(token), json=payload)
    r2 = await client.post("/api/v1/articles", headers=_auth(token), json=payload)
    assert r1.json()["slug"] == "same-title"
    assert r2.json()["slug"] == "same-title-2"


@pytest.mark.asyncio
async def test_list_articles(client):
    """List all articles for the dietitian."""
    token, _ = await _register_and_get_token(client)
    for i in range(3):
        await client.post(
            "/api/v1/articles",
            headers=_auth(token),
            json={"title": f"Article {i}", "content": f"Content {i}"},
        )
    resp = await client.get("/api/v1/articles", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["articles"]) == 3


@pytest.mark.asyncio
async def test_list_articles_filter_by_status(client):
    """Filter articles by status."""
    token, _ = await _register_and_get_token(client)
    await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={"title": "Draft One", "content": "C", "status": "draft"},
    )
    await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={"title": "Published One", "content": "C", "status": "published"},
    )
    resp = await client.get("/api/v1/articles?status=published", headers=_auth(token))
    data = resp.json()
    assert data["total"] == 1
    assert data["articles"][0]["status"] == "published"


@pytest.mark.asyncio
async def test_get_article(client):
    """Get a single article by ID."""
    token, _ = await _register_and_get_token(client)
    create_resp = await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={"title": "Test Article", "content": "Details here."},
    )
    article_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/articles/{article_id}", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Article"


@pytest.mark.asyncio
async def test_get_nonexistent_article(client):
    """Get article with bogus ID -> 404."""
    token, _ = await _register_and_get_token(client)
    resp = await client.get(
        "/api/v1/articles/00000000-0000-0000-0000-000000000001",
        headers=_auth(token),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_article(client):
    """Partial update on an article."""
    token, _ = await _register_and_get_token(client)
    create_resp = await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={"title": "Old Title", "content": "Old content."},
    )
    article_id = create_resp.json()["id"]
    resp = await client.put(
        f"/api/v1/articles/{article_id}",
        headers=_auth(token),
        json={"title": "New Title", "summary": "Updated summary"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "New Title"
    assert data["summary"] == "Updated summary"
    assert data["content"] == "Old content."


@pytest.mark.asyncio
async def test_publish_article(client):
    """Publish a draft article."""
    token, _ = await _register_and_get_token(client)
    create_resp = await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={"title": "Draft", "content": "Content."},
    )
    article_id = create_resp.json()["id"]
    resp = await client.post(
        f"/api/v1/articles/{article_id}/publish", headers=_auth(token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "published"
    assert data["published_at"] is not None


@pytest.mark.asyncio
async def test_unpublish_article(client):
    """Unpublish a published article back to draft."""
    token, _ = await _register_and_get_token(client)
    create_resp = await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={"title": "Live Article", "content": "C.", "status": "published"},
    )
    article_id = create_resp.json()["id"]
    resp = await client.post(
        f"/api/v1/articles/{article_id}/unpublish", headers=_auth(token)
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_delete_article(client):
    """Delete an article -> subsequent GET returns 404."""
    token, _ = await _register_and_get_token(client)
    create_resp = await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={"title": "Delete Me", "content": "Gone soon."},
    )
    article_id = create_resp.json()["id"]
    del_resp = await client.delete(
        f"/api/v1/articles/{article_id}", headers=_auth(token)
    )
    assert del_resp.status_code == 200
    get_resp = await client.get(
        f"/api/v1/articles/{article_id}", headers=_auth(token)
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_multi_tenant_isolation(client):
    """Dietitian A cannot see Dietitian B's articles."""
    token_a, _ = await _register_and_get_token(client, "a@test.com", "Dr. A")
    token_b, _ = await _register_and_get_token(client, "b@test.com", "Dr. B")

    create_resp = await client.post(
        "/api/v1/articles",
        headers=_auth(token_a),
        json={"title": "Private Article", "content": "Secret."},
    )
    article_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/articles/{article_id}", headers=_auth(token_b))
    assert resp.status_code == 404

    list_resp = await client.get("/api/v1/articles", headers=_auth(token_b))
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_public_dietitian_profile(client):
    """Public endpoint returns dietitian profile by slug."""
    token, dietitian = await _register_and_get_token(client)
    slug = dietitian["slug"]
    resp = await client.get(f"/api/v1/public/dietitians/{slug}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Dr. Neha Sharma"
    assert data["slug"] == slug


@pytest.mark.asyncio
async def test_public_articles_only_published(client):
    """Public endpoint only returns published articles."""
    token, dietitian = await _register_and_get_token(client)
    slug = dietitian["slug"]

    await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={"title": "Draft Article", "content": "Not visible.", "status": "draft"},
    )
    await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={
            "title": "Published Article",
            "content": "Visible.",
            "status": "published",
        },
    )

    resp = await client.get(f"/api/v1/public/dietitians/{slug}/articles")
    assert resp.status_code == 200
    articles = resp.json()
    assert len(articles) == 1
    assert articles[0]["title"] == "Published Article"


@pytest.mark.asyncio
async def test_public_single_article(client):
    """Public endpoint returns a single published article by slug."""
    token, dietitian = await _register_and_get_token(client)
    d_slug = dietitian["slug"]

    await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={
            "title": "Healthy Eating Tips",
            "content": "Eat more vegetables.",
            "status": "published",
        },
    )

    resp = await client.get(
        f"/api/v1/public/dietitians/{d_slug}/articles/healthy-eating-tips"
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Healthy Eating Tips"


@pytest.mark.asyncio
async def test_public_article_not_found_if_draft(client):
    """Public endpoint returns 404 for draft articles."""
    token, dietitian = await _register_and_get_token(client)
    d_slug = dietitian["slug"]

    await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={"title": "Secret Draft", "content": "Hidden."},
    )

    resp = await client.get(
        f"/api/v1/public/dietitians/{d_slug}/articles/secret-draft"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_article_without_auth(client):
    """Creating an article without auth -> 403."""
    resp = await client.post(
        "/api/v1/articles",
        json={"title": "Unauthorized", "content": "Nope."},
    )
    assert resp.status_code == 403


CLIENT_PAYLOAD = {
    "full_name": "Priya Kapoor",
    "whatsapp_number": "+919876543210",
    "age": 28,
    "gender": "female",
    "height_cm": 162,
    "weight_kg": 72,
    "target_weight_kg": 60,
    "activity_level": "light",
    "dietary_type": "veg",
    "cuisine_preference": "north_indian",
    "primary_goal": "weight_loss",
}


async def _create_published_article(client, token: str, title="Broadcast Me"):
    """Helper: create and publish an article."""
    create_resp = await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={
            "title": title,
            "summary": "Quick nutrition tips for busy professionals.",
            "content": "Full article body.",
            "status": "published",
        },
    )
    return create_resp.json()


@pytest.mark.asyncio
async def test_broadcast_article_to_active_clients(client, monkeypatch):
    """Broadcast sends WhatsApp messages to active clients with phone numbers."""
    token, _ = await _register_and_get_token(client)
    article = await _create_published_article(client, token)

    await client.post(
        "/api/v1/clients",
        headers=_auth(token),
        json={**CLIENT_PAYLOAD, "whatsapp_number": "+919876543211"},
    )
    await client.post(
        "/api/v1/clients",
        headers=_auth(token),
        json={
            **CLIENT_PAYLOAD,
            "full_name": "Rahul Sharma",
            "whatsapp_number": "+919876543212",
        },
    )
    archived_resp = await client.post(
        "/api/v1/clients",
        headers=_auth(token),
        json={
            **CLIENT_PAYLOAD,
            "full_name": "Archived Client",
            "whatsapp_number": "+919876543213",
        },
    )
    await client.delete(
        f"/api/v1/clients/{archived_resp.json()['id']}",
        headers=_auth(token),
    )

    sent_numbers: list[str] = []
    sent_bodies: list[str] = []

    async def mock_send(to_number, body, db=None, client_id=None, dietitian_id=None):
        sent_numbers.append(to_number)
        sent_bodies.append(body)
        return {"messages": [{"id": f"msg_{to_number}"}]}

    async def mock_sleep(_):
        return None

    monkeypatch.setattr(
        "app.services.article_service.whatsapp_service.send_text_message",
        mock_send,
    )
    monkeypatch.setattr("app.services.article_service.asyncio.sleep", mock_sleep)

    resp = await client.post(
        f"/api/v1/articles/{article['id']}/broadcast",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["sent_count"] == 2
    assert data["failed_count"] == 0
    assert data["skipped_count"] == 0
    assert data["total_active_clients"] == 2
    assert data["article"]["broadcast_count"] == 2
    assert data["article"]["broadcasted_at"] is not None
    assert set(sent_numbers) == {"+919876543211", "+919876543212"}
    assert all("Broadcast Me" in body for body in sent_bodies)
    assert all("/p/" in body for body in sent_bodies)


@pytest.mark.asyncio
async def test_broadcast_draft_article_rejected(client):
    """Broadcasting a draft article -> 400."""
    token, _ = await _register_and_get_token(client)
    create_resp = await client.post(
        "/api/v1/articles",
        headers=_auth(token),
        json={"title": "Draft Only", "content": "Not published."},
    )
    article_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/articles/{article_id}/broadcast",
        headers=_auth(token),
    )
    assert resp.status_code == 400
    assert "published" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_broadcast_multi_tenant_isolation(client, monkeypatch):
    """Dietitian B cannot broadcast Dietitian A's article."""
    token_a, _ = await _register_and_get_token(client, "a@test.com", "Dr. A")
    token_b, _ = await _register_and_get_token(client, "b@test.com", "Dr. B")
    article = await _create_published_article(client, token_a)

    async def mock_send(*args, **kwargs):
        return {"messages": [{"id": "x"}]}

    monkeypatch.setattr(
        "app.services.article_service.whatsapp_service.send_text_message",
        mock_send,
    )

    async def mock_sleep(_):
        return None

    monkeypatch.setattr("app.services.article_service.asyncio.sleep", mock_sleep)

    resp = await client.post(
        f"/api/v1/articles/{article['id']}/broadcast",
        headers=_auth(token_b),
    )
    assert resp.status_code == 404
