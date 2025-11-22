import asyncio
import json
from pathlib import Path

import httpx

from app.core.config import settings
from app.models.enums import LocationType

ORION_ENTITIES_URL = f"{settings.orion_broker_url}/ngsi-ld/v1/entities"

# Header chuẩn NGSI-LD
HEADERS = {
    "Content-Type": "application/ld+json",
    "Accept": "application/json"
}
# Bối cảnh (Context) để Orion hiểu "name", "location" là gì
CONTEXT = "https://schema.lab.fiware.org/ld/context"

# --- 3. ĐƯỜNG DẪN DỮ LIỆU ---
CURRENT_FILE_PATH = Path(__file__).resolve()
PROJECT_DIR = CURRENT_FILE_PATH.parent
# Trỏ đến thư mục data (ngang hàng với thư mục backend)
DATA_DIR = PROJECT_DIR.parent / "GreenMap-Data" / "Data"


# --- 4. HÀM "DỊCH" VÀ "BƠM" ---
async def create_ngsi_entity(client: httpx.AsyncClient, feature: dict, entity_type: LocationType):
    """
    Dịch 1 'feature' từ GeoJSON sang JSON-LD và POST lên Orion.
    """
    properties = feature.get("properties", {})
    geometry = feature.get("geometry")

    if not geometry:
        return

    # 1. Tạo ID duy nhất (URN)
    osm_id = properties.get("@id", "").replace("/", "-")
    if not osm_id:
        print("Bỏ qua (không có @id)")
        return

    entity_id = f"urn:ngsi-ld:{entity_type.value}:{osm_id}"

    # 2. Lấy tên (nếu không có, dùng tên dự phòng)
    name = properties.get("name")
    if not name:
        name = properties.get("description", f"{entity_type.value} {osm_id}")

    # 3. Xây dựng Payload (JSON-LD)
    payload = {
        "id": entity_id,
        "type": entity_type.value,

        "name": {
            "type": "Property",
            "value": str(name)  # Ép kiểu sang string
        },

        "location": {
            "type": "GeoProperty",
            "value": geometry  # Gửi thẳng object GeoJSON (Point hoặc Polygon)
        },

        "source": {
            "type": "Property",
            "value": "OpenStreetMap"
        },
        "original_osm_id": {
            "type": "Property",
            "value": properties.get("@id")
        },

        "@context": CONTEXT
    }

    # 4. "Bơm" (POST) thực thể lên Orion-LD
    try:
        response = await client.post(ORION_ENTITIES_URL, headers=HEADERS, json=payload, timeout=30.0)

        if response.status_code == 201:  # 201 Created
            print(f"Đã tạo: {entity_id}")
        elif response.status_code == 409:  # 409 Conflict
            print(f"Bỏ qua (đã tồn tại): {entity_id}")
        else:
            print(f"LỖI BƠM: {entity_id} - {response.status_code} - {response.text}")

    except httpx.ConnectError:
        print(
            f"LỖI KẾT NỐI: Không thể kết nối tới Orion-LD tại . Bạn đã chạy 'docker-compose up' chưa?")
        return  # Dừng nếu không kết nối được
    except Exception as e:
        print(f"Lỗi không xác định: {e}")


# --- 5. HÀM CHẠY CHÍNH ---
async def seed():
    if not DATA_DIR.exists():
        print(f"LỖI: Không tìm thấy thư mục data tại: {DATA_DIR}")
        print(
            "Hãy chắc chắn cấu trúc thư mục là: \n- HCMConnect-Backend\n- HCMConnect-Data\n  - Data\n    - park.geojson\n    - ...")
        return

    print(f"Sẽ đọc dữ liệu từ: {DATA_DIR}")
    print(f"Bơm dữ liệu vào Context Broker tại: {settings.orion_broker_url}")


async with httpx.AsyncClient() as client:
    tasks = []  # Danh sách các "việc cần làm"

    # 1. Bơm TRẠM SẠC
    print("Đang đọc Trạm Sạc...")
    charging_file = DATA_DIR / "charging_station.geojson"
    with open(charging_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for feature in data['features']:
            tasks.append(create_ngsi_entity(client, feature, LocationType.CHARGING_STATION))

    # 2. Bơm ĐIỂM THUÊ XE ĐẠP
    print("Đang đọc Thuê Xe Đạp...")
    bicycle_file = DATA_DIR / "bicycle_rental.geojson"
    with open(bicycle_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for feature in data['features']:
            tasks.append(create_ngsi_entity(client, feature, LocationType.BICYCLE_RENTAL))

    # 3. Bơm CÔNG VIÊN
    print("Đang đọc Công Viên...")
    park_file = DATA_DIR / "park.geojson"
    with open(park_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for feature in data['features']:
            tasks.append(create_ngsi_entity(client, feature, LocationType.PUBLIC_PARK))

    # 4. Bơm ĐỊA ĐIỂM DU LỊCH
    print("Đang đọc Địa Điểm Du Lịch...")
    tourist_file = DATA_DIR / "tourist_attractions.geojson"
    with open(tourist_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for feature in data['features']:
            tasks.append(create_ngsi_entity(client, feature, LocationType.TOURIST_ATTRACTION))

    # --- 6. Chạy song song (theo lô) ---
    print(f"\n--- Chuẩn bị bơm {len(tasks)} thực thể. Quá trình này có thể mất vài phút... ---")

    for i in range(0, len(tasks), 100):  # Chạy 100 task 1 lần
        batch = tasks[i:i + 100]
        print(f"--- Đang chạy lô {i // 100 + 1}/{len(tasks) // 100 + 1} ---")
        await asyncio.gather(*batch)
        await asyncio.sleep(1)  # Nghỉ 1 giây

    print("\n--- HOÀN THÀNH BƠM DỮ LIỆU VÀO ORION-LD! ---")

if __name__ == "__main__":
    asyncio.run(seed())
