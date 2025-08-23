import math
from datetime import datetime, timedelta, date
from typing import Optional

from app.core.domain.entities import VehicleEvent, Vehicle, EventoDescripcion, GeolocationInfo, \
    PeriodoActivo, PeriodoConductor, ProgramacionEspecialVehiculo, RutaEspecialDetalle, RutaEspecialControl, EventoResumen
from app.core.domain.services import GeolocationService
from app.core.ports.repositories import (
    VehicleEventRepository, VehicleRepository, PeriodRepository, SpecialRouteRepository
)
from app.core.ports.event_publisher import EventPublisher

# Helper functions for calculations (can be moved to a utilities module if many)
def _parse_coord_string(coord_str: str) -> Optional[float]:
    if not coord_str or len(coord_str) < 3:
        return None
    try:
        sign = 1.0 if coord_str[0] in ('N', 'E') else -1.0
        value = float(coord_str[1:])
        return sign * value
    except ValueError:
        return None

def _calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    # This function is complex due to getbearing and getbearing2 in SP.
    # For a simplified version, you can use:
    # math.atan2(math.sin(lon2 - lon1) * math.cos(lat2), math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lon2 - lon1))
    # Then convert radians to degrees and adjust to 0-360 range.
    # Given the SP uses `getbearing` and `getbearing2`, these imply a more specific calculation
    # potentially handling quadrants or special cases. For this example, we'll use a standard one.
    # You might need to implement the exact logic from the original `getbearing` functions.

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    delta_lon = lon2_rad - lon1_rad
    x = math.sin(delta_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - (math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
    
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return int(compass_bearing)

# Simplified haversine distance for geo_distance in SP
def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000 # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c # Distance in meters
    return distance

class VehicleEventProcessorService:
    def __init__(
        self,
        vehicle_event_repo: VehicleEventRepository,
        vehicle_repo: VehicleRepository,
        period_repo: PeriodRepository,
        special_route_repo: SpecialRouteRepository,
        geolocation_service: GeolocationService,
        event_publisher: EventPublisher
    ):
        self.vehicle_event_repo = vehicle_event_repo
        self.vehicle_repo = vehicle_repo
        self.period_repo = period_repo
        self.special_route_repo = special_route_repo
        self.geolocation_service = geolocation_service
        self.event_publisher = event_publisher

    async def process_event(self, event: VehicleEvent) -> str:
        # Simulate time init
        time_init = datetime.now()

        # 1. Get Vehicle Info
        vehicle = await self.vehicle_repo.get_active_vehicle_by_id(event.vehicle_id)
        if not vehicle:
            return f"{event.vehicle_id} INACTIVO"

        result_message = ""

        # 2. Process Lat/Lon (from SP's float8(CASE WHEN substring...) logic)
        event.processed_latitude = _parse_coord_string(event.latitude_raw)
        event.processed_longitude = _parse_coord_string(event.longitude_raw)

        # 3. Determine Event Date
        event.processed_date = event.realtime_date if event.realtime_date else event.keep_alive_date

        # Adjust date for specific modem types and old dates (SP logic)
        if (vehicle.tipo_modem in ['SKYPATROL 8750 MODIFIED', 'MT4000']) and \
           (event.processed_date.date() < (datetime.now() - timedelta(days=1)).date()):
            event.processed_date = datetime.now()

        # 4. Geocoding (getdireccion logic)
        # Prioritize modem-provided address, then use geocoding service
        geolocation_info = None
        if event.address and event.city and event.department:
            geolocation_info = GeolocationInfo(address=event.address, city=event.city, department=event.department)
        elif event.processed_latitude and event.processed_longitude:
            geolocation_info = await self.geolocation_service.get_address_from_coords(
                event.processed_latitude, event.processed_longitude
            )
            # If geocoding service returns nothing, and initial values were provided by modem, use them.
            # This is to replicate the SP's "if direccion_ is null OR direccion_.direccion IS NULL..." part
            if not geolocation_info or not geolocation_info.is_valid():
                if event.address and event.city and event.department:
                    geolocation_info = GeolocationInfo(address=event.address, city=event.city, department=event.department)
                else: # Default to "No Disponible" if no info at all
                    geolocation_info = GeolocationInfo(address='No Disponible', city='No Disponible', department='No Disponible')

        event.geolocation = geolocation_info

        # Insert into EjesViales if address not found (SP logic)
        if geolocation_info and not geolocation_info.is_valid():
             # The SP tries to insert into EjesViales if address is not available or 'No Disponible'
             # It uses SP_ASCII, which implies character normalization.
             # This part might need to be adjusted based on the `getdireccion` function's actual behavior
             # and if `EjesViales` table is meant for caching geocoding results.
             if event.address and event.city and event.department and event.processed_latitude and event.processed_longitude:
                await self.vehicle_event_repo.insert_ejes_viales(
                    event.address, event.city, event.processed_latitude, event.processed_longitude, event.department
                )


        # 5. Apply time tolerance based on 'Procesos'
        tolerancia_minutes = await self.vehicle_repo.get_vehicle_tolerancia_tiempo(vehicle.contratista)
        if tolerancia_minutes:
            event.processed_date += timedelta(minutes=tolerancia_minutes)

        # 6. Process Speed
        if not event.speed or event.speed == 0:
            event.processed_speed = 0.0 # Default if empty or zero
        elif event.speed > 180.0: # Cap speed
            event.processed_speed = vehicle.velocidad if vehicle.velocidad is not None else 0.0
        else:
            event.processed_speed = event.speed

        # 7. Main event processing logic (tipo = 0 or tipo = 300)
        if event.event_type in (0, 300):
            if event.event_code != 1: # Not a KEEP ALIVE event
                result_message += f"Trama recibida del modem: {event.ip_address}:{event.port}@\n"
                result_message += f"ID Vehiculo: {event.vehicle_id}@\n"
                result_message += f"User Specified Number: {event.event_code}@\n"

                # Handle missing GPS data (SP's "if(lat_ is null or d_lat = 0.0)...")
                if event.processed_latitude is None or event.processed_latitude == 0.0:
                    # Replicate last known good GPS from 'vehiculos' table
                    event.latitude_raw = vehicle.latitud
                    event.longitude_raw = vehicle.longitud
                    event.geolocation = GeolocationInfo(
                        address=vehicle.direccion,
                        city=vehicle.municipio,
                        department=vehicle.departamento
                    )
                    event.processed_speed = vehicle.velocidad if vehicle.velocidad is not None else 0.0
                    result_message += "Se ha actualizado la info GPS a partir de la ultima info valida@\n"
                
                # Check if event is static
                event_desc = await self.vehicle_event_repo.find_evento_descripcion(event.event_code)
                if event_desc and event_desc.estatico == 'S' or event.processed_speed < 0.0:
                    event.is_static_event = True
                    event.processed_speed = 0.0

                result_message += f"Latitud: {event.latitude_raw}@\n"
                result_message += f"Longitud: {event.longitude_raw}@\n"
                result_message += f"Direccion: {event.geolocation.address}@\n"
                result_message += f"Municipio: {event.geolocation.city}@\n"
                result_message += f"Departamento: {event.geolocation.department}@\n"
                result_message += f"Velocidad: {event.processed_speed}@\n"

                # Handle ignition events (ENCENDIDO/APAGADO - 5/6)
                reset_periodo_conductor = False
                if event.event_code in (5, 6):
                    event.ignition_status = str(event.event_code)
                    reset_periodo_conductor = True
                elif event.signal_status is not None and event.realtime_date is not None:
                    if event.vehicle_on:
                        event.ignition_status = '5' # Encendido
                    else:
                        event.ignition_status = '6' # Apagado
                
                # Determine current driver
                event.current_driver_id = vehicle.idconductor_actual if vehicle.idconductor_actual else vehicle.idconductor

                # Manage active periods (periodosactivo)
                active_period = await self.period_repo.get_active_periodo(vehicle.ultperiodo)

                if (event.vehicle_on or event.event_code == 5) and (not active_period or active_period.fechahasta is not None):
                    # Start a new period
                    event.period_id = await self.period_repo.create_periodo_activo(
                        event.vehicle_id, event.processed_date, event.current_driver_id
                    )
                    vehicle.ultperiodo = event.period_id
                elif (not event.vehicle_on or event.event_code == 6) and (active_period and active_period.fechahasta is None):
                    # End current period
                    await self.period_repo.update_periodo_activo_end_date(vehicle.ultperiodo, event.processed_date)
                
                # Driver Period Reset Logic (periodosconductores)
                if reset_periodo_conductor:
                    last_driver_period = await self.period_repo.get_last_periodo_conductor_for_reset(
                        event.vehicle_id, event.current_driver_id, event.processed_date
                    )
                    if last_driver_period and (event.processed_date - last_driver_period.fechahasta < timedelta(minutes=1)) and event.event_code == 5:
                        await self.period_repo.update_periodo_conductor_end_date(last_driver_period.idperiodo, None) # Set fechahasta to NULL
                    else:
                        if last_driver_period and last_driver_period.fechahasta is None:
                            await self.period_repo.update_periodo_conductor_end_date(last_driver_period.idperiodo, event.processed_date)
                        
                        # Logic to set idconductor_actual to NULL
                        # This part of the SP is conditional: "IF (COALESCE((SELECT count(*) FROM progvehiculos WHERE idvehiculo = idveh AND activa = 'S'), 0) <= 0)"
                        # You'd need to add a method to `ProgramacionVehicularRepository` to check active programs.
                        # For now, let's just assume the direct update if `idconductor_actual` is set.
                        # if (await self.programacion_vehicular_repo.count_active_programaciones(event.vehicle_id)) <= 0: # Requires a new repo method
                        #     await self.vehicle_repo.deactivate_current_driver(event.vehicle_id, event.current_driver_id)
                        pass # Placeholder for `deactivate_current_driver` logic

                # Insert into EVENTS table
                event.event_db_id = await self.vehicle_event_repo.save_event(event)
                result_message += f"Codigo Evento: {event.event_db_id}@\n"

                # Update eventos_resumen (if not vehicle 0560025196)
                if event.vehicle_id != '0560025196':
                    event_summary = await self.vehicle_event_repo.find_eventos_resumen(
                        event.vehicle_id, event.event_code, event.processed_date.date(), event.processed_date.hour
                    )
                    if event_summary:
                        await self.vehicle_event_repo.update_eventos_resumen(
                            event.vehicle_id, event.event_code, event.processed_date.date(), event.processed_date.hour, event_summary.valor + 1
                        )
                    else:
                        await self.vehicle_event_repo.insert_eventos_resumen(
                            event.vehicle_id, event.event_code, 1, event.processed_date.date(), event.processed_date.hour
                        )
                
                # Update VEHICULOS table
                if event.processed_latitude is None or event.processed_longitude is None or event.processed_latitude == 0.0 or event.processed_longitude == 0.0:
                    result_message += "El movil no posee informacion de GPS@\n"
                    # Update without GPS coords
                    vehicle.ultimaactualizacion = event.processed_date
                    vehicle.ultimoevento = event.event_code
                    vehicle.ultperiodo = event.period_id
                    vehicle.enc_apa = event.ignition_status
                    vehicle.estadosenal = event.signal_status
                    vehicle.encendido = event.vehicle_on
                    await self.vehicle_repo.update_vehicle_status(vehicle)
                else:
                    # Calculate bearing
                    ult_lat = _parse_coord_string(vehicle.latitud)
                    ult_lon = _parse_coord_string(vehicle.longitud)
                    
                    rumbo = None
                    rumbo_lt = 0 # Default as in SP
                    if ult_lat is not None and ult_lat != 0.0 and ult_lon is not None:
                        rumbo = _calculate_bearing(ult_lat, ult_lon, event.processed_latitude, event.processed_longitude)
                        rumbo_lt = rumbo # SP uses getbearing2 which might be slightly different or for a specific visualization. Assume same for now.
                        
                    # Update with GPS coords
                    vehicle.latitud = event.latitude_raw
                    vehicle.longitud = event.longitude_raw
                    vehicle.municipio = event.geolocation.city
                    vehicle.departamento = event.geolocation.department
                    vehicle.ultimaactualizacion = event.processed_date
                    vehicle.direccion = event.geolocation.address
                    vehicle.velocidad = event.processed_speed
                    vehicle.ultimoevento = event.event_code
                    vehicle.rumbo = rumbo
                    vehicle.rumbo_linea_tiempo = rumbo_lt
                    vehicle.indexgeoc = event.geofence_index
                    vehicle.ultperiodo = event.period_id
                    vehicle.enc_apa = event.ignition_status
                    vehicle.estadosenal = event.signal_status
                    vehicle.encendido = event.vehicle_on
                    vehicle.indexevento = event.event_db_id
                    await self.vehicle_repo.update_vehicle_status(vehicle)

                    # Special Transport Logic
                    prog_especial = await self.special_route_repo.get_active_special_programacion_for_vehicle(
                        event.vehicle_id, datetime.now() # SP uses localtimestamp for this check
                    )

                    if prog_especial:
                        detalle_punto = await self.special_route_repo.get_nearby_special_route_detail(
                            prog_especial.idruta, event.processed_latitude, event.processed_longitude
                        )
                        if detalle_punto:
                            # Calculate time (assuming tiempoglobal in SP is time in minutes from start)
                            # SP uses localtimestamp - progespecial_.fechasalida, then divide by 60
                            current_time_minutes = (datetime.now() - prog_especial.fechasalida).total_seconds() / 60.0
                            
                            initial_offset = await self.special_route_repo.get_initial_tiempoglobal(prog_especial.idruta)
                            if initial_offset is None:
                                initial_offset = 0.0 # Default if not found
                            
                            val_df = detalle_punto.tiempoglobal
                            dif_int = current_time_minutes - val_df + initial_offset

                            # Insert into rutas_especiales_control
                            await self.special_route_repo.insert_ruta_especial_control(
                                RutaEspecialControl(
                                    idprogramacion=prog_especial.idprogramacion,
                                    idpunto=detalle_punto.idpunto,
                                    fecha=datetime.now(),
                                    tiempoint=current_time_minutes,
                                    tiempoglobal=current_time_minutes, # SP uses tint for both
                                    diferenciaint=dif_int,
                                    diferenciaglobal=dif_int, # SP uses difint for both
                                    orden=detalle_punto.orden
                                )
                            )

                # Update Recursos table
                if vehicle.recurso and vehicle.contratista:
                    await self.vehicle_repo.update_resource_gps_status(
                        vehicle.recurso, vehicle.contratista, event.processed_date, True if event.processed_latitude else False
                    )

                # Odometer
                if event.odometer is not None:
                    await self.vehicle_event_repo.save_odometer(event.vehicle_id, event.odometer, event.processed_date)
                    result_message += f"ODOMETRO: {event.odometer}@\n"

                await self.event_publisher.publish_processed_event(event)

            else: # Event Type 1 (KEEP ALIVE)
                result_message += f"Vehiculo {event.vehicle_id} Vivo!!!@\n"
                vehicle.ultimaactualizacion = event.processed_date
                vehicle.estadosenal = event.signal_status
                vehicle.encendido = event.vehicle_on
                vehicle.indexevento = event.event_db_id # Although SP sets idevt only on save_event, here it might be redundant for keep_alive
                await self.vehicle_repo.update_vehicle_status(vehicle)

                await self.event_publisher.publish_processed_event(event) # Still publish keep-alive

        elif event.event_type == 128: # OTA Current Position
            if event.processed_latitude is not None and event.processed_latitude != 0.0:
                result_message += "Actualizando Posicion por OTA@\n"
                result_message += f"Latitud: {event.latitude_raw}@\n"
                result_message += f"Longitud: {event.longitude_raw}@\n"
                result_message += f"Direccion: {event.geolocation.address}@\n"
                result_message += f"Municipio: {event.geolocation.city}@\n"
                result_message += f"Departamento: {event.geolocation.department}@\n"

                vehicle.latitud = event.latitude_raw
                vehicle.longitud = event.longitude_raw
                vehicle.municipio = event.geolocation.city
                vehicle.departamento = event.geolocation.department
                vehicle.ultimaactualizacion = event.processed_date
                vehicle.direccion = event.geolocation.address
                vehicle.indexgeoc = event.geofence_index
                vehicle.estadosenal = event.signal_status
                vehicle.encendido = event.vehicle_on
                vehicle.indexevento = event.event_db_id # Similar to above, potentially redundant here
                await self.vehicle_repo.update_vehicle_status(vehicle)

                await self.event_publisher.publish_processed_event(event)

        # Calculate and log time taken
        time_taken = (datetime.now() - time_init).total_seconds()
        print(f"TIME INSERT_EVENT {event.vehicle_id}: ({time_taken})")

        return result_message.strip()