print("--- [DEBUG] File aqi_agent.py đã được đọc ---")

import asyncio
import httpx
from datetime import datetime, timezone
import services  # Import file services.py của bạn
from config import ORION_BROKER_URL  # Import URL của Orion-LD

# --- 1. CẤU HÌNH (Đã sửa lỗi 405) ---
print("--- [DEBUG] Đang cấu hình URLs... ---")
ORION_UPSERT_URL = f"{ORION_BROKER_URL}/ngsi-ld/v1/entityOperations/upsert?options=update"
HEADERS = {
    "Content-Type": "application/ld+json",
    "Accept": "application/json"
}
CONTEXT = "https://schema.lab.fiware.org/ld/context"

# --- 2. HÀM "DỊCH THUẬT" (Đã sửa lỗi 'null observedAt') ---
def translate_to_ngsi_aqi(measurement: dict) -> dict:
    station_name = measurement.get("station_name", "Trạm không tên")
    provider = measurement.get("provider_name", "Không rõ")
    coords = measurement.get("coordinates", {})
    value = measurement.get("value")
    utc_time_str = measurement.get("datetime_utc") # Có thể là None
    
    safe_name = "".join(e for e in station_name if e.isalnum())
    safe_name_id = measurement.get("sensor_id", "UnknownID") 
    entity_id = f"urn:ngsi-ld:AirQualityObserved:Hanoi:{safe_name}:{safe_name_id}"

    # 1. Tạo payload cơ bản
    pm25_payload = {
        "type": "Property",
        "value": value,
        "unitCode": "GP" # µg/m³
    }
    
    # 2. CHỈ thêm 'observedAt' NẾU NÓ TỒN TẠI (khác None)
    if utc_time_str:
        pm25_payload["observedAt"] = utc_time_str
    else:
        # Cảnh báo này là BÌNH THƯỜNG (vì trạm OpenAQ không có data)
        print(f"Cảnh báo: Không có 'observedAt' cho {entity_id}. Sẽ bỏ qua thuộc tính này.")

    payload = {
        "id": entity_id,
        "type": "AirQualityObserved",
        
        "location": {
            "type": "GeoProperty",
            "value": {
                "type": "Point",
                "coordinates": [coords.get("longitude", 0), coords.get("latitude", 0)]
            }
        },
        
        "pm25": pm25_payload,
        
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

# --- 3. HÀM CHẠY CHÍNH CỦA ĐẶC VỤ (Đã sửa lỗi 201) ---
async def run_aqi_agent():
    print("--- [Đặc Vụ AQI] bắt đầu khởi động (trong hàm run_aqi_agent) ---")
    
    while True:
        print(f"\n[{datetime.now()}] Đang chạy... Lấy dữ liệu AQI từ OpenAQ...")
        
        try:
            live_measurements = await services.get_hanoi_aqi()
            
            if not live_measurements:
                print("Không tìm thấy số đo 'sống' nào. Bỏ qua vòng này.")
                await asyncio.sleep(600) # Nghỉ 10 phút
                continue

            print(f"Tìm thấy {len(live_measurements)} số đo 'sống'. Bắt đầu 'bơm' (upsert) lên Orion-LD...")
            
            entities_to_upsert = []
            for measurement in live_measurements:
                ngsi_entity = translate_to_ngsi_aqi(measurement)
                entities_to_upsert.append(ngsi_entity)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    ORION_UPSERT_URL, 
                    headers=HEADERS, 
                    json=entities_to_upsert,
                    timeout=30.0
                )
                
                # --- SỬA LỖI TẠI ĐÂY ---
                # Chấp nhận 201 (Created) VÀ 204 (No Content/Updated) là THÀNH CÔNG
                if response.status_code == 204 or response.status_code == 201:
                    print(f"Thành công! Đã 'upsert' {len(entities_to_upsert)} thực thể (Code: {response.status_code}).")
                # --- HẾT PHẦN SỬA LỖI ---
                
                elif response.status_code == 207: # 207 Multi-Status
                    print(f"Thành công 1 phần (Multi-Status): {response.text}")
                else:
                    print(f"LỖI 'UPSERT': {response.status_code} - {response.text}")

        except Exception as e:
            print(f"LỖI NGHIÊM TRỌNG TRONG VÒNG LẶP: {e}")
            import traceback
            traceback.print_exc() 
            
        print("--- [Đặc Vụ AQI] Hoàn thành. Nghỉ 10 phút... ---")
        await asyncio.sleep(600) 

# --- 4. ĐIỂM KHỞI CHẠY (Giữ nguyên) ---
print("--- [DEBUG] Sắp vào __main__ ---")

if __name__ == "__main__":
    print("--- [DEBUG] Đã vào __main__, sắp chạy asyncio.run() ---")
    try:
        asyncio.run(run_aqi_agent())
    except KeyboardInterrupt:
        print("\n--- [Đặc Vụ AQI] Đã tắt. ---")
    except Exception as e_main:
        print(f"LỖI KHỞI ĐỘNG NGHIÊM TRỌNG: {e_main}")
        import traceback
        traceback.print_exc()