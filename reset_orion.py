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
import httpx
from app.core.config import settings

# Xóa tất cả các loại địa điểm
TARGET_TYPES = ["PUBLIC_PARK", "CHARGING_STATION", "BICYCLE_RENTAL", "TOURIST_ATTRACTION"]

async def reset_orion():
    print("--- 🧹 ĐANG DỌN DẸP SẠCH SẼ ORION-LD ---")
    async with httpx.AsyncClient() as client:
        for type_ in TARGET_TYPES:
            print(f"Đang xóa loại {type_}...")
            # Lấy danh sách
            res = await client.get(f"{settings.orion_broker_url}/ngsi-ld/v1/entities?type={type_}&limit=1000", 
                                   headers={"Accept": "application/ld+json", "Link": f'<{settings.ngsi_context_url}>; rel="http://www.w3.org/ns/ldp#context"; type="application/ld+json"'})
            entities = res.json()
            
            # Xóa từng cái
            for entity in entities:
                await client.delete(f"{settings.orion_broker_url}/ngsi-ld/v1/entities/{entity['id']}")
                
    print("--- ✅ ORION ĐÃ TRỐNG RỖNG ---")

if __name__ == "__main__":
    asyncio.run(reset_orion())