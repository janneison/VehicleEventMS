from aiokafka import AIOKafkaProducer
import json
from app.core.ports.event_publisher import EventPublisher
from app.core.domain.entities import VehicleEvent
from app.infrastructure.config.settings import settings

class KafkaEventPublisher(EventPublisher):
    def __init__(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def publish_processed_event(self, event: VehicleEvent):
        topic = settings.KAFKA_PROCESSED_EVENTS_TOPIC
        # Use model_dump_json to serialize Pydantic model, ensuring datetime is ISO formatted
        message = event.model_dump_json().encode('utf-8')
        await self.producer.send_and_wait(topic, message)
        print(f"Published processed event to {topic}: {message}")