from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

class GeolocationInfo(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    department: Optional[str] = None
    
    def is_valid(self) -> bool:
        return self.address is not None and self.city is not None and self.department is not None and \
               self.address != 'No Disponible' and self.city != 'No Disponible' and self.department != 'No Disponible'

class VehicleEvent(BaseModel):
    event_type: int # tipo in SP (0, 300, 128)
    vehicle_id: str = Field(..., max_length=50) # idveh
    event_code: int = Field(..., ge=0) # idevento_
    system_date_str: str # fechasys_
    speed: float = Field(..., ge=0)
    latitude_raw: str # lat (e.g., 'N10.12345')
    longitude_raw: str # lon (e.g., 'W074.12345')
    odometer: Optional[float] = None
    ip_address: str
    port: int
    geofence_index: Optional[int] = None # indexgeocerca
    vehicle_on: Optional[bool] = None # vehicleon_ (signal for ignition)
    signal_status: Optional[str] = None # signal_ (e.g., 'OK', 'NOK')
    realtime_date: Optional[datetime] = None # realtime_
    address: Optional[str] = None # address_ (from modem if available)
    city: Optional[str] = None # city_ (from modem if available)
    department: Optional[str] = None # department_ (from modem if available)
    keep_alive_date: datetime # fechakeep (fallback date)

    # Calculated fields, not part of input directly
    processed_latitude: Optional[float] = None
    processed_longitude: Optional[float] = None
    processed_speed: Optional[float] = None
    processed_date: Optional[datetime] = None
    geolocation: Optional[GeolocationInfo] = None
    is_static_event: Optional[bool] = False
    is_ignition_event: Optional[bool] = False
    period_id: Optional[int] = None # idperiodo_
    ignition_status: Optional[str] = None # enc_apa_
    current_driver_id: Optional[int] = None # idconductor_
    event_db_id: Optional[int] = None # idevt

class Vehicle(BaseModel):
    idvehiculo: str
    estado: str
    tipo_modem: Optional[str] = None
    velocidad: Optional[float] = None
    direccion: Optional[str] = None
    latitud: Optional[str] = None
    longitud: Optional[str] = None
    municipio: Optional[str] = None
    departamento: Optional[str] = None
    ultperiodo: Optional[int] = None
    enc_apa: Optional[str] = None
    idconductor: Optional[int] = None
    idconductor_actual: Optional[int] = None
    ultimaactualizacion: Optional[datetime] = None
    ultimoevento: Optional[int] = None
    rumbo: Optional[int] = None
    rumbo_linea_tiempo: Optional[int] = None
    indexgeoc: Optional[int] = None
    estadosenal: Optional[str] = None
    encendido: Optional[bool] = None
    indexevento: Optional[int] = None
    contratista: Optional[str] = None
    recurso: Optional[str] = None

class EventoDescripcion(BaseModel):
    evento: str
    estatico: Optional[str] = 'N' # 'S' for static, 'N' for not

class Proceso(BaseModel):
    proceso: str
    contratistas: str
    toleranciatiempo: int

class PeriodoActivo(BaseModel):
    idperiodo: int
    idvehiculo: str
    fechadesde: datetime
    fechahasta: Optional[datetime] = None
    idconductor: Optional[int] = None

class PeriodoConductor(BaseModel):
    idperiodo: int
    idvehiculo: str
    idconductor: int
    fechadesde: datetime
    fechahasta: Optional[datetime] = None

class ProgramacionEspecialVehiculo(BaseModel):
    idprogramacion: int
    idvehiculo: str
    fechasalida: datetime
    finalizado: str
    cancelada: str
    activa: str
    idruta: int

class RutaEspecialDetalle(BaseModel):
    idruta: int
    idpunto: int
    orden: int
    tiempoglobal: Optional[float] = None # tiempoglobal in SP

class PuntoControlEspecial(BaseModel):
    idpunto: int
    latitud: float
    longitud: float
    radio: float

class RutaEspecialControl(BaseModel):
    idprogramacion: int
    idpunto: int
    fecha: datetime
    tiempoint: float
    tiempoglobal: float
    diferenciaint: float
    diferenciaglobal: float
    orden: int

class EventoResumen(BaseModel):
    idvehiculo: str
    idevento: int
    valor: int
    fecha: datetime
    hora: int