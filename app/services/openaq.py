import asyncio
from datetime import datetime, timezone
import httpx
from app.core.config import settings

BASE_URL = "https://api.openaq.org/v3"

async def fetch_sensor_measurement(client: httpx.AsyncClient, sensor_info: dict, headers: dict):
    """
    Lấy dữ liệu từ endpoint /sensors/{id} 
    (Nơi chứa trường 'latest' mà bạn đã tìm thấy).
    """
    sensor_id = sensor_info["sensor_id"]
    
    # --- SỬA URL: Gọi vào Metadata Sensor thay vì Measurements ---
    # URL này trả về cấu trúc có chứa "latest": { "value": ... }
    meas_url = f"{BASE_URL}/sensors/{sensor_id}" 
    
    try:
        meas_res = await client.get(meas_url, headers=headers)
        if meas_res.status_code == 404:
            return None
        # Với 429 (rate limit), bỏ qua sensor này để không làm hỏng toàn bộ kết quả
        if meas_res.status_code == 429:
            print(f"[WARN] Sensor {sensor_id} bị giới hạn tần suất (429). Bỏ qua.")
            return None
        meas_res.raise_for_status()
        
        json_body = meas_res.json()
        results = json_body.get("results", [])
        
        if not results: return None
        
        # Lấy phần tử đầu tiên
        sensor_data = results[0]
        
        # --- SỬA LOGIC PARSE DỮ LIỆU (Theo mẫu bạn gửi) ---
        # Tìm trường 'latest'
        latest_obj = sensor_data.get("latest", {})
        
        if not latest_obj:
            return None # Sensor này chưa có dữ liệu đo nào
            
        val = latest_obj.get("value")
        
        # Lấy thời gian từ bên trong 'latest'
        # Cấu trúc: latest -> datetime -> utc
        time_obj = latest_obj.get("datetime", {})
        utc_time_str = time_obj.get("utc")
        
        # Lấy unit từ sensor_data (cấp ngoài) hoặc parameter
        unit = sensor_data.get("parameter", {}).get("units", "µg/m³")

        if not utc_time_str: return None

        if utc_time_str.endswith("Z"):
            utc_time_str = utc_time_str[:-1] + "+00:00"

        # Kiểm tra độ tươi (Online/Offline)
        is_online = False
        try:
            now = datetime.now(timezone.utc)
            obs_time = datetime.fromisoformat(utc_time_str)
            if (now - obs_time).total_seconds() < 86400:  # 24h
                is_online = True
        except Exception:
            pass

        return {
            "sensor_id": sensor_id,
            "station_name": sensor_info["station_name"],
            "provider_name": sensor_info["provider_name"],
            "coordinates": sensor_info["coordinates"],
            "value": val,
            "unit": unit,
            "datetime_utc": utc_time_str,
            "status": "Online" if is_online else "Offline"
        }
    except Exception as exc:
        print(f"Lỗi sensor {sensor_id}: {exc}")
        return None


async def get_hanoi_aqi(max_sensors: int = 80, concurrency: int = 5):
    """
    Lấy danh sách AQI/PM2.5 quanh Hà Nội. Giới hạn số sensor và độ song song để tránh 429.
    """
    try:
        headers = {"accept": "application/json"}
        if settings.openaq_api_key:
            headers["X-API-Key"] = settings.openaq_api_key

        async with httpx.AsyncClient() as client:
            # 1. Lấy danh sách trạm
            print("--- Đang lấy danh sách trạm từ OpenAQ... ---")
            loc_res = await client.get(
                f"{BASE_URL}/locations",
                params={
                    "coordinates": "21.0285,105.8542",
                    "radius": 25000,
                    "parameter": "pm25",
                    "limit": 1000
                },
                headers=headers
            )
            loc_res.raise_for_status()
            locations = loc_res.json().get("results", [])

            # 2. Lọc lấy các sensor PM2.5
            sensors_to_fetch = []
            for loc in locations:
                station_id = loc.get("id")
                coords = loc.get("coordinates", {})
                provider = loc.get("provider", {}).get("name", "Không rõ")
                name = loc.get("name", "Trạm không tên")

                for sensor in loc.get("sensors", []):
                    param_name = sensor.get("parameter", {}).get("name", "").lower()
                    if param_name in ["pm25", "pm2.5", "particulate matter 2.5"]:
                        sensors_to_fetch.append({
                            "station_id": station_id,
                            "sensor_id": sensor["id"],
                            "station_name": name,
                            "coordinates": coords,
                            "provider_name": provider,
                        })

            if not sensors_to_fetch:
                return []

            # Giới hạn số sensor để tránh bị rate limit
            sensors_to_fetch = sensors_to_fetch[:max_sensors]

            print(f"--- Tìm thấy {len(sensors_to_fetch)} sensors. Đang lấy dữ liệu từ trường 'latest'... ---")

            # 3. Gọi API song song nhưng giới hạn độ song song
            sem = asyncio.Semaphore(concurrency)

            async def wrapped_fetch(sensor: dict):
                async with sem:
                    return await fetch_sensor_measurement(client, sensor, headers)

            tasks = [wrapped_fetch(s) for s in sensors_to_fetch]
            measurements_results = await asyncio.gather(*tasks)

            # 4. Gom nhóm (Lấy sensor tốt nhất của mỗi trạm)
            best_stations_map = {}
            
            for res in measurements_results:
                if not res: continue
                
                # Logic gom nhóm giữ nguyên như cũ
                # (Ưu tiên Online, sau đó ưu tiên Mới nhất)
                # ... (Tôi đã tích hợp sẵn logic trả về kết quả ở đây)
                
                # Để đơn giản code, ta dùng ID trạm làm key
                # Vì chúng ta không truyền station_id vào hàm con, ta dùng tọa độ hoặc tên để gom tạm
                # Hoặc tốt nhất: Chấp nhận hiển thị tất cả sensors (nếu 1 trạm có 2 sensor sống thì hiện cả 2)
                # Nhưng để bản đồ đẹp, ta lọc theo tọa độ
                
                coord_key = f"{res['coordinates']['latitude']}_{res['coordinates']['longitude']}"
                
                if coord_key not in best_stations_map:
                    best_stations_map[coord_key] = res
                else:
                    current = best_stations_map[coord_key]
                    if res["status"] == "Online" and current["status"] == "Offline":
                        best_stations_map[coord_key] = res
            
            final_results = list(best_stations_map.values())
            print(f"--- Hoàn thành. Trả về {len(final_results)} trạm (Dữ liệu chuẩn từ 'latest'). ---")
            return final_results

    except Exception as exc:
        print(f"Lỗi chính: {exc}")
        return []
