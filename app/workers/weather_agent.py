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

import asyncio
from datetime import datetime
import httpx
import traceback

from app.core.config import settings
from app.services import weather as weather_service

print("--- [DEBUG] Đang cấu hình URLs... ---")
ORION_UPSERT_URL = f"{settings.orion_broker_url}/ngsi-ld/v1/entityOperations/upsert?options=update"

HEADERS = {
    "Content-Type": "application/ld+json",
    "Accept": "application/json"
}
CONTEXT = settings.ngsi_context_url
HANOI_DISTRICTS = [
    {"id": "HoanKiem", "name": "Hoàn Kiếm", "lat": 21.0285, "lon": 105.8542},
    {"id": "BaDinh", "name": "Ba Đình", "lat": 21.0341, "lon": 105.8372},
    {"id": "TayHo", "name": "Tây Hồ", "lat": 21.0705, "lon": 105.8243},
    {"id": "DongDa", "name": "Đống Đa", "lat": 21.0126, "lon": 105.8274},
    {"id": "CauGiay", "name": "Cầu Giấy", "lat": 21.0328, "lon": 105.7838},
    {"id": "HaiBaTrung", "name": "Hai Bà Trưng", "lat": 21.0097, "lon": 105.8545},
    {"id": "ThanhXuan", "name": "Thanh Xuân", "lat": 20.9936, "lon": 105.8148},
    {"id": "HoangMai", "name": "Hoàng Mai", "lat": 20.9715, "lon": 105.8539},
    {"id": "LongBien", "name": "Long Biên", "lat": 21.0384, "lon": 105.8962},
    {"id": "HaDong", "name": "Hà Đông", "lat": 20.9631, "lon": 105.7727}
]

def translate_to_ngsi_weather(data: dict, district_info: dict) -> dict:
    """
    Dịch dữ liệu (ĐÃ ĐƯỢC SERVICE XỬ LÝ) sang NGSI-LD.
    """
    current = data.get("current", {})
    entity_id = f"urn:ngsi-ld:WeatherObserved:Hanoi:{district_info['id']}"
    time_str = current.get("time", datetime.now().isoformat())

    payload = {
        "id": entity_id,
        "type": settings.ngsi_type_weather,
        "address": {
            "type": "Property",
            "value": {
                "addressLocality": "Hanoi",
                "addressRegion": district_info["name"],
                "addressCountry": "VN"
            }
        },
        "location": {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": [district_info["lon"], district_info["lat"]]
            }
        },
        "temperature": {
            "type": "Property",
            "value": current.get("temp"),
            "unitCode": "CEL"
        },
        "relativeHumidity": {
            "type": "Property",
            "value": (current.get("humidity") or 0) / 100,
            "unitCode": "P1"
        },
        "weatherType": {
            "type": "Property",
            "value": current.get("desc")
        },
        "windSpeed": {
            "type": "Property",
            "value": current.get("wind_speed"),
            "unitCode": "KMH"
        },
        "dateObserved": {
            "type": "Property",
            "value": time_str
        },
        "@context": CONTEXT
    }
    return payload

async def run_weather_agent():
    print("--- [Đặc Vụ Thời Tiết] Khởi động ---")
    
    while True:
        print(f"\n[{datetime.now()}] Đang cập nhật thời tiết cho {len(HANOI_DISTRICTS)} quận...")
        entities_to_upsert = []
        
        try:
            for district in HANOI_DISTRICTS:
                weather_data = await weather_service.get_weather_forecast(district["lat"], district["lon"])
                
                if weather_data:
                    ngsi_entity = translate_to_ngsi_weather(weather_data, district)
                    entities_to_upsert.append(ngsi_entity)
            
            if entities_to_upsert:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        ORION_UPSERT_URL,
                        headers=HEADERS,
                        json=entities_to_upsert,
                        timeout=30.0
                    )
                    
                    if response.status_code in [201, 204]:
                        print(f"✅ Đã cập nhật thành công {len(entities_to_upsert)} trạm thời tiết.")
                    else:
                        print(f"❌ Lỗi Orion: {response.status_code} - {response.text}")
                        
        except Exception as e:
            print(f"Lỗi Vòng lặp: {e}")
            traceback.print_exc()
        
        print("--- Nghỉ 15 phút... ---")
        await asyncio.sleep(900) 

if __name__ == "__main__":
    try:
        asyncio.run(run_weather_agent())
    except KeyboardInterrupt:
        pass