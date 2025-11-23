from fastapi import APIRouter

from app.api.routes import aqi, auth, locations, news, reports, system, uploads, users

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(locations.router)
api_router.include_router(news.router)
api_router.include_router(reports.router)
api_router.include_router(uploads.router)
api_router.include_router(aqi.router)
