from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Event Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "event_management"
    DATABASE_URL: Optional[str] = None

    # JWT
    SECRET_KEY: str = "de30948c8ae1a6060309dbe6ce26a185b58f282c9cd7adbaac53ded2727a11c4"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis
    REDIS_URL: str = "redis://localhost"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        case_sensitive = True
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # First try to get DATABASE_URL from environment (Render sets this)
        database_url = os.getenv("DATABASE_URL")
        
        if database_url:
            # Convert postgres:// to postgresql:// for SQLAlchemy
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            
            # Add asyncpg driver if not present
            if "postgresql://" in database_url and "+asyncpg" not in database_url:
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
            self.DATABASE_URL = database_url
        elif not self.DATABASE_URL:
            # Fallback to constructing URL from components
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/"
                f"{self.POSTGRES_DB}"
            )

@lru_cache()
def get_settings() -> Settings:
    return Settings()