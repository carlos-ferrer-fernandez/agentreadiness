"""Tests for health check and root endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "services" in data


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AgentReadiness API"
    assert "version" in data
