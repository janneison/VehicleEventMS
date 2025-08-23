from abc import ABC, abstractmethod
from app.core.domain.entities import VehicleEvent

class EventPublisher(ABC):
    @abstractmethod
    async def publish_processed_event(self, event: VehicleEvent):
        pass