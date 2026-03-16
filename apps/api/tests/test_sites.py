"""Tests for the sites API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_site(client: AsyncClient):
    response = await client.post("/api/sites", json={
        "url": "https://docs.example.com",
        "name": "Example Docs",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Example Docs"
    assert data["url"] == "https://docs.example.com/"
    assert data["status"] == "PENDING"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_sites_empty(client: AsyncClient):
    response = await client.get("/api/sites")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_sites_after_create(client: AsyncClient):
    await client.post("/api/sites", json={
        "url": "https://docs.example.com",
        "name": "Example Docs",
    })
    response = await client.get("/api/sites")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Example Docs"


@pytest.mark.asyncio
async def test_get_site(client: AsyncClient):
    create_response = await client.post("/api/sites", json={
        "url": "https://docs.example.com",
        "name": "Test",
    })
    site_id = create_response.json()["id"]

    response = await client.get(f"/api/sites/{site_id}")
    assert response.status_code == 200
    assert response.json()["id"] == site_id


@pytest.mark.asyncio
async def test_get_nonexistent_site(client: AsyncClient):
    response = await client.get("/api/sites/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_site(client: AsyncClient):
    create_response = await client.post("/api/sites", json={
        "url": "https://docs.example.com",
        "name": "Old Name",
    })
    site_id = create_response.json()["id"]

    response = await client.patch(f"/api/sites/{site_id}", json={"name": "New Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_site(client: AsyncClient):
    create_response = await client.post("/api/sites", json={
        "url": "https://docs.example.com",
        "name": "To Delete",
    })
    site_id = create_response.json()["id"]

    response = await client.delete(f"/api/sites/{site_id}")
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/api/sites/{site_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_request():
    """Requests without auth should be rejected."""
    from httpx import AsyncClient, ASGITransport
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/sites")
        assert response.status_code == 401
