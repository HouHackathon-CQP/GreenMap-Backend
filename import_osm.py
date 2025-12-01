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

import json
import asyncio
import os
from sqlalchemy import text
from app.db.session import engine
from app.models.enums import LocationType
from shapely.geometry import shape, Point

# Cấu hình đường dẫn file và loại tương ứng
DATA_MAPPING = [
    {"file": "Data/park.geojson", "type": LocationType.PUBLIC_PARK},
    {"file": "Data/charging_station.geojson", "type": LocationType.CHARGING_STATION},
    {"file": "Data/bicycle_rental.geojson", "type": LocationType.BICYCLE_RENTAL},
    {"file": "Data/tourist_attractions.geojson", "type": LocationType.TOURIST_ATTRACTION},
]

async def import_osm_data():
    print("--- 🚀 BẮT ĐẦU NHẬP DỮ LIỆU TỪ OSM VÀO POSTGRESQL ---")
    
    async with engine.begin() as conn:
        # Xóa dữ liệu cũ để nạp lại từ đầu (Reset)
        await conn.execute(text("TRUNCATE TABLE green_locations RESTART IDENTITY CASCADE"))
        
        total_count = 0

        for item in DATA_MAPPING:
            file_path = item["file"]
            loc_type = item["type"].value
            
            if not os.path.exists(file_path):
                print(f"⚠️ Không tìm thấy file: {file_path}")
                continue
                
            print(f"📂 Đang xử lý {file_path}...")
            
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            features = data.get("features", [])
            batch_values = []
            
            for feature in features:
                props = feature.get("properties", {})
                geom = feature.get("geometry")
                
                if not geom: continue

                # 1. Xử lý Tên (Lấy name, nếu không có lấy tên khác)
                name = props.get("name") or props.get("amenity") or "Địa điểm chưa đặt tên"
                
                # 2. Xử lý Hình học (Chuyển Polygon thành Point tâm)
                shapely_geom = shape(geom)
                centroid = shapely_geom.centroid
                lon = centroid.x
                lat = centroid.y
                
                # 3. Lấy ID gốc OSM
                osm_id = props.get("@id", "unknown")
                
                # 4. Tạo mô tả (Gộp các thông tin phụ)
                desc_parts = []
                if "operator" in props: desc_parts.append(f"Operator: {props['operator']}")
                if "brand" in props: desc_parts.append(f"Brand: {props['brand']}")
                if "opening_hours" in props: desc_parts.append(f"Open: {props['opening_hours']}")
                description = "; ".join(desc_parts)

                # Tạo câu lệnh SQL Insert
                # name, location_type, description, is_active, data_source, external_id, location
                val = {
                    "name": name,
                    "type": loc_type,
                    "desc": description,
                    "src": "OSM",
                    "ext_id": osm_id,
                    "wkt": f"POINT({lon} {lat})"
                }
                batch_values.append(val)
            
            # Thực thi Batch Insert
            if batch_values:
                # SQLAlchemy Core Insert
                await conn.execute(text("""
                    INSERT INTO green_locations (name, location_type, description, is_active, data_source, external_id, location)
                    VALUES (:name, :type, :desc, true, :src, :ext_id, ST_GeomFromText(:wkt, 4326))
                """), batch_values)
                
                count = len(batch_values)
                total_count += count
                print(f"   -> Đã nhập {count} địa điểm.")

    print(f"--- ✅ HOÀN TẤT! TỔNG CỘNG: {total_count} ĐỊA ĐIỂM ĐÃ VÀO DB ---")

if __name__ == "__main__":
    asyncio.run(import_osm_data())