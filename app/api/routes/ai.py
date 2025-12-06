from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.services.ai_insights import generate_ai_insight


Provider = Literal["gemini", "groq", "auto"]
router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/weather-insights")
async def get_ai_weather_insights(
    lat: float = Query(21.0285, description="Vĩ độ (mặc định: Hà Nội)"),
    lon: float = Query(105.8542, description="Kinh độ (mặc định: Hà Nội)"),
    provider: Provider = Query("auto", description="Chọn provider AI: gemini, groq hoặc auto để thử lần lượt."),
    model: str | None = Query(
        None,
        description="Ghi đè model nếu cần (ví dụ: gemini-1.5-pro). Bỏ trống để dùng mặc định.",
    ),
):
    """
    Phân tích thời tiết 24h/7 ngày + AQI bằng AI (Gemini/Groq) và trả về lời khuyên.
    """
    try:
        return await generate_ai_insight(
            lat=lat,
            lon=lon,
            provider=provider,
            model_override=model,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc
