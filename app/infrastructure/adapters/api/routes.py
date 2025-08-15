from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader # For basic API Key security example
from app.infrastructure.adapters.api.schemas import VehicleEventRequest, VehicleEventResponse
from app.core.services.vehicle_event_processor_service import VehicleEventProcessorService
from app.core.domain.entities import VehicleEvent
from app.infrastructure.dependencies import get_vehicle_event_processor_service
from app.infrastructure.config.settings import settings
from typing import Dict

router = APIRouter()

# --- OWASP Top 10 Considerations ---
# A01:2021-Broken Access Control & A07:2021-Security Misconfiguration
# Implement API Key or OAuth2 for authentication.
# For simplicity, using a basic API Key header. In production, use a more robust solution like JWT/OAuth2.

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Invalid API Key.",
            headers={"WWW-Authenticate": "APIKey"},
        )
    return api_key

@router.post("/process-vehicle-event", response_model=VehicleEventResponse, status_code=status.HTTP_200_OK,
             dependencies=[Depends(verify_api_key)]) # Apply API Key security
async def process_vehicle_event_api(
    request: VehicleEventRequest,
    service: VehicleEventProcessorService = Depends(get_vehicle_event_processor_service)
) -> Dict[str, str]:
    """
    Procesa un evento de un vehículo recibido a través de la API.
    Transforma los datos del Request a la entidad de dominio y los procesa.
    """
    # A03:2021-Injection (SQL Injection) - Handled by ORM (SQLAlchemy) in repositories
    # A04:2021-Insecure Design - Addressed by Hexagonal Architecture and clear separation of concerns.
    # A05:2021-Security Misconfiguration - Covered by env vars for sensitive data, API Key.
    # A06:2021-Vulnerable and Outdated Components - Ensure `requirements.txt` is up-to-date and scanned.
    # A08:2021-Software and Data Integrity Failures - Data validation by Pydantic. Integrity managed by DB transactions.
    # A09:2021-Security Logging and Monitoring - Logging to console (basic), extend with proper logging tools.
    # A10:2021-Server-Side Request Forgery (SSRF) - No external requests based on user input for now. Geocoding is controlled.

    # Map Pydantic request to domain entity
    event = VehicleEvent(
        event_type=request.tipo,
        vehicle_id=request.idveh,
        event_code=request.idevento_,
        system_date_str=request.fechasys_,
        speed=request.speed,
        latitude_raw=request.lat,
        longitude_raw=request.lon,
        odometer=request.odometer,
        ip_address=request.ip,
        port=request.port,
        geofence_index=request.indexgeocerca,
        vehicle_on=request.vehicleon_,
        signal_status=request.signal_,
        realtime_date=request.realtime_,
        address=request.address_,
        city=request.city_,
        department=request.department_,
        keep_alive_date=request.fechakeep
    )

    try:
        # A02:2021-Cryptographic Failures - No direct sensitive data handling in this endpoint, but DB connections are secured via SSL.
        # A03:2021-Injection (Input Validation) - Pydantic handles this for the API.
        result_message = await service.process_event(event)
        
        return {"status": "OK", "message": result_message}
    except Exception as e:
        print(f"Error processing vehicle event for {request.idveh}: {e}")
        # A09:2021-Security Logging and Monitoring - Log errors with context.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")