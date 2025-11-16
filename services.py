import httpx
from fastapi import HTTPException
from config import OPENAQ_API_KEY  
OPENAQ_URL = "https://api.openaq.org/v3/locations" 

async def get_hanoi_aqi():
    """
    Gọi API OpenAQ V3, lấy CÁC TRẠM ĐO (locations) tại Hà Nội.
    Endpoint /latest của họ đang trả về 404, nên chúng ta dùng /locations.
    """
    
    # 2. THAM SỐ TRUY VẤN CHO /locations
    params = {
        "city": "Hanoi",
        "country_id": "VN",
        "parameter": "pm25",      # Lọc các trạm CÓ ĐO pm25
        "limit": 100,
        "sort": "desc",
        "order_by": "id" 
    }

    # Headers (để chứa API Key)
    headers = {
        "accept": "application/json"
    }
    
    if OPENAQ_API_KEY:
        headers["X-API-Key"] = OPENAQ_API_KEY
    else:
        print("CẢNH BÁO: Đang gọi OpenAQ mà không có API Key...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(OPENAQ_URL, params=params, headers=headers)
            
            response.raise_for_status() 
            
            data = response.json()
            return data.get("results", []) # Trả về danh sách CÁC TRẠM

    except httpx.HTTPStatusError as exc:
        print(f"Lỗi HTTP khi gọi OpenAQ V3: {exc.response.status_code} - {exc.response.text}")
        raise HTTPException(status_code=exc.response.status_code, detail=f"Lỗi từ OpenAQ: {exc.response.text}")
    except httpx.RequestError as exc:
        print(f"Lỗi kết nối OpenAQ: {exc}")
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu AQI từ OpenAQ.")
    except Exception as e:
        print(f"Lỗi xử lý dữ liệu AQI: {e}")
        raise HTTPException(status_code=500, detail="Lỗi server nội bộ khi xử lý dữ liệu AQI.")