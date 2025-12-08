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

import httpx
from fastapi import APIRouter, HTTPException, Query
from app.core.config import settings
from app.services import weather as weather_service

router = APIRouter(prefix="/weather", tags=["weather"])

@router.get("/hanoi")
async def get_hanoi_weather(
    limit: int = Query(100, ge=1, description="Số lượng kết quả")
):
    """
    Lấy dữ liệu thời tiết các quận từ Orion-LD.
    """
    orion_url = f"{settings.orion_broker_url}/ngsi-ld/v1/entities"
    full_type = "https://smartdatamodels.org/dataModel.Environment/WeatherObserved"
    
    params = {
        "type": full_type,
        "limit": limit,
        "options": "keyValues"
    }
    
    headers = {
        "Accept": "application/ld+json",
        "Link": '<https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld>; rel="http://www.w3.org/ns/ldp#context"; type="application/ld+json"'
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(orion_url, params=params, headers=headers)
            response.raise_for_status()
            
            orion_data = response.json()
            
            return {
                "source": "Orion-LD Context Broker",
                "count": len(orion_data),
                "data": orion_data
            }
            
        except Exception as e:
            return {
                "source": "Orion-LD (Error)",
                "error": str(e),
                "hint": "Kiểm tra kết nối tới Orion-LD."
            }
        
@router.get("/forecast")
async def get_weather_forecast(
    lat: float = Query(21.0285, description="Vĩ độ"),
    lon: float = Query(105.8542, description="Kinh độ")
):
    """
    API Dự báo thời tiết chi tiết (Direct from Open-Meteo).
    - Trả về: Hiện tại, 24h tới, 7 ngày tới.
    - Phục vụ: Hiển thị biểu đồ trên Mobile App.
    """
    data = await weather_service.get_weather_forecast(lat, lon)
    
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu thời tiết.")
        
    return {
        "source": "Open-Meteo",
        "location": {"lat": lat, "lon": lon},
        "data": data
    }