from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader # For basic API Key security example
from app.infrastructure.adapters.api.schemas import VehicleEventRequest, VehicleEventResponse
from app.core.services.vehicle_event_processor_service import VehicleEventProcessorService
from app.core.domain.entities import VehicleEvent
from app.infrastructure.dependencies import get_vehicle_event_processor_service
from app.infrastructure.config.settings import settings
from typing import Dict

router = APIRouter()

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
        result_message = await service.process_event(event)
        return {"status": "OK", "message": result_message}
    except Exception as e:
        print(f"Error processing vehicle event for {request.idveh}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {e}")