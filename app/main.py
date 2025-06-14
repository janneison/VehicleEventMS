from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.infrastructure.adapters.api.routes import router as vehicle_event_router
from app.infrastructure.dependencies import kafka_publisher

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Kafka producer
    print("Starting Kafka Producer...")
    await kafka_publisher.start()
    yield
    # Shutdown: Stop Kafka producer
    print("Stopping Kafka Producer...")
    await kafka_publisher.stop()

app = FastAPI(
    title="Vehicle Event Microservice",
    description="Microservice to process vehicle tracking events using hexagonal architecture.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(vehicle_event_router, prefix="/vehicle-events", tags=["Vehicle Events"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Vehicle Event Microservice!"}