# flake8: noqa
import re
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.domain.entities import (
    EventoDescripcion,
    EventoResumen,
    GeolocationInfo,
    PeriodoActivo,
    PeriodoConductor,
    Proceso,
    ProgramacionEspecialVehiculo,
    PuntoControlEspecial,
    RutaEspecialControl,
    RutaEspecialDetalle,
    Vehicle,
    VehicleEvent,
)
from app.core.ports.repositories import (
    PeriodRepository,
    SpecialRouteRepository,
    VehicleEventRepository,
    VehicleRepository,
)
from app.infrastructure.adapters.database.models import (
    EjesViales,
    Eventos,
    EventosDesc,
    EventosResumen,
    Odométros,
    PeriodosActivo,
    PeriodosConductores,
    Procesos,
    ProgEspecialesVehiculos,
    ProgramacionVehicularModel,
    PuntosControl,
    Recursos,
    RutasEspecialesControl,
    RutasEspecialesDetalles,
    Vehiculos,
)


# Helper function for converting ORM models to domain entities
def _to_vehicle_entity(model: Vehiculos) -> Optional[Vehicle]:
    if not model:
        return None
    return Vehicle(
        idvehiculo=model.idvehiculo,
        estado=model.estado,
        tipo_modem=model.tipo_modem,
        velocidad=model.velocidad,
        direccion=model.direccion,
        latitud=model.latitud,
        longitud=model.longitud,
        municipio=model.municipio,
        departamento=model.departamento,
        ultperiodo=model.ultperiodo,
        enc_apa=model.enc_apa,
        idconductor=model.idconductor,
        idconductor_actual=model.idconductor_actual,
        ultimaactualizacion=model.ultimaactualizacion,
        ultimoevento=model.ultimoevento,
        rumbo=model.rumbo,
        rumbo_linea_tiempo=model.rumbo_linea_tiempo,
        indexgeoc=model.indexgeoc,
        estadosenal=model.estadosenal,
        encendido=model.encendido,
        indexevento=model.indexevento,
        contratista=model.contratista,
        recurso=model.recurso,
    )


def _to_evento_descripcion_entity(model: EventosDesc) -> Optional[EventoDescripcion]:
    if not model:
        return None
    return EventoDescripcion(evento=model.evento, estatico=model.estatico)


def _to_periodo_activo_entity(model: PeriodosActivo) -> Optional[PeriodoActivo]:
    if not model:
        return None
    return PeriodoActivo(
        idperiodo=model.idperiodo,
        idvehiculo=model.idvehiculo,
        fechadesde=model.fechadesde,
        fechahasta=model.fechahasta,
        idconductor=model.idconductor,
    )


def _to_periodo_conductor_entity(
    model: PeriodosConductores,
) -> Optional[PeriodoConductor]:
    if not model:
        return None
    return PeriodoConductor(
        idperiodo=model.idperiodo,
        idvehiculo=model.idvehiculo,
        idconductor=model.idconductor,
        fechadesde=model.fechadesde,
        fechahasta=model.fechahasta,
    )


def _to_programacion_especial_vehiculo_entity(
    model: ProgEspecialesVehiculos,
) -> Optional[ProgramacionEspecialVehiculo]:
    if not model:
        return None
    return ProgramacionEspecialVehiculo(
        idprogramacion=model.idprogramacion,
        idvehiculo=model.idvehiculo,
        fechasalida=model.fechasalida,
        finalizado=model.finalizado,
        cancelada=model.cancelada,
        activa=model.activa,
        idruta=model.idruta,
    )


def _to_ruta_especial_detalle_entity(
    model: RutasEspecialesDetalles,
) -> Optional[RutaEspecialDetalle]:
    if not model:
        return None
    return RutaEspecialDetalle(
        idruta=model.idruta,
        idpunto=model.idpunto,
        orden=model.orden,
        tiempoglobal=model.tiempoglobal,
    )


def _to_evento_resumen_entity(model: EventosResumen) -> Optional[EventoResumen]:
    if not model:
        return None
    return EventoResumen(
        idvehiculo=model.idvehiculo,
        idevento=model.idevento,
        valor=model.valor,
        fecha=model.fecha,
        hora=model.hora,
    )


class VehicleEventRepositoryImpl(VehicleEventRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_event(self, event: VehicleEvent) -> int:
        new_event = Eventos(
            idvehiculo=event.vehicle_id,
            evento=str(event.event_code),
            fecha=event.processed_date,
            velocidad=(
                str(event.processed_speed)
                if event.processed_speed is not None
                else None
            ),
            direccion=event.geolocation.address if event.geolocation else None,
            latitud=event.latitude_raw,
            longitud=event.longitude_raw,
            xpos=0,  # SP sets to 0
            ypos=0,  # SP sets to 0
            municipio=event.geolocation.city if event.geolocation else None,
            departamento=event.geolocation.department if event.geolocation else None,
            indicegeocerca=event.geofence_index,
            idconductor=event.current_driver_id,
        )
        self.session.add(new_event)
        await self.session.flush()  # Flushes to get the idevento (ID)
        return new_event.idevento

    async def save_odometer(self, vehicle_id: str, value: float, date: datetime):
        new_odometer = Odométros(idvehiculo=vehicle_id, valor=value, fecha=date)
        self.session.add(new_odometer)
        await self.session.flush()

    async def get_last_event_with_gps(self, vehicle_id: str) -> Optional[VehicleEvent]:
        # SP query is complex here. It implies fetching the last valid GPS event
        # This implementation fetches the last event for the vehicle and then relies on
        # the service logic to use its GPS info if available.
        stmt = (
            select(Eventos)
            .where(
                Eventos.idvehiculo == vehicle_id,
                Eventos.latitud != "null",  # Assuming 'null' as string for invalid GPS
                Eventos.longitud != "null",
                Eventos.latitud
                != "N",  # Handle malformed string like 'N' which can become 0.0
                Eventos.longitud != "W",
                Eventos.fecha
                > datetime.now() - timedelta(days=2),  # SP uses 'now() - 2 days'
            )
            .order_by(Eventos.idevento.desc())
            .limit(1)
        )  # Order by idevento_ desc in SP

        result = await self.session.execute(stmt)
        event_model = result.scalar_one_or_none()
        if event_model:
            return VehicleEvent(
                event_type=0,  # Placeholder
                vehicle_id=event_model.idvehiculo,
                event_code=(
                    int(event_model.evento) if event_model.evento is not None else 0
                ),
                system_date_str="",  # Not available
                speed=(
                    float(event_model.velocidad)
                    if event_model.velocidad is not None
                    else 0.0
                ),
                latitude_raw=event_model.latitud,
                longitude_raw=event_model.longitud,
                ip_address="",
                port=0,  # Not available
                geofence_index=event_model.indicegeocerca,
                vehicle_on=False,
                signal_status="",
                realtime_date=event_model.fecha,
                address=event_model.direccion,
                city=event_model.municipio,
                department=event_model.departamento,
                keep_alive_date=event_model.fecha,  # Using event_model.fecha as fallback
            )
        return None

    async def insert_ejes_viales(
        self,
        address: str,
        city: str,
        latitude: float,
        longitude: float,
        department: str,
    ):
        # The SP's EjesViales insert references 'Municipios' table for city/department.
        # This requires `Municipios` model and potentially `SP_ASCII` function in SQL.
        # For simplicity, this will directly insert if needed, assuming the city/department are valid.
        # A more robust solution might check if the entry already exists or validate city/department.
        new_entry = EjesViales(
            direccion=address,
            municipio=city,
            latitud=latitude,
            longitud=longitude,
            dirnoform=address,
            the_geom=func.ST_GeomFromText(f"POINT({longitude} {latitude})", 4326),
            flat_geom=func.ST_Transform(
                func.ST_GeomFromText(f"POINT({longitude} {latitude})", 4326), 21892
            ),
            xpos=0,
            ypos=0,
        )
        self.session.add(new_entry)
        await self.session.flush()

    async def find_evento_descripcion(
        self, event_code: int
    ) -> Optional[EventoDescripcion]:
        stmt = select(EventosDesc).where(
            EventosDesc.evento == str(event_code)
        )  # event is text in DB
        result = await self.session.execute(stmt)
        return _to_evento_descripcion_entity(result.scalar_one_or_none())

    async def find_eventos_resumen(
        self, vehicle_id: str, event_code: int, date: date, hour: int
    ) -> Optional[EventoResumen]:
        stmt = select(EventosResumen).where(
            EventosResumen.idvehiculo == vehicle_id,
            EventosResumen.idevento == event_code,
            EventosResumen.fecha == date,
            EventosResumen.hora == hour,
        )
        result = await self.session.execute(stmt)
        return _to_evento_resumen_entity(result.scalar_one_or_none())

    async def update_eventos_resumen(
        self, vehicle_id: str, event_code: int, date: date, hour: int, value: int
    ):
        stmt = select(EventosResumen).where(
            EventosResumen.idvehiculo == vehicle_id,
            EventosResumen.idevento == event_code,
            EventosResumen.fecha == date,
            EventosResumen.hora == hour,
        )
        result = await self.session.execute(stmt)
        summary = result.scalar_one_or_none()
        if summary:
            summary.valor = value
            await self.session.flush()

    async def insert_eventos_resumen(
        self, vehicle_id: str, event_code: int, value: int, date: date, hour: int
    ):
        new_summary = EventosResumen(
            idvehiculo=vehicle_id,
            idevento=event_code,
            valor=value,
            fecha=date,
            hora=hour,
        )
        self.session.add(new_summary)
        await self.session.flush()


class VehicleRepositoryImpl(VehicleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_vehicle_by_id(self, vehicle_id: str) -> Optional[Vehicle]:
        stmt = select(Vehiculos).where(
            Vehiculos.idvehiculo == vehicle_id, Vehiculos.estado == "Y"
        )
        result = await self.session.execute(stmt)
        return _to_vehicle_entity(result.scalar_one_or_none())

    async def update_vehicle_status(self, vehicle: Vehicle):
        stmt = select(Vehiculos).where(Vehiculos.idvehiculo == vehicle.idvehiculo)
        result = await self.session.execute(stmt)
        vehicle_orm = result.scalar_one_or_none()
        if vehicle_orm:
            # Update all fields that can be changed by the SP
            vehicle_orm.latitud = vehicle.latitud
            vehicle_orm.longitud = vehicle.longitud
            vehicle_orm.municipio = vehicle.municipio
            vehicle_orm.departamento = vehicle.departamento
            vehicle_orm.ultimaactualizacion = vehicle.ultimaactualizacion
            vehicle_orm.direccion = vehicle.direccion
            vehicle_orm.velocidad = vehicle.velocidad
            vehicle_orm.ultimoevento = vehicle.ultimoevento
            vehicle_orm.rumbo = vehicle.rumbo
            vehicle_orm.rumbo_linea_tiempo = vehicle.rumbo_linea_tiempo
            vehicle_orm.indexgeoc = vehicle.indexgeoc
            vehicle_orm.ultperiodo = vehicle.ultperiodo
            vehicle_orm.enc_apa = vehicle.enc_apa
            vehicle_orm.estadosenal = vehicle.estadosenal
            vehicle_orm.encendido = vehicle.encendido
            vehicle_orm.indexevento = vehicle.indexevento
            vehicle_orm.idconductor_actual = (
                vehicle.idconductor_actual
            )  # Can be set to NULL by SP logic

            await self.session.flush()
        else:
            # This scenario (vehicle not found but exists in SP 'if(found)') shouldn't happen if `get_active_vehicle_by_id`
            # is called first and returns a vehicle. If it can happen, handle accordingly.
            pass

    async def get_vehicle_tolerancia_tiempo(self, vehicle_contratista: str) -> int:
        # This part of the SP uses regex matches against `contratistas` column.
        # This is hard to replicate efficiently purely in SQLAlchemy.
        # A workaround is to fetch all `Procesos` and then filter in Python, or
        # use a text-based search (ILIKE) if exact match is sufficient, or
        # integrate a proper regex engine if PostgreSQL `regexp_matches` is critical.
        # For this example, assuming 'contratistas' can be matched directly or contains a single contractor string.
        # Or, if 'contratistas' is a comma-separated list, iterate.

        # Example of a simplified regex matching for direct string comparison:
        stmt = (
            select(Procesos)
            .where(
                Procesos.contratistas.ilike(f"%{vehicle_contratista}%"),
                Procesos.toleranciatiempo != 0,
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        proceso = result.scalar_one_or_none()
        return proceso.toleranciatiempo if proceso else 0

    async def update_resource_gps_status(
        self, recurso_id: str, contratista_id: str, event_date: datetime, gps_ok: bool
    ):
        stmt = select(Recursos).where(
            Recursos.recurso == recurso_id, Recursos.contratista == contratista_id
        )
        result = await self.session.execute(stmt)
        recurso_orm = result.scalar_one_or_none()
        if recurso_orm:
            recurso_orm.fechagps = event_date
            recurso_orm.estadogps = (
                "OK" if gps_ok else "NOTOK"
            )  # SP uses 'okgps' variable
            await self.session.flush()


class PeriodRepositoryImpl(PeriodRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_periodo(self, period_id: int) -> Optional[PeriodoActivo]:
        stmt = select(PeriodosActivo).where(PeriodosActivo.idperiodo == period_id)
        result = await self.session.execute(stmt)
        return _to_periodo_activo_entity(result.scalar_one_or_none())

    async def create_periodo_activo(
        self, vehicle_id: str, start_date: datetime, driver_id: Optional[int]
    ) -> int:
        new_periodo = PeriodosActivo(
            idvehiculo=vehicle_id, fechadesde=start_date, idconductor=driver_id
        )
        self.session.add(new_periodo)
        await self.session.flush()
        return new_periodo.idperiodo

    async def update_periodo_activo_end_date(self, period_id: int, end_date: datetime):
        stmt = select(PeriodosActivo).where(PeriodosActivo.idperiodo == period_id)
        result = await self.session.execute(stmt)
        periodo_orm = result.scalar_one_or_none()
        if periodo_orm:
            periodo_orm.fechahasta = end_date
            await self.session.flush()

    async def get_last_periodo_conductor_for_reset(
        self, vehicle_id: str, driver_id: int, current_date: datetime
    ) -> Optional[PeriodoConductor]:
        # SP: WHERE fecha_-fechahasta < '1 minutes'::INTERVAL AND idvehiculo=idveh AND idconductor=idconductor_;
        # This implies `fecha_` is the current event's processed_date.
        # It's looking for a period that ended very recently.
        # The SP code here is a bit ambiguous as `fecha_` is an input and `fechahasta` is a column.
        # Assuming it means current_date - fechahasta < 1 minute.
        stmt = (
            select(PeriodosConductores)
            .where(
                PeriodosConductores.idvehiculo == vehicle_id,
                PeriodosConductores.idconductor == driver_id,
            )
            .order_by(PeriodosConductores.fechadesde.desc())
            .limit(1)
        )  # Get the last one

        result = await self.session.execute(stmt)
        last_period = _to_periodo_conductor_entity(result.scalar_one_or_none())

        if last_period and last_period.fechahasta:
            if (current_date - last_period.fechahasta) < timedelta(minutes=1):
                return last_period
        elif (
            last_period and last_period.fechahasta is None
        ):  # If an active period exists
            return last_period
        return None

    async def update_periodo_conductor_end_date(
        self, period_id: int, end_date: Optional[datetime]
    ):
        stmt = select(PeriodosConductores).where(
            PeriodosConductores.idperiodo == period_id
        )
        result = await self.session.execute(stmt)
        periodo_orm = result.scalar_one_or_none()
        if periodo_orm:
            periodo_orm.fechahasta = end_date
            await self.session.flush()

    async def deactivate_current_driver(self, vehicle_id: str, driver_id: int):
        stmt = select(Vehiculos).where(
            Vehiculos.idvehiculo == vehicle_id,
            Vehiculos.idconductor_actual == driver_id,
        )
        result = await self.session.execute(stmt)
        vehicle_orm = result.scalar_one_or_none()
        if vehicle_orm:
            vehicle_orm.idconductor_actual = None
            await self.session.flush()


class SpecialRouteRepositoryImpl(SpecialRouteRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_special_programacion_for_vehicle(
        self, vehicle_id: str, current_date: datetime
    ) -> Optional[ProgramacionEspecialVehiculo]:
        stmt = (
            select(ProgEspecialesVehiculos)
            .where(
                ProgEspecialesVehiculos.idvehiculo == vehicle_id,
                func.date(ProgEspecialesVehiculos.fechasalida) == current_date.date(),
                ProgEspecialesVehiculos.finalizado == "N",
                ProgEspecialesVehiculos.cancelada == "N",
                ProgEspecialesVehiculos.activa == "S",
            )
            .order_by(ProgEspecialesVehiculos.fechasalida.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return _to_programacion_especial_vehiculo_entity(result.scalar_one_or_none())

    async def get_nearby_special_route_detail(
        self, route_id: int, latitude: float, longitude: float
    ) -> Optional[RutaEspecialDetalle]:
        # This replicates the SP's complex join with `PuntosControl` and `geodistance`.
        # Requires PostGIS and `geoalchemy2`.
        # `geodistance` in SP likely refers to ST_Distance.

        current_point = func.ST_GeomFromText(f"POINT({longitude} {latitude})", 4326)

        stmt = (
            select(RutasEspecialesDetalles)
            .join(
                PuntosControl, RutasEspecialesDetalles.idpunto == PuntosControl.idpunto
            )
            .outerjoin(
                RutasEspecialesControl,
                and_(
                    RutasEspecialesControl.idpunto == RutasEspecialesDetalles.idpunto,
                    RutasEspecialesControl.idprogramacion
                    == ProgEspecialesVehiculos.idprogramacion,  # This join needs to be careful
                ),
            )
            .where(
                RutasEspecialesDetalles.idruta == route_id,
                func.ST_Distance(
                    func.ST_Transform(
                        current_point, 2163
                    ),  # Transform to a projected CRS for distance in meters
                    func.ST_Transform(
                        func.ST_GeomFromText(
                            text(
                                "'POINT(' || puntoscontrol.longitud || ' ' || "
                                "puntoscontrol.latitud || ')'"
                            ),
                            4326,
                        ),
                        2163,
                    ),
                )
                <= PuntosControl.radio,
                RutasEspecialesControl.idpunto.is_(None),  # rc.idpunto IS NULL
            )
            .limit(1)
        )

        # NOTE: The original SP filters out existing points from
        # `rutas_especiales_control` for the current program.
        # For simplicity, this version filters on `idpunto IS NULL`.

        result = await self.session.execute(stmt)
        return _to_ruta_especial_detalle_entity(result.scalar_one_or_none())

    async def get_initial_tiempoglobal(self, route_id: int) -> Optional[float]:
        # SP query:
        # SELECT tiempoglobal FROM rutas_especiales_detalles
        # WHERE idruta = progespecial_.idruta ORDER BY orden LIMIT 1;
        stmt = (
            select(RutasEspecialesDetalles.tiempoglobal)
            .where(RutasEspecialesDetalles.idruta == route_id)
            .order_by(RutasEspecialesDetalles.orden)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def insert_ruta_especial_control(
        self,
        control_data: RutaEspecialControl,
    ):
        new_control = RutasEspecialesControl(
            idprogramacion=control_data.idprogramacion,
            idpunto=control_data.idpunto,
            fecha=control_data.fecha,
            tiempoint=control_data.tiempoint,
            tiempoglobal=control_data.tiempoglobal,
            diferenciaint=control_data.diferenciaint,
            diferenciaglobal=control_data.diferenciaglobal,
            orden=control_data.orden,
        )
        self.session.add(new_control)
        await self.session.flush()
