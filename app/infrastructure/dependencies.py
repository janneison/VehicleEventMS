from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E501
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.domain.services import GeolocationService
from app.core.services.vehicle_event_processor_service import (
    VehicleEventProcessorService,
)
from app.infrastructure.adapters.database.repositories import (
    PeriodRepositoryImpl,
    SpecialRouteRepositoryImpl,
    VehicleEventRepositoryImpl,
    VehicleRepositoryImpl,
)
from app.infrastructure.adapters.geolocation.Maps_adapter import (
    PostgresGeolocationAdapter,
)
from app.infrastructure.adapters.messaging.noop_publisher import (  # noqa: E501
    NoOpEventPublisher,
)
from app.infrastructure.config.settings import settings

# ────────────────────────────────────────────────────────────────────────────────
# Database Engine Setup
# ────────────────────────────────────────────────────────────────────────────────

# Ensure DATABASE_URL uses asyncpg (e.g., postgresql+asyncpg://...)
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)

# ────────────────────────────────────────────────────────────────────────────────
# Singletons
# ────────────────────────────────────────────────────────────────────────────────

kafka_publisher = NoOpEventPublisher()

# ────────────────────────────────────────────────────────────────────────────────
# Dependencies
# ────────────────────────────────────────────────────────────────────────────────


async def get_db_session():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session


async def get_geolocation_service(
    db_session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[GeolocationService, None]:
    # Retorna una instancia de PostgresGeolocationAdapter
    # que usa la sesión de base de datos
    yield PostgresGeolocationAdapter(session=db_session)


async def get_vehicle_event_processor_service(
    db_session: AsyncSession = Depends(get_db_session),
    geolocation_svc: GeolocationService = Depends(get_geolocation_service),
) -> AsyncGenerator[VehicleEventProcessorService, None]:
    vehicle_event_repo = VehicleEventRepositoryImpl(db_session)
    vehicle_repo = VehicleRepositoryImpl(db_session)
    period_repo = PeriodRepositoryImpl(db_session)
    special_route_repo = SpecialRouteRepositoryImpl(db_session)

    service = VehicleEventProcessorService(
        vehicle_event_repo=vehicle_event_repo,
        vehicle_repo=vehicle_repo,
        period_repo=period_repo,
        special_route_repo=special_route_repo,
        geolocation_service=geolocation_svc,
        event_publisher=kafka_publisher,
    )

    yield service
