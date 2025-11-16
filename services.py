import httpx
from fastapi import HTTPException
from config import OPENAQ_API_KEY
from datetime import datetime, timedelta, timezone  

OPENAQ_URL = "https://api.openaq.org/v3/locations" 

async def get_hanoi_aqi():
    """
    Gọi API OpenAQ V3, lấy CÁC TRẠM ĐO (locations) tại Hà Nội
    và LỌC ra những trạm đang hoạt động (cập nhật trong 24h qua).
    """
    
    params = {
        "coordinates": "21.0285,105.8542", # Tọa độ trung tâm Hà Nội
        "radius": 25000,                  # Bán kính 25km
        "parameter": "pm25",
        "limit": 500, 
        "sort": "desc",
        "order_by": "id"
    }

    headers = {"accept": "application/json"}
    
    if OPENAQ_API_KEY:
        headers["X-API-Key"] = OPENAQ_API_KEY
    else:
        print("CẢNH BÁO: Đang gọi OpenAQ mà không có API Key...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(OPENAQ_URL, params=params, headers=headers)
            response.raise_for_status() 
            
            data = response.json()
            all_stations = data.get("results", [])
            
            active_stations = []
            now = datetime.now(timezone.utc)
            one_day_ago = now - timedelta(days=1)
            
            for station in all_stations:
                datetime_last_obj = station.get("datetimeLast")
                
                if not datetime_last_obj:
                    continue
                
                last_update_str = datetime_last_obj.get("utc")
                
                if not last_update_str:
                    continue
                    
                try:
                    # Thay thế "Z" bằng "+00:00" để fromisoformat hiểu
                    if last_update_str.endswith("Z"):
                        last_update_str = last_update_str[:-1] + "+00:00"

                    last_update_time = datetime.fromisoformat(last_update_str)
                    
                    if last_update_time > one_day_ago:
                        active_stations.append(station)
                        
                except (ValueError, TypeError) as e:
                    print(f"Bỏ qua trạm {station.get('name')} do lỗi định dạng ngày: {e}")
                    continue
            
            return active_stations

    except httpx.HTTPStatusError as exc:
        print(f"Lỗi HTTP khi gọi OpenAQ V3: {exc.response.status_code} - {exc.response.text}")
        raise HTTPException(status_code=exc.response.status_code, detail=f"Lỗi từ OpenAQ: {exc.response.text}")
    except httpx.RequestError as exc:
        print(f"Lỗi kết nối OpenAQ: {exc}")
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu AQI từ OpenAQ.")
    except Exception as e:
        print(f"Lỗi xử lý dữ liệu AQI: {e}") 
        raise HTTPException(status_code=500, detail="Lỗi server nội bộ khi xử lý dữ liệu AQI.")