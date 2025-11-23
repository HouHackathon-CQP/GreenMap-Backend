from fastapi import APIRouter, Query # <-- 1. Import Query
import httpx
from app.core.config import settings

router = APIRouter(prefix="/aqi", tags=["aqi"])

@router.get("/hanoi")
async def get_live_hanoi_aqi(limit: int = Query(100, ge=1, le=1000, description="Số lượng trạm tối đa")):
    """
    Lấy dữ liệu AQI từ Orion-LD.
    Hỗ trợ ?limit=10 để giới hạn kết quả.
    """
    orion_url = f"{settings.orion_broker_url}/ngsi-ld/v1/entities"
    full_type = f"{settings.aqi_service_path}/AirQualityObserved"
    params = {
        "type": full_type,
        "limit": limit
    }
    
    headers = {
        "Accept": "application/ld+json",
        "Link": '<https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld>; rel="http://www.w3.org/ns/ldp#context"; type="application/ld+json"'
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(orion_url, params=params, headers=headers)
            response.raise_for_status()
            
            orion_data = response.json()
            
            return {
                "source": "Orion-LD Context Broker",
                "limit_requested": limit, 
                "count": len(orion_data),
                "data": orion_data,
            }
            
    except Exception as exc:
        return {
            "source": "Orion-LD (Error)",
            "error": str(exc),
            "hint": "Kiểm tra kết nối tới Orion-LD."
        }