from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_health_returns_ok_when_ollama_up(client):
    with patch("application.health.HealthService.check_ollama", new=AsyncMock(return_value=("up", None))):
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["checks"]["api"] == "up"
    assert data["checks"]["ollama"] == "up"
    assert "version" in data


@pytest.mark.asyncio
async def test_health_returns_degraded_when_ollama_down(client):
    with patch(
        "application.health.HealthService.check_ollama",
        new=AsyncMock(return_value=("down", "Ollama sidecar unreachable at http://localhost:11434")),
    ):
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["ollama"] == "down"
    assert "message" in data
