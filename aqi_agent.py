print("--- [DEBUG] File aqi_agent.py đã được đọc ---")

import asyncio
import httpx
from datetime import datetime, timezone
import services  # Import file services.py
from config import ORION_BROKER_URL  # Import URL Orion-LD

print("--- [DEBUG] Đang cấu hình URLs... ---")
ORION_UPSERT_URL = f"{ORION_BROKER_URL}/ngsi-ld/v1/entityOperations/upsert?options=update"

HEADERS = {
    "Content-Type": "application/ld+json",
    "Accept": "application/json"
}

# --- CHUẨN HÓA: Sử dụng Context chính thức của Smart Data Models (Environment) ---
# Context này định nghĩa AirQualityObserved và refDevice đúng chuẩn SOSA/SSN
CONTEXT = "https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld"

def translate_to_ngsi_aqi(measurement: dict) -> dict:
    """
    Dịch dữ liệu sang NGSI-LD tuân thủ SOSA/SSN.
    """
    station_name = measurement.get("station_name", "Trạm không tên")
    provider = measurement.get("provider_name", "Không rõ")
    coords = measurement.get("coordinates", {})
    value = measurement.get("value")
    utc_time_str = measurement.get("datetime_utc")
    
    safe_name = "".join(e for e in station_name if e.isalnum())
    sensor_id = measurement.get("sensor_id", "UnknownID") 
    
    # ID Quan trắc (Observation)
    entity_id = f"urn:ngsi-ld:AirQualityObserved:Hanoi:{safe_name}:{sensor_id}"
    
    # ID Thiết bị (Sensor) - Phải khớp với logic tạo Device
    device_ref_id = f"urn:ngsi-ld:Device:OpenAQ-{sensor_id}"

    # Payload cho thuộc tính PM2.5
    pm25_payload = {
        "type": "Property",
        "value": value,
        "unitCode": "GP" # Mã chuẩn cho µg/m³
    }
    
    # Chỉ thêm thời gian quan sát nếu có
    if utc_time_str:
        pm25_payload["observedAt"] = utc_time_str

    # Cấu trúc Entity
    payload = {
        "id": entity_id,
        "type": "AirQualityObserved", # Tương đương sosa:Observation
        
        "location": {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": [coords.get("longitude", 0), coords.get("latitude", 0)]
            }
        },
        
        "pm25": pm25_payload, # Tương đương sosa:hasResult
        
        # --- LIÊN KẾT DỮ LIỆU (LINKED DATA) ---
        # Thuộc tính này liên kết Quan trắc với Thiết bị đo (sosa:madeBySensor)
        "refDevice": {
            "type": "Relationship",
            "object": device_ref_id
        },
        # --------------------------------------
        
        "provider": {
            "type": "Property",
            "value": provider
        },
        "stationName": {
            "type": "Property",
            "value": station_name
        },
        
        "@context": CONTEXT
    }
    return payload

async def run_aqi_agent():
    print("--- [Đặc Vụ AQI] bắt đầu khởi động ---")
    
    while True:
        print(f"\n[{datetime.now()}] Đang chạy... Lấy dữ liệu AQI từ OpenAQ...")
        
        try:
            live_measurements = await services.get_hanoi_aqi()
            
            if not live_measurements:
                print("Không tìm thấy số đo 'sống' nào. Bỏ qua vòng này.")
                await asyncio.sleep(600)
                continue

            print(f"Tìm thấy {len(live_measurements)} số đo 'sống'. Bắt đầu 'bơm' (upsert) lên Orion-LD...")
            
            entities_to_upsert = []
            for measurement in live_measurements:
                ngsi_entity = translate_to_ngsi_aqi(measurement)
                entities_to_upsert.append(ngsi_entity)

            async with httpx.AsyncClient() as client:
                # Tăng timeout vì Context từ GitHub có thể tải hơi lâu lần đầu
                response = await client.post(
                    ORION_UPSERT_URL, 
                    headers=HEADERS, 
                    json=entities_to_upsert,
                    timeout=60.0 
                )
                
                if response.status_code == 204 or response.status_code == 201:
                    print(f"Thành công! Đã 'upsert' {len(entities_to_upsert)} thực thể (Code: {response.status_code}).")
                elif response.status_code == 207:
                    print(f"Thành công 1 phần (Multi-Status): {response.text}")
                else:
                    print(f"LỖI 'UPSERT': {response.status_code} - {response.text}")

        except Exception as e:
            print(f"LỖI NGHIÊM TRỌNG: {e}")
            import traceback
            traceback.print_exc() 
            
        print("--- [Đặc Vụ AQI] Hoàn thành. Nghỉ 10 phút... ---")
        await asyncio.sleep(600) 

if __name__ == "__main__":
    try:
        asyncio.run(run_aqi_agent())
    except KeyboardInterrupt:
        print("\n--- [Đặc Vụ AQI] Đã tắt. ---")
    except Exception as e_main:
        print(f"LỖI KHỞI ĐỘNG: {e_main}")