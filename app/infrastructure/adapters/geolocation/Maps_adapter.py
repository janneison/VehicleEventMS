"""Geolocation adapter backed by PostgreSQL.

This version adds a small in-memory cache to avoid hitting the database for
coordinates that were recently resolved.  Many vehicles report events from the
same location consecutively and the reverse geocoding query is expensive.  By
keeping a simple LRU cache we can dramatically reduce average response times
for those repeated lookups.
"""

from collections import OrderedDict
from typing import Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.entities import GeolocationInfo
from app.core.domain.services import GeolocationService

CacheType = OrderedDict[Tuple[float, float], GeolocationInfo]


class PostgresGeolocationAdapter(GeolocationService):
    """Geolocation service using a PostgreSQL stored procedure.

    Parameters
    ----------
    session:
        Async SQLAlchemy session used to execute the ``getdireccion`` stored
        procedure.
    cache_size:
        Maximum number of coordinates stored in the local cache.  When the
        cache is full the least recently used entry is discarded.
    """

    def __init__(self, session: AsyncSession, cache_size: int = 128):
        self.session = session
        self.cache_size = cache_size
        # Simple LRU cache for reverse geocoding lookups
        self._cache: CacheType = OrderedDict()

    async def get_address_from_coords(
        self, latitude: float, longitude: float
    ) -> Optional[GeolocationInfo]:
        """Resolve coordinates into an address using ``getdireccion``.

        A simple LRU cache is used so that consecutive requests for the same
        coordinates return immediately without querying the database again.
        Coordinates are rounded to 5 decimal places before caching to avoid
        storing excessive keys for minimal variations.
        """

        key = (round(latitude, 5), round(longitude, 5))
        cached = self._cache.get(key)
        if cached is not None:
            # Move to the end to mark as recently used and return cached value
            self._cache.move_to_end(key)
            return cached

        try:
            query = text("SELECT * FROM getdireccion(:lat, :lon)")
            result = await self.session.execute(
                query, {"lat": latitude, "lon": longitude}
            )
            row = result.fetchone()

            if row:
                address = row[0] if len(row) > 0 else None
                city = row[1] if len(row) > 1 else None
                department = row[2] if len(row) > 2 else None

                if address and address.lower() == "no disponible":
                    address = None
                if city and city.lower() == "no disponible":
                    city = None
                if department and department.lower() == "no disponible":
                    department = None

                info = GeolocationInfo(
                    address=address, city=city, department=department
                )
            else:
                info = GeolocationInfo(
                    address="No Disponible",
                    city="No Disponible",
                    department="No Disponible",
                )

        except Exception as exc:  # pragma: no cover - log and return default
            print(f"Error calling getdireccion in PostgreSQL: {exc}")
            info = GeolocationInfo(
                address="No Disponible",
                city="No Disponible",
                department="No Disponible",
            )

        # Maintain LRU cache
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self.cache_size:
                self._cache.popitem(last=False)
            self._cache[key] = info

        return info
