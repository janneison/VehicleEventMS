from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime, date
from app.core.domain.entities import (
    VehicleEvent, Vehicle, EventoDescripcion, Proceso, GeolocationInfo,
    PeriodoActivo, PeriodoConductor, ProgramacionEspecialVehiculo,
    RutaEspecialDetalle, PuntoControlEspecial, RutaEspecialControl,
    EventoResumen
)

class VehicleEventRepository(ABC):
    @abstractmethod
    async def save_event(self, event: VehicleEvent) -> int:
        pass

    @abstractmethod
    async def save_odometer(self, vehicle_id: str, value: float, date: datetime):
        pass

    @abstractmethod
    async def get_last_event_with_gps(self, vehicle_id: str) -> Optional[VehicleEvent]:
        pass

    @abstractmethod
    async def insert_ejes_viales(self, address: str, city: str, latitude: float, longitude: float, department: str):
        pass

    @abstractmethod
    async def find_evento_descripcion(self, event_code: int) -> Optional[EventoDescripcion]:
        pass

    @abstractmethod
    async def find_eventos_resumen(self, vehicle_id: str, event_code: int, date: date, hour: int) -> Optional[EventoResumen]:
        pass

    @abstractmethod
    async def update_eventos_resumen(self, vehicle_id: str, event_code: int, date: date, hour: int, value: int):
        pass

    @abstractmethod
    async def insert_eventos_resumen(self, vehicle_id: str, event_code: int, value: int, date: date, hour: int):
        pass

class VehicleRepository(ABC):
    @abstractmethod
    async def get_active_vehicle_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        pass

    @abstractmethod
    async def update_vehicle_status(self, vehicle: Vehicle):
        pass

    @abstractmethod
    async def get_vehicle_tolerancia_tiempo(self, vehicle_contratista: str) -> int:
        pass
    
    @abstractmethod
    async def update_resource_gps_status(self, recurso_id: str, contratista_id: str, event_date: datetime, gps_ok: bool):
        pass

class PeriodRepository(ABC):
    @abstractmethod
    async def get_active_periodo(self, period_id: int) -> Optional[PeriodoActivo]:
        pass

    @abstractmethod
    async def create_periodo_activo(self, vehicle_id: str, start_date: datetime, driver_id: Optional[int]) -> int:
        pass

    @abstractmethod
    async def update_periodo_activo_end_date(self, period_id: int, end_date: datetime):
        pass

    @abstractmethod
    async def get_last_periodo_conductor_for_reset(self, vehicle_id: str, driver_id: int, current_date: datetime) -> Optional[PeriodoConductor]:
        pass

    @abstractmethod
    async def update_periodo_conductor_end_date(self, period_id: int, end_date: datetime):
        pass
    
    @abstractmethod
    async def deactivate_current_driver(self, vehicle_id: str, driver_id: int):
        pass

class SpecialRouteRepository(ABC):
    @abstractmethod
    async def get_active_special_programacion_for_vehicle(self, vehicle_id: str, current_date: datetime) -> Optional[ProgramacionEspecialVehiculo]:
        pass

    @abstractmethod
    async def get_nearby_special_route_detail(self, route_id: int, latitude: float, longitude: float) -> Optional[RutaEspecialDetalle]:
        pass
        
    @abstractmethod
    async def get_initial_tiempoglobal(self, route_id: int) -> Optional[float]:
        pass

    @abstractmethod
    async def insert_ruta_especial_control(self, control_data: RutaEspecialControl):
        pass