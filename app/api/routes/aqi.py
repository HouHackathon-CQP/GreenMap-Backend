import httpx
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/aqi", tags=["aqi"])


@router.get("/hanoi")
async def get_live_hanoi_aqi():
    orion_url = f"{settings.orion_broker_url}/ngsi-ld/v1/entities"
    params = {"type": "AirQualityObserved", "limit": 100}
    headers = {
        "Accept": "application/ld+json",
        'Link': '<https://raw.githubusercontent.com/smart-data-models/dataModel.Environment/master/context.jsonld>; rel="http://www.w3.org/ns/ldp#context"; type="application/ld+json"',
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(orion_url, params=params, headers=headers)
            response.raise_for_status()
            orion_data = response.json()
            return {
                "source": "Orion-LD Context Broker",
                "count": len(orion_data),
                "data": orion_data,
            }
    except Exception as exc:  # pylint: disable=broad-except
        return {
            "source": "Orion-LD (Error)",
            "error": str(exc),
            "hint": "Kiểm tra container 'greenmap-orion' hoặc header Link.",
        }
