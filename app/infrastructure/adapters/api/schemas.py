from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class VehicleEventRequest(BaseModel):
    tipo: int = Field(..., description="Tipo de evento (0, 300 para normal, 128 para OTA)")
    idveh: str = Field(..., max_length=50, description="ID del vehículo")
    idevento_: int = Field(..., ge=0, description="Código del evento")
    fechasys_: str = Field(..., description="Fecha del sistema (string)")
    speed: float = Field(..., ge=0, description="Velocidad")
    lat: str = Field(..., description="Latitud (string, e.g., 'N10.12345')")
    lon: str = Field(..., description="Longitud (string, e.g., 'W074.12345')")
    odometer: Optional[float] = Field(None, ge=0, description="Valor del odómetro")
    ip: str = Field(..., description="Dirección IP del modem/dispositivo")
    port: int = Field(..., ge=0, description="Puerto del modem/dispositivo")
    indexgeocerca: Optional[int] = Field(None, description="Índice de la geocerca")
    vehicleon_: Optional[bool] = Field(None, description="Estado de encendido del vehículo")
    signal_: Optional[str] = Field(None, description="Estado de la señal GPS")
    realtime_: Optional[datetime] = Field(None, description="Fecha y hora real del evento")
    address_: Optional[str] = Field(None, description="Dirección proporcionada por el modem")
    city_: Optional[str] = Field(None, description="Ciudad proporcionada por el modem")
    department_: Optional[str] = Field(None, description="Departamento proporcionado por el modem")
    fechakeep: datetime = Field(..., description="Fecha de keep-alive (fecha de respaldo)")

class VehicleEventResponse(BaseModel):
    status: str = Field(..., example="OK")
    message: Optional[str] = None