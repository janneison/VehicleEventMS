from app.core.domain.entities import VehicleEvent
from app.core.ports.event_publisher import EventPublisher


class NoOpEventPublisher(EventPublisher):
    async def start(self) -> None:
        print("⚠️ Kafka disabled: no-op start")

    async def stop(self) -> None:
        print("⚠️ Kafka disabled: no-op stop")

    async def publish_processed_event(self, event: VehicleEvent) -> None:
        # Log the event locally instead of publishing to Kafka
        print(f"📤 [NoOpEventPublisher] {event}")
