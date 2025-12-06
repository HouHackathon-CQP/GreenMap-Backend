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

from fastapi import APIRouter

from app.api.routes import aqi, auth, locations, news, reports, system, uploads, users, weather, traffic, ai


api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(locations.router)
api_router.include_router(news.router)
api_router.include_router(reports.router)
api_router.include_router(uploads.router)
api_router.include_router(aqi.router)
api_router.include_router(weather.router)
api_router.include_router(traffic.router)
api_router.include_router(ai.router)
