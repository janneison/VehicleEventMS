from aiokafka import AIOKafkaProducer
import json
import asyncio
from app.core.ports.event_publisher import EventPublisher
from app.core.domain.entities import VehicleEvent
from app.infrastructure.config.settings import settings
import pydantic
class KafkaEventPublisher(EventPublisher):
    def __init__(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
        )

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def publish_processed_event(self, event: VehicleEvent):
        topic = settings.KAFKA_PROCESSED_EVENTS_TOPIC

        # Usa model_dump_json para Pydantic v2, y json() para v1
        if int(pydantic.VERSION.split(".")[0]) >= 2:
            message = event.model_dump_json().encode("utf-8")
        else:
            message = event.json().encode("utf-8")

        try:
            await self.producer.send_and_wait(topic, message)
            print(f"✅ Published processed event to {topic}: {message}")
        except Exception as e:
            print(f"❌ Failed to publish event: {e}")
