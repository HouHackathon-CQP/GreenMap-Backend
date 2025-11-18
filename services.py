import httpx
from fastapi import HTTPException
from config import OPENAQ_API_KEY
from datetime import datetime, timezone, timedelta
import asyncio 

BASE_URL = "https://api.openaq.org/v3"

# -----------------------------------------------------------------
# HÀM HELPER (Để gọi API song song)
# -----------------------------------------------------------------
async def fetch_sensor_measurement(client: httpx.AsyncClient, sensor_id: int, headers: dict):
    """
    Hàm này lấy số đo MỚI NHẤT (limit=1) từ MỘT sensor.
    """
    meas_url = f"{BASE_URL}/sensors/{sensor_id}/measurements" 
    meas_params = {"limit": 1, "order_by": "datetime", "sort": "desc"}
    
    try:
        meas_res = await client.get(meas_url, params=meas_params, headers=headers)
        if meas_res.status_code == 404:
            return None # Sensor không có dữ liệu
        meas_res.raise_for_status()
        data = meas_res.json().get("results", [])
        if data:
            return data[0] # Trả về object số đo ({"value": 10, "date": ...})
    except Exception as e:
        print(f"Lỗi khi gọi sensor {sensor_id}: {e}")
        return None
    return None

# -----------------------------------------------------------------
# HÀM API CHÍNH (Kết hợp code của BẠN và của TÔI)
# -----------------------------------------------------------------
async def get_hanoi_aqi():
    try:
        headers = {"accept": "application/json"}
        if OPENAQ_API_KEY:
            headers["X-API-Key"] = OPENAQ_API_KEY
        else:
            print("CẢNH BÁO: Đang gọi OpenAQ mà không có API Key...")

        async with httpx.AsyncClient() as client:
            
            # --- Bước 1: Lấy các trạm ---
            loc_url = f"{BASE_URL}/locations"
            loc_params = {
                "coordinates": "21.0285,105.8542",
                "radius": 25000,
                "parameter": "pm25",
                "limit": 500,
                "sort": "desc",
                "order_by": "id"
            }
            print("Bước 1: Đang lấy danh sách 37 trạm...")
            loc_res = await client.get(loc_url, params=loc_params, headers=headers)
            loc_res.raise_for_status() 
            all_stations = loc_res.json().get("results", [])
            
            # --- Bước 2: Lọc 24h ---
            active_stations_metadata = [] # Đây là danh sách các trạm "sống"
            now = datetime.now(timezone.utc)
            one_day_ago = now - timedelta(days=1)
            
            for station in all_stations:
                datetime_last_obj = station.get("datetimeLast")
                if not datetime_last_obj: continue
                last_update_str = datetime_last_obj.get("utc")
                if not last_update_str: continue
                
                try:
                    if last_update_str.endswith("Z"):
                        last_update_str = last_update_str[:-1] + "+00:00"
                    last_update_time = datetime.fromisoformat(last_update_str)
                    
                    if last_update_time > one_day_ago:
                        active_stations_metadata.append(station) # Giữ lại trạm "sống"
                        
                except (ValueError, TypeError):
                    continue
            
            print(f"Bước 2: Đã lọc, còn {len(active_stations_metadata)} trạm 'sống'.")
            if not active_stations_metadata:
                return [] # Trả về rỗng nếu không có trạm nào "sống"

            # --- Bước 3: Lấy sensor PM2.5 từ các trạm "sống" ---
            sensors_to_fetch = []
            for loc in active_stations_metadata:
                coords = loc.get("coordinates", {})
                provider_name = loc.get("provider", {}).get("name", "Không rõ")
                station_name = loc.get("name", "Trạm không tên")
                
                for sensor in loc.get("sensors", []):
                    param_info = sensor.get("parameter", {})
                    # Lấy 'name' trong 'parameter'
                    if param_info.get("name") == "pm25": 
                        sensors_to_fetch.append({
                            "sensor_id": sensor["id"],
                            "station_name": station_name,
                            "coordinates": coords,
                            "provider_name": provider_name
                        })

            unique_sensors_map = {s["sensor_id"]: s for s in sensors_to_fetch}
            unique_sensors_list = list(unique_sensors_map.values())
            
            print(f"Bước 3: Đã tìm thấy {len(unique_sensors_list)} sensors PM2.5. Bắt đầu gọi song song...")

            # --- Bước 4: Gọi API đo lường song song ---
            tasks = []
            for sensor_info in unique_sensors_list:
                tasks.append(fetch_sensor_measurement(client, sensor_info["sensor_id"], headers))
            
            measurements_results = await asyncio.gather(*tasks)

            # --- Bước 5: Gộp kết quả ---
            final_results = []
            for i, measurement_data in enumerate(measurements_results):
                if measurement_data: # Bỏ qua các sensor không có dữ liệu
                    sensor_info = unique_sensors_list[i]
                    
                    final_results.append({
                        "station_name": sensor_info["station_name"],
                        "provider_name": sensor_info["provider_name"],
                        "coordinates": sensor_info["coordinates"],
                        "value": measurement_data.get("value"),
                        "unit": measurement_data.get("unit"),
                        "datetime_utc": measurement_data.get("date", {}).get("utc") 
                    })

            print(f"Hoàn thành. Trả về {len(final_results)} kết quả.")
            return final_results

    except httpx.HTTPStatusError as exc:
        print(f"Lỗi HTTP (Bước 1): {exc.response.status_code} - {exc.response.text}")
        raise HTTPException(status_code=exc.response.status_code, detail=f"Lỗi từ OpenAQ: {exc.response.text}")
    except Exception as e:
        import traceback
        print(traceback.format_exc()) 
        raise HTTPException(status_code=500, detail=f"Lỗi server nội bộ: {e}")