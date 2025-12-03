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
from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings
from shapely import wkt  # <-- 1. Thay đổi import: Dùng wkt thay vì to_shape

# Cấu hình Orion
ORION_UPSERT_URL = f"{settings.orion_broker_url}/ngsi-ld/v1/entityOperations/upsert?options=update"
# Dùng Context chuẩn Môi trường (giống các file khác)
CONTEXT = "https://raw.githubusercontent.com/smart-data-models/dataModel.Transportation/master/context.jsonld"
HEADERS = {"Content-Type": "application/ld+json", "Accept": "application/json"}

async def sync_db_to_orion():
    print("--- 🔄 BẮT ĐẦU ĐỒNG BỘ TỪ POSTGRES SANG ORION ---")
    
    async with engine.begin() as conn:
        # --- 2. SỬA CÂU TRUY VẤN ---
        # Dùng ST_AsText(location) để lấy chuỗi WKT (dễ xử lý hơn raw binary)
        query = text("""
            SELECT id, name, location_type, description, ST_AsText(location) as location_wkt 
            FROM green_locations
        """)
        result = await conn.execute(query)
        rows = result.all()
        
        print(f"📦 Tìm thấy {len(rows)} địa điểm trong DB. Đang đẩy sang Orion...")
        
        batch_entities = []
        
        for row in rows:
            # Bỏ qua nếu không có tọa độ
            if not row.location_wkt:
                continue

            # --- 3. XỬ LÝ TỌA ĐỘ ---
            # Dùng wkt.loads để đọc chuỗi "POINT(105.8 21.0)"
            try:
                point = wkt.loads(row.location_wkt)
                
                # Tạo ID chuẩn: urn:ngsi-ld:PUBLIC_PARK:1 (Dùng ID số của Postgres)
                # Lưu ý: row.location_type trong DB có thể là enum hoặc string
                # Nếu là enum python, cần .value, nếu là string raw từ SQL thì dùng trực tiếp
                loc_type = row.location_type
                # Xử lý trường hợp nó trả về object Enum của Python
                if hasattr(loc_type, 'value'):
                    loc_type = loc_type.value
                
                entity_id = f"urn:ngsi-ld:{loc_type}:{row.id}"
                
                entity = {
                    "id": entity_id,
                    "type": loc_type,
                    "name": {"type": "Property", "value": row.name},
                    "location": {
                        "type": "GeoProperty",
                        "value": {
                            "type": "Point",
                            "coordinates": [point.x, point.y] # Lon, Lat
                        }
                    },
                    "source": {"type": "Property", "value": "PostgreSQL"},
                    "@context": CONTEXT
                }
                
                if row.description:
                    entity["description"] = {"type": "Property", "value": row.description}
                    
                batch_entities.append(entity)
            except Exception as e:
                print(f"⚠️ Lỗi xử lý dòng ID {row.id}: {e}")
                continue
            
            # Gửi từng lô 100 cái
            if len(batch_entities) >= 100:
                await send_batch(batch_entities)
                batch_entities = []
        
        # Gửi nốt lô cuối
        if batch_entities:
            await send_batch(batch_entities)

    print("--- ✅ ĐỒNG BỘ HOÀN TẤT ---")

async def send_batch(entities):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(ORION_UPSERT_URL, json=entities, headers=HEADERS, timeout=30.0)
            
            # 201: Created, 204: No Content (Updated success)
            if resp.status_code in [201, 204]:
                print(f"   -> Đã đẩy {len(entities)} entities.")
            elif resp.status_code == 207:
                print(f"   -> Đã đẩy {len(entities)} entities (Multi-Status).")
            else:
                print(f"   ❌ Lỗi Orion: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"   ❌ Lỗi kết nối: {e}")

if __name__ == "__main__":
    asyncio.run(sync_db_to_orion())