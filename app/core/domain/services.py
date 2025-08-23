from abc import ABC, abstractmethod
from typing import Optional
from app.core.domain.entities import GeolocationInfo

class GeolocationService(ABC):
    @abstractmethod
    async def get_address_from_coords(self, latitude: float, longitude: float) -> Optional[GeolocationInfo]:
        """Performs reverse geocoding to get address details."""
        pass