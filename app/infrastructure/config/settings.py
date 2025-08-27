from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_PROCESSED_EVENTS_TOPIC: str = "vehicle_events_processed"
    KAFKA_RAW_EVENTS_TOPIC: str = "raw_vehicle_events"  # For consumer
    Maps_API_KEY: str  # Or another geocoding service API key
    API_KEY: str  # For basic API security

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

if not settings.DATABASE_URL.startswith("postgresql+asyncpg://"):
    raise ValueError("DATABASE_URL must start with 'postgresql+asyncpg://'")
