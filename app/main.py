import asyncio
import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.api import api_router
from app.core.config import settings
from app.db.session import init_db

logger = logging.getLogger(__name__)


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    logger.info("--- [SYSTEM] Đã kích hoạt WindowsSelectorEventLoopPolicy ---")


def create_application() -> FastAPI:
    app = FastAPI(title=settings.project_name)

    static_dir = Path(settings.static_dir)
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.on_event("startup")
    async def on_startup():
        await init_db()

    app.include_router(api_router)
    return app


app = create_application()
