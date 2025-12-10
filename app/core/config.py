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
    
    # API Documentation
    docs_enabled: bool = os.getenv("DOCS_ENABLED", "true").lower() == "true"
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
    ngsi_context_url: str = os.getenv("NGSI_CONTEXT_URL", "https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld")
    ngsi_type_aqi: str = os.getenv("NGSI_TYPE_AQI", "https://smartdatamodels.org/dataModel.Environment/AirQualityObserved")
    ngsi_type_weather: str = os.getenv("NGSI_TYPE_WEATHER", "https://smartdatamodels.org/dataModel.Environment/WeatherObserved")
    ngsi_context_transportation: str = os.getenv("NGSI_CONTEXT_TRANSPORTATION", "https://raw.githubusercontent.com/smart-data-models/dataModel.Transportation/master/context.jsonld")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    groq_api_key: str | None = os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY")
    groq_model: str = (
        os.getenv("GROQ_MODEL")
    )
    groq_api_base: str = (
        os.getenv("GROQ_API_BASE")
        or "https://api.groq.com/openai/v1/chat/completions"
    )
    osrm_base_url: str = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org")
    osm_nominatim_url: str = os.getenv(
        "OSM_NOMINATIM_URL",
        "https://nominatim.openstreetmap.org/search",
    )
    firebase_credentials_file: str | None = os.getenv("FIREBASE_CREDENTIALS_FILE")
    firebase_default_topic: str = os.getenv("FIREBASE_DEFAULT_TOPIC", "greenmap-daily")
    daily_push_hour: int = int(os.getenv("DAILY_PUSH_HOUR", "7"))
    daily_push_minute: int = int(os.getenv("DAILY_PUSH_MINUTE", "0"))
    daily_push_title: str = os.getenv(
        "DAILY_PUSH_TITLE",
        "Bản đồ Xanh - Cập nhật môi trường mỗi ngày",
    )
    daily_push_body: str = os.getenv(
        "DAILY_PUSH_BODY",
        "Mở ứng dụng để xem dự báo thời tiết và chất lượng không khí hôm nay.",
    )

    @validator("cors_origins", pre=True)
    def split_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
