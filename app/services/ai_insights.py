from __future__ import annotations

from statistics import mean
from typing import Any, Literal

import httpx

from app.core.config import settings
from app.services import openaq
from app.services import weather as weather_service

Provider = Literal["gemini", "groq", "auto"]


def _safe_round(value: Any, digits: int = 1) -> Any:
    try:
        return round(float(value), digits)
    except Exception:
        return value


def _summarize_aqi(aqi_list: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Gom tóm tắt nhanh về AQI/PM2.5 để đưa vào prompt và trả ra API.
    """
    numeric_values = [
        float(item["value"])
        for item in aqi_list
        if isinstance(item, dict) and isinstance(item.get("value"), (int, float))
    ]

    stations = len(aqi_list)
    online = sum(1 for item in aqi_list if item.get("status") == "Online")

    if not numeric_values:
        return {
            "stations": stations,
            "online": online,
            "pm25_avg": None,
            "pm25_max": None,
            "pm25_min": None,
            "hint": "Không có giá trị đo PM2.5 hợp lệ",
        }

    max_item = max(
        (
            item
            for item in aqi_list
            if isinstance(item.get("value"), (int, float))
        ),
        key=lambda x: x["value"],
    )
    min_item = min(
        (
            item
            for item in aqi_list
            if isinstance(item.get("value"), (int, float))
        ),
        key=lambda x: x["value"],
    )

    return {
        "stations": stations,
        "online": online,
        "pm25_avg": _safe_round(mean(numeric_values), 1),
        "pm25_max": {
            "value": _safe_round(max_item["value"], 1),
            "station": max_item.get("station_name"),
        },
        "pm25_min": {
            "value": _safe_round(min_item["value"], 1),
            "station": min_item.get("station_name"),
        },
    }


def _top_aqi_stations(aqi_list: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    valid = [
        item for item in aqi_list
        if isinstance(item.get("value"), (int, float))
    ]
    sorted_items = sorted(valid, key=lambda x: x["value"], reverse=True)
    return sorted_items[:limit]


def _format_hourly_for_prompt(hourly: list[dict[str, Any]]) -> str:
    if not hourly:
        return "Không có dữ liệu 24h tới."

    # Lấy 12 mốc (mỗi 2 giờ) để prompt gọn hơn
    sampled = hourly[::2][:12] if len(hourly) > 12 else hourly
    lines = []
    for slot in sampled:
        time_str = slot.get("time")
        temp = _safe_round(slot.get("temp"))
        rain = slot.get("rain_prob")
        desc = slot.get("desc")
        lines.append(f"{time_str}: {temp}°C, mưa {rain}%, {desc}")
    return "\n".join(lines)


def _format_daily_for_prompt(daily: list[dict[str, Any]]) -> str:
    if not daily:
        return "Không có dữ liệu 7 ngày."

    lines = []
    for day in daily:
        date = day.get("date")
        tmax = _safe_round(day.get("temp_max"))
        tmin = _safe_round(day.get("temp_min"))
        desc = day.get("desc")
        lines.append(f"{date}: cao {tmax}°C, thấp {tmin}°C, {desc}")
    return "\n".join(lines)


def _build_prompt(
        weather_data: dict[str, Any],
        aqi_summary: dict[str, Any],
        lat: float,
        lon: float,
) -> str:
    current = weather_data.get("current", {})
    hourly = weather_data.get("hourly_24h", [])
    daily = weather_data.get("daily_7days", [])

    hourly_block = _format_hourly_for_prompt(hourly)
    daily_block = _format_daily_for_prompt(daily)

    return (
        "Bạn là trợ lý khí hậu tiếng Việt. Hãy phân tích dữ liệu thời tiết (hiện tại, 24h tới, 7 ngày tới) "
        "và chất lượng không khí Hà Nội, sau đó đưa ra dự đoán và lời khuyên ngắn gọn, dễ hành động.\n"
        "- Giọng văn rõ ràng, tối đa 4 đoạn/bullet.\n"
        "- Nêu rủi ro mưa, nắng nóng, gió mạnh, ô nhiễm; nếu nhẹ hãy nói rõ là an toàn.\n"
        "- Đề xuất hành động: lịch trình ra ngoài, vận động, mang theo vật dụng, lưu ý cho người nhạy cảm.\n"
        f"Vị trí: lat {lat}, lon {lon}\n"
        f"Hiện tại: {current.get('temp')}°C, ẩm {current.get('humidity')}%, gió {current.get('wind_speed')} km/h, {current.get('desc')}\n"
        "Trong 24h tới (mỗi ~2h):\n"
        f"{hourly_block}\n"
        "7 ngày tới:\n"
        f"{daily_block}\n"
        "AQI/PM2.5:\n"
        f"- Trung bình: {aqi_summary.get('pm25_avg')} µg/m³ từ {aqi_summary.get('online')}/{aqi_summary.get('stations')} trạm online.\n"
        f"- Cao nhất: {aqi_summary.get('pm25_max')}, Thấp nhất: {aqi_summary.get('pm25_min')}.\n"
        "Hãy trả lời bằng tiếng Việt."
    )


async def _call_gemini(prompt: str, model_override: str | None = None) -> dict[str, Any]:
    if not settings.gemini_api_key:
        raise RuntimeError("Thiếu GEMINI_API_KEY")

    model = model_override or settings.gemini_model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    params = {"key": settings.gemini_api_key}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.post(url, params=params, json=payload)
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates") or []
    parts = (
        candidates[0]
        .get("content", {})
        .get("parts", [])
        if candidates
        else []
    )
    text = parts[0].get("text") if parts else None
    return {"provider": "gemini", "model": model, "text": text}

async def _call_groq(prompt: str, model_override: str | None = None) -> dict[str, Any]:
    if not settings.groq_api_key:
        raise RuntimeError("Thiếu GROQ_API_KEY")

    model = model_override or settings.groq_model
    url = settings.groq_api_base
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "temperature": 0.35,
        "messages": [
            {
                "role": "system",
                "content": "Bạn là trợ lý môi trường trả lời bằng tiếng Việt, ngắn gọn và hành động được.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message", {})
    text = message.get("content")
    return {"provider": "groq", "model": model, "text": text}

async def generate_ai_insight(
        lat: float,
        lon: float,
        provider: Provider = "auto",
        model_override: str | None = None,
) -> dict[str, Any]:
    """
    Thu thập dữ liệu (thời tiết + AQI), dựng prompt và gọi AI (Gemini/Groq).
    Trả về nội dung AI kèm ngữ cảnh thô để client có thể hiển thị.
    """
    weather_data = await weather_service.get_weather_forecast(lat, lon)
    if not weather_data:
        raise RuntimeError("Không lấy được dữ liệu thời tiết")

    # Thu hẹp số sensor và song song thấp để tránh 429 từ OpenAQ khi gọi AI
    aqi_raw = await openaq.get_hanoi_aqi(max_sensors=40, concurrency=4)
    aqi_summary = _summarize_aqi(aqi_raw)
    prompt = _build_prompt(weather_data, aqi_summary, lat, lon)

    providers: list[str] = []
    if provider == "auto":
        providers = ["gemini", "groq"]
    else:
        providers = [provider]

    errors: list[str] = []
    ai_result: dict[str, Any] | None = None

    for p in providers:
        try:
            if p == "gemini":
                ai_result = await _call_gemini(prompt, model_override)
            elif p == "groq":
                ai_result = await _call_groq(prompt, model_override)

            if ai_result and ai_result.get("text"):
                ai_result["provider"] = p
                break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{p}: {exc}")
            continue

    if not ai_result or not ai_result.get("text"):
        raise RuntimeError(f"Không thể gọi AI: {'; '.join(errors) or 'không rõ lỗi'}")

    return {
        "provider": ai_result.get("provider"),
        "model": ai_result.get("model"),
        "analysis": ai_result.get("text"),
        "context": {
            "location": {"lat": lat, "lon": lon},
            "weather": weather_data,
            "aqi": {
                "summary": aqi_summary,
                "top_stations": _top_aqi_stations(aqi_raw),
            },
        },
    }
