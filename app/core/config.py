import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel


# Load environment variables early so the Settings class can read them.
load_dotenv()


class Settings(BaseModel):
    project_name: str = "GreenMap Backend"
    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@localhost/greenmap_db",
    )
    openaq_api_key: str | None = os.getenv("OPENAQ_API_KEY")
    orion_broker_url: str = os.getenv("ORION_BROKER_URL", "http://localhost:1026")
    first_superuser: str = os.getenv("FIRST_SUPERUSER", "admin@example.com")
    first_superuser_password: str = os.getenv("FIRST_SUPERUSER_PASSWORD", "123456")
    static_dir: str = os.getenv("STATIC_DIR", "static")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
