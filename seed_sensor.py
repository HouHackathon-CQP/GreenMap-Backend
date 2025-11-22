import asyncio

import httpx

from app.core.config import settings
from app.services import openaq

ORION_ENTITIES_URL = f"{settings.orion_broker_url}/ngsi-ld/v1/entities"
HEADERS = {"Content-Type": "application/ld+json", "Accept": "application/json"}
CONTEXT = "https://schema.lab.fiware.org/ld/context"

async def seed_devices():
    print("--- BẮT ĐẦU ĐĂNG KÝ THIẾT BỊ (SOSA: SENSOR) ---")
    
    # 1. Lấy danh sách trạm từ OpenAQ (Dùng hàm có sẵn)
    # Hàm này trả về danh sách các số đo, ta sẽ trích xuất thông tin trạm từ đó
    measurements = await openaq.get_hanoi_aqi()
    
    if not measurements:
        print("Không lấy được dữ liệu từ OpenAQ.")
        return

    print(f"Tìm thấy {len(measurements)} trạm. Đang tạo thực thể Device...")

    async with httpx.AsyncClient() as client:
        for item in measurements:
            sensor_id = item["sensor_id"]
            station_name = item["station_name"]
            coords = item["coordinates"]
            provider = item["provider_name"]

            # 2. Tạo ID chuẩn cho Thiết bị
            device_id = f"urn:ngsi-ld:Device:OpenAQ-{sensor_id}"

            # 3. Tạo Payload theo chuẩn NGSI-LD (Mô hình hóa SOSA:Sensor)
            payload = {
                "id": device_id,
                "type": "Device", # Đây là Entity đại diện cho Cảm biến
                "category": {
                    "type": "Property",
                    "value": ["sensor"]
                },
                "name": {
                    "type": "Property",
                    "value": station_name
                },
                "location": {
                    "type": "GeoProperty",
                    "value": {
                        "type": "Point",
                        "coordinates": [coords.get("longitude", 0), coords.get("latitude", 0)]
                    }
                },
                "provider": {
                    "type": "Property",
                    "value": provider
                },
                "controlledProperty": {
                    "type": "Property",
                    "value": ["airQuality"] # Thiết bị này đo cái gì?
                },
                "@context": CONTEXT
            }

            # 4. Gửi sang Orion-LD
            try:
                resp = await client.post(ORION_ENTITIES_URL, json=payload, headers=HEADERS)
                if resp.status_code == 201:
                    print(f"✅ Đã đăng ký Device: {station_name}")
                elif resp.status_code == 409:
                    print(f"⚠️ Device đã tồn tại: {station_name}")
                else:
                    print(f"❌ Lỗi: {resp.text}")
            except Exception as e:
                print(f"❌ Lỗi kết nối: {e}")

    print("--- HOÀN TẤT ĐĂNG KÝ THIẾT BỊ ---")

if __name__ == "__main__":
    asyncio.run(seed_devices())
