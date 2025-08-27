from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.infrastructure.adapters.api.routes import router as vehicle_event_router
from app.infrastructure.dependencies import kafka_publisher

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        print("🚀 Starting Kafka Producer...")
        await kafka_publisher.start()
    except Exception as e:
        print(f"❌ Error starting Kafka producer: {e}")
        raise e

    yield
    # Shutdown
    try:
        print("🛑 Stopping Kafka Producer...")
        await kafka_publisher.stop()
    except Exception as e:
        print(f"❌ Error stopping Kafka producer: {e}")

app = FastAPI(
    title="Vehicle Event Microservice",
    description="Microservice to process vehicle tracking events.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(vehicle_event_router, prefix="/vehicle-events", tags=["Vehicle Events"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Vehicle Event Microservice!"}
