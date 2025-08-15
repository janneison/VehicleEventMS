import os
import sys
from pathlib import Path

import pytest
from httpx import AsyncClient
from asgi_lifespan import LifespanManager

sys.path.append(str(Path(__file__).resolve().parents[2]))

# Set required environment variables before importing the app
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
os.environ.setdefault("Maps_API_KEY", "test")
os.environ.setdefault("API_KEY", "test-key")

from app.main import app  # noqa: E402
from app.infrastructure.dependencies import get_vehicle_event_processor_service


class DummyService:
    async def process_event(self, event):
        return "processed"


@pytest.fixture(autouse=True)
def override_dependencies():
    async def _get_service():
        return DummyService()

    app.dependency_overrides[get_vehicle_event_processor_service] = _get_service
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_process_vehicle_event_endpoint():
    payload = {
        "tipo": 0,
        "idveh": "veh1",
        "idevento_": 2,
        "fechasys_": "2024-01-01T00:00:00",
        "speed": 10.0,
        "lat": "N10.0",
        "lon": "W074.0",
        "odometer": 123.4,
        "ip": "127.0.0.1",
        "port": 8080,
        "indexgeocerca": 1,
        "vehicleon_": True,
        "signal_": "OK",
        "realtime_": "2024-01-01T00:00:00",
        "address_": "Main St",
        "city_": "Town",
        "department_": "State",
        "fechakeep": "2024-01-01T00:00:00",
    }

    async with LifespanManager(app):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/vehicle-events/process-vehicle-event",
                json=payload,
                headers={"X-API-Key": "test-key"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "OK"
            assert data["message"] == "processed"
