from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.infrastructure.config.settings import settings
from app.infrastructure.adapters.database.repositories import (
    VehicleEventRepositoryImpl,
    VehicleRepositoryImpl,
    PeriodRepositoryImpl,
    SpecialRouteRepositoryImpl,
)
from app.infrastructure.adapters.geolocation.Maps_adapter import PostgresGeolocationAdapter
from app.infrastructure.adapters.messaging.kafka_publisher import KafkaEventPublisher
from app.core.services.vehicle_event_processor_service import VehicleEventProcessorService
from app.core.domain.services import GeolocationService

# ────────────────────────────────────────────────────────────────────────────────
# Database Engine Setup
# ────────────────────────────────────────────────────────────────────────────────

# Ensure DATABASE_URL uses asyncpg (e.g., postgresql+asyncpg://...)
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)

# ────────────────────────────────────────────────────────────────────────────────
# Singletons
# ────────────────────────────────────────────────────────────────────────────────

kafka_publisher = KafkaEventPublisher()

# ────────────────────────────────────────────────────────────────────────────────
# Dependencies
# ────────────────────────────────────────────────────────────────────────────────

async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_geolocation_service(db_session: AsyncSession = Depends(get_db_session)) -> GeolocationService:
    # Retorna una instancia de PostgresGeolocationAdapter que usa la sesión de DB
    return PostgresGeolocationAdapter(session=db_session)

async def get_vehicle_event_processor_service(
    db_session: AsyncSession = Depends(get_db_session),
    geolocation_svc: GeolocationService = Depends(get_geolocation_service)
) -> VehicleEventProcessorService:
    vehicle_event_repo = VehicleEventRepositoryImpl(db_session)
    vehicle_repo = VehicleRepositoryImpl(db_session)
    period_repo = PeriodRepositoryImpl(db_session)
    special_route_repo = SpecialRouteRepositoryImpl(db_session)

    return VehicleEventProcessorService(
        vehicle_event_repo=vehicle_event_repo,
        vehicle_repo=vehicle_repo,
        period_repo=period_repo,
        special_route_repo=special_route_repo,
        geolocation_service=geolocation_svc, 
        event_publisher=kafka_publisher
    )
