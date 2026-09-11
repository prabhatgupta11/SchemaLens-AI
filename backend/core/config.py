import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SchemaLens API"
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./metadata.db")
    DUCKDB_PATH: str = os.getenv("DUCKDB_PATH", "./analytics.duckdb")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
