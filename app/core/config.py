# Copyright 2025 HouHackathon-CQP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, validator


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
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    openaq_api_key: str | None = os.getenv("OPENAQ_API_KEY")
    orion_broker_url: str = os.getenv("ORION_BROKER_URL", "http://localhost:1026")
    first_superuser: str = os.getenv("FIRST_SUPERUSER", "admin@example.com")
    first_superuser_password: str = os.getenv("FIRST_SUPERUSER_PASSWORD", "123456")
    static_dir: str = os.getenv("STATIC_DIR", "static")
    aqi_service_path: str = os.getenv("AQI_SERVICE_PATH", "https://smartdatamodels.org/dataModel.Environment")

    @validator("cors_origins", pre=True)
    def split_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
