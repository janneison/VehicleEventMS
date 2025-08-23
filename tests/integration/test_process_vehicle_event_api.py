import os
import sys
from pathlib import Path

import pytest
import python_multipart
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from dotenv import load_dotenv

load_dotenv()  # Carga las variables del archivo .env

database_url = os.getenv("DATABASE_URL")
api_key = os.getenv("API_KEY")
sys.modules["multipart"] = python_multipart
sys.path.append(str(Path(__file__).resolve().parents[2]))

# Set required environment variables before importing the app
os.environ.setdefault("DATABASE_URL", database_url)
os.environ.setdefault("Maps_API_KEY", "test")
os.environ.setdefault("API_KEY", api_key)

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
        "idveh": "SOBUSA305",
        "idevento_": 2,
        "fechasys_": "2025-08-20T00:00:00",
        "speed": 10.0,
        "lat": "0.9790",
        "lon": "-74.8007",
        "odometer": 123.4,
        "ip": "127.0.0.1",
        "port": 8080,
        "indexgeocerca": 1,
        "vehicleon_": True,
        "signal_": "OK",
        "realtime_": "2025-08-20T00:00:00",
        "address_": "Main St",
        "city_": "Town",
        "department_": "State",
        "fechakeep": "2025-08-20T00:00:00",
    }

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/vehicle-events/process-vehicle-event",
                json=payload,
                headers={"X-API-Key": api_key},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "OK"
            assert data["message"] == "processed"

