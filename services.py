import httpx
from fastapi import HTTPException
from config import OPENAQ_API_KEY
from datetime import datetime, timezone, timedelta # Vẫn cần để parse
import asyncio 

BASE_URL = "https://api.openaq.org/v3"

# --- HÀM HELPER (Giữ nguyên) ---
async def fetch_sensor_measurement(client: httpx.AsyncClient, sensor_id: int, headers: dict):
    meas_url = f"{BASE_URL}/sensors/{sensor_id}/measurements" 
    meas_params = {
        "limit": 1, 
        "order_by": "datetime",
        "sort": "desc"
    }
    
    try:
        meas_res = await client.get(meas_url, params=meas_params, headers=headers)
        if meas_res.status_code == 404:
            return None 
        meas_res.raise_for_status()
        data = meas_res.json().get("results", [])
        if data:
            return data[0]
    except httpx.RequestError as e:
        print(f"Lỗi khi gọi sensor {sensor_id}: {e}")
        return None
    return None

# --- HÀM API CHÍNH (Đã cập nhật) ---
async def get_hanoi_aqi():
    try:
        headers = {
            "accept": "application/json",
            "X-API-Key": OPENAQ_API_KEY, 
        }

        async with httpx.AsyncClient() as client:

            # --- Bước 1: Lấy các trạm của Hà Nội (Dùng tọa độ) ---
            loc_url = f"{BASE_URL}/locations"
            loc_params = {
                "coordinates": "21.0285,105.8542",
                "radius": 25000,
                "parameter": "pm25",
                "limit": 200
            }
            loc_res = await client.get(loc_url, params=loc_params, headers=headers)
            loc_res.raise_for_status()
            locations = loc_res.json().get("results", [])

            # --- Bước 2: Tạo danh sách "việc cần làm" ---
            sensors_to_fetch = []
            for loc in locations:
                coords = loc.get("coordinates", {})
                provider_name = loc.get("provider", {}).get("name", "Không rõ")
                station_name = loc.get("name", "Trạm không tên") 
                
                for sensor in loc.get("sensors", []):
                    param_info = sensor.get("parameter", {})
                    if param_info.get("name") == "pm25": 
                        sensors_to_fetch.append({
                            "sensor_id": sensor["id"],
                            "station_name": station_name,
                            "coordinates": coords,
                            "provider_name": provider_name
                        })

            if not sensors_to_fetch:
                raise HTTPException(status_code=404, detail="Không tìm thấy sensor pm25 tại Hà Nội (dùng tọa độ)")

            unique_sensors_map = {s["sensor_id"]: s for s in sensors_to_fetch}
            unique_sensors_list = list(unique_sensors_map.values())
            
            print(f"Đã tìm thấy {len(unique_sensors_list)} sensors PM2.5. Bắt đầu gọi song song...")

            # --- Bước 3: Thực thi song song (Giữ nguyên) ---
            tasks = []
            for sensor_info in unique_sensors_list:
                tasks.append(fetch_sensor_measurement(client, sensor_info["sensor_id"], headers))
            
            measurements_results = await asyncio.gather(*tasks)

            # --- Bước 4: Gộp kết quả (BỎ LỌC 24 GIỜ) ---
            final_results = []
            
            for i, measurement_data in enumerate(measurements_results):
                if measurement_data:
                    sensor_info = unique_sensors_list[i]
                    
                    datetime_obj = measurement_data.get("date", {})
                    utc_time_str = datetime_obj.get("utc") if datetime_obj else None
                    
                    # (Chúng ta vẫn parse ngày tháng, nhưng không lọc)
                    try:
                        if utc_time_str and utc_time_str.endswith("Z"):
                            utc_time_str = utc_time_str[:-1] + "+00:00"
                        
                        # (Vẫn parse để kiểm tra, nhưng không dùng để lọc)
                        datetime.fromisoformat(utc_time_str) 
                        
                        final_results.append({
                            "sensor_id": sensor_info["sensor_id"],
                            "station_name": sensor_info["station_name"],
                            "provider_name": sensor_info["provider_name"],
                            "coordinates": sensor_info["coordinates"],
                            "value": measurement_data.get("value"),
                            "unit": measurement_data.get("unit"),
                            "datetime_utc": utc_time_str 
                        })

                    except (ValueError, TypeError, AttributeError):
                        # Nếu ngày tháng bị null hoặc sai định dạng, vẫn trả về nhưng không có thời gian
                        final_results.append({
                            "sensor_id": sensor_info["sensor_id"],
                            "station_name": sensor_info["station_name"],
                            "provider_name": sensor_info["provider_name"],
                            "coordinates": sensor_info["coordinates"],
                            "value": measurement_data.get("value"),
                            "unit": measurement_data.get("unit"),
                            "datetime_utc": None # Báo là không có thời gian
                        })

            print(f"Đã gộp xong. Trả về {len(final_results)} kết quả (không lọc 24h).")
            return final_results

    except httpx.HTTPStatusError as exc:
        print(f"Lỗi HTTP khi gọi OpenAQ V3: {exc.response.status_code} - {exc.response.text}")
        raise HTTPException(status_code=exc.response.status_code, detail=f"Lỗi từ OpenAQ: {exc.response.text}")
    except Exception as e:
        import traceback
        print(traceback.format_exc()) 
        raise HTTPException(status_code=500, detail=f"Lỗi server nội bộ: {e}")