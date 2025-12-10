# Copyright 2025 HouHackathon-CQP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
import re
from typing import Any, Iterable

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import LocationType

DEFAULT_GEOMETRY = {"type": "LineString", "coordinates": []}
GROQ_CANONICAL_URL = "https://api.groq.com/openai/v1/chat/completions"
OSM_USER_AGENT = "GreenMapBackend/1.0"

LOCATION_TYPE_ALIASES: dict[str, LocationType] = {
    "PUBLIC_PARK": LocationType.PUBLIC_PARK,
    "CONG_VIEN": LocationType.PUBLIC_PARK,
    "CONG_VIEN_XANH": LocationType.PUBLIC_PARK,
    "PARK": LocationType.PUBLIC_PARK,
    "CHARGING_STATION": LocationType.CHARGING_STATION,
    "TRAM_SAC": LocationType.CHARGING_STATION,
    "SAC_XE_DIEN": LocationType.CHARGING_STATION,
    "TOURIST_ATTRACTION": LocationType.TOURIST_ATTRACTION,
    "DIEM_DU_LICH": LocationType.TOURIST_ATTRACTION,
    "THAM_QUAN": LocationType.TOURIST_ATTRACTION,
    "BICYCLE_RENTAL": LocationType.BICYCLE_RENTAL,
    "THUE_XE_DAP": LocationType.BICYCLE_RENTAL,
    "TRAM_XE_DAP": LocationType.BICYCLE_RENTAL,
}


def _extract_json_block(raw: str) -> dict[str, Any]:
    if not raw:
        return {}

    cleaned = raw.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        cleaned = "".join(parts[1:-1]) or "".join(parts[1:]) or cleaned
        cleaned = cleaned.replace("json", "", 1).strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    brace_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except Exception:
            return {}
    return {}


def _build_groq_url(base_url: str | None) -> str:
    """
    Chấp nhận nhiều dạng cấu hình:
    - https://api.groq.com
    - https://api.groq.com/openai/v1
    - https://api.groq.com/openai/v1/chat/completions
    """
    if not base_url:
        return GROQ_CANONICAL_URL

    cleaned = base_url.strip().rstrip("/")
    if cleaned.endswith("/chat/completions"):
        return cleaned
    if cleaned.endswith("/openai/v1") or cleaned.endswith("/v1"):
        return f"{cleaned}/chat/completions"
    if cleaned.endswith("/openai"):
        return f"{cleaned}/v1/chat/completions"
    return f"{cleaned}/openai/v1/chat/completions"


def _build_nominatim_url(base_url: str | None) -> str:
    """
    Đảm bảo URL trỏ tới endpoint /search của Nominatim.
    """
    default = "https://nominatim.openstreetmap.org/search"
    if not base_url:
        return default

    cleaned = base_url.strip().rstrip("/")
    if cleaned.lower().endswith("/search"):
        return cleaned
    return f"{cleaned}/search"


async def _geocode_osm(query: str) -> dict[str, Any] | None:
    """
    Tìm tọa độ bằng OpenStreetMap Nominatim.
    """
    if not query:
        return None

    url = _build_nominatim_url(settings.osm_nominatim_url)
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 0,
    }
    headers = {"User-Agent": OSM_USER_AGENT}

    async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Nominatim trả về lỗi {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Nominatim không phản hồi: {exc}") from exc

    if not data:
        return None

    best = data[0]
    try:
        return {
            "lat": float(best.get("lat")),
            "lon": float(best.get("lon")),
            "name": best.get("display_name") or query,
        }
    except Exception:
        return None


async def _call_groq_for_intent(question: str, model_override: str | None = None) -> dict[str, Any]:
    if not settings.groq_api_key:
        raise RuntimeError("Thiếu GROQ_API_KEY")

    model = model_override or settings.groq_model or "mixtral-8x7b-32768"
    url = _build_groq_url(settings.groq_api_base)
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }
    system_prompt = (
        "Bạn là agent chỉ đường tiếng Việt. Đọc câu hỏi của người dùng và trích xuất ý định di chuyển, "
        "POI liên quan. Chỉ trả lời JSON đúng cấu trúc sau, không thêm giải thích:\n"
        "{\n"
        '  \"start\": \"Tên điểm xuất phát (chuỗi rỗng nếu không chắc)\",\n'
        '  \"destination\": \"Tên điểm đến (chuỗi rỗng nếu không chắc)\",\n'
        '  \"constraints\": [ {\"type\": \"PUBLIC_PARK|CHARGING_STATION|TOURIST_ATTRACTION|BICYCLE_RENTAL|ANY\", \"count\": 1} ]\n'
        "}\n"
        "- Chuẩn hóa loại POI: công viên -> PUBLIC_PARK; trạm sạc/sạc xe điện -> CHARGING_STATION; "
        "điểm du lịch/tham quan -> TOURIST_ATTRACTION; thuê xe đạp/trạm xe đạp -> BICYCLE_RENTAL; không xác định -> ANY.\n"
        "- Giữ nguyên ngôn ngữ tiếng Việt cho start/destination."
    )
    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Groq trả về lỗi {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc

    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message", {})
    text_content = message.get("content")
    return _extract_json_block(text_content)


def _normalize_location_type(raw: Any) -> LocationType | None:
    if raw is None:
        return None
    key = str(raw).strip().upper().replace(" ", "_")
    if key in {"", "ANY", "NONE"}:
        return None
    return LOCATION_TYPE_ALIASES.get(key)


def _normalize_constraints(intent: dict[str, Any]) -> list[dict[str, Any]]:
    raw_constraints = intent.get("constraints") if isinstance(intent, dict) else []
    if not isinstance(raw_constraints, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in raw_constraints:
        if not isinstance(item, dict):
            continue
        poi_type = _normalize_location_type(item.get("type"))
        if not poi_type:
            continue
        try:
            count = int(item.get("count", 1))
        except Exception:
            count = 1
        count = max(1, min(count, 5))
        normalized.append({"type": poi_type, "count": count})
    return normalized


async def _find_location_by_name(db: AsyncSession, keyword: str) -> dict[str, Any] | None:
    if not keyword:
        return None

    query = text(
        """
        SELECT id, name, ST_X(location::geometry) AS lon, ST_Y(location::geometry) AS lat, location_type
        FROM green_locations
        WHERE name ILIKE :pattern
        ORDER BY id DESC
        LIMIT 1;
        """
    )
    result = await db.execute(query, {"pattern": f"%{keyword}%"})
    row = result.mappings().first()
    if not row:
        return None

    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "lat": row.get("lat"),
        "lon": row.get("lon"),
        "type": row.get("location_type"),
    }


async def _get_nearest_pois(
    db: AsyncSession,
    poi_type: LocationType,
    start_lat: float,
    start_lon: float,
    count: int,
) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT id, name, ST_X(location::geometry) AS lon, ST_Y(location::geometry) AS lat, location_type,
               ST_Distance(
                   location::geography,
                   ST_SetSRID(ST_MakePoint(:lon_start, :lat_start), 4326)::geography
               ) AS distance_m
        FROM green_locations
        WHERE location_type = :poi_type
        ORDER BY distance_m
        LIMIT :limit;
        """
    )
    result = await db.execute(
        query,
        {
            "poi_type": poi_type.value,
            "lon_start": start_lon,
            "lat_start": start_lat,
            "limit": count,
        },
    )

    pois: list[dict[str, Any]] = []
    for row in result.mappings():
        pois.append(
            {
                "id": row.get("id"),
                "name": row.get("name"),
                "lat": row.get("lat"),
                "lon": row.get("lon"),
                "type": row.get("location_type") or poi_type.value,
                "distance": row.get("distance_m"),
            }
        )
    return pois


async def _call_osrm(coordinates: Iterable[tuple[float, float]]) -> dict[str, Any]:
    coord_list = list(coordinates)
    if len(coord_list) < 2:
        raise RuntimeError("Thiếu tọa độ để tính route.")

    coord_text = ";".join(f"{lon},{lat}" for lon, lat in coord_list)
    url = f"{settings.osrm_base_url.rstrip('/')}/route/v1/driving/{coord_text}"
    params = {"overview": "full", "geometries": "geojson"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    routes = data.get("routes") or []
    if not routes:
        raise RuntimeError("OSRM không trả về kết quả.")

    best = routes[0]
    geometry = best.get("geometry") or DEFAULT_GEOMETRY
    return {
        "distance": float(best.get("distance") or 0),
        "duration": float(best.get("duration") or 0),
        "geometry": geometry,
    }


def _build_summary(
    start_name: str,
    dest_name: str,
    via_pois: list[dict[str, Any]],
    route: dict[str, Any],
    note: str = "",
) -> str:
    distance_km = round((route.get("distance") or 0) / 1000, 2)
    duration_min = round((route.get("duration") or 0) / 60)
    chain = " → ".join([start_name, *[p.get("name", "") for p in via_pois], dest_name])

    poi_clause = ""
    if via_pois:
        poi_clause = f" Qua các điểm: {', '.join(p.get('name', '') for p in via_pois)}."

    return (
        f"Tuyến đường {chain}. Tổng quãng đường {distance_km} km, thời gian dự kiến {duration_min} phút."
        f"{poi_clause}{note}"
    )


async def generate_ai_route(
    db: AsyncSession,
    question: str,
    current_lat: float,
    current_lon: float,
    destination_lat: float | None = None,
    destination_lon: float | None = None,
    model_override: str | None = None,
) -> dict[str, Any]:
    intent = await _call_groq_for_intent(question, model_override)
    start_label = (intent.get("start") or "").strip()
    dest_label = (intent.get("destination") or "").strip()
    constraints = _normalize_constraints(intent)

    start_match = await _find_location_by_name(db, start_label) if start_label else None
    dest_match = await _find_location_by_name(db, dest_label) if dest_label else None

    start_point = {
        "name": (start_match or {}).get("name") or start_label or "Điểm xuất phát",
        "lat": current_lat if current_lat is not None else (start_match or {}).get("lat"),
        "lon": current_lon if current_lon is not None else (start_match or {}).get("lon"),
    }
    dest_point = {
        "name": (dest_match or {}).get("name") or dest_label or "Điểm đến",
        "lat": destination_lat if destination_lat is not None else (dest_match or {}).get("lat"),
        "lon": destination_lon if destination_lon is not None else (dest_match or {}).get("lon"),
    }

    if (dest_point["lat"] is None or dest_point["lon"] is None) and dest_label:
        osm_place = await _geocode_osm(dest_label)
        if osm_place:
            dest_point["lat"] = osm_place["lat"]
            dest_point["lon"] = osm_place["lon"]
            dest_point["name"] = osm_place.get("name") or dest_point["name"]

    if start_point["lat"] is None or start_point["lon"] is None:
        raise RuntimeError("Thiếu tọa độ điểm xuất phát.")
    if dest_point["lat"] is None or dest_point["lon"] is None:
        raise RuntimeError("Thiếu tọa độ điểm đến. Không tìm được tọa độ từ câu hỏi.")

    via_pois: list[dict[str, Any]] = []
    for constraint in constraints:
        pois = await _get_nearest_pois(
            db=db,
            poi_type=constraint["type"],
            start_lat=start_point["lat"],
            start_lon=start_point["lon"],
            count=constraint["count"],
        )
        via_pois.extend(pois)

    if via_pois:
        via_pois.sort(key=lambda p: p.get("distance") or 0)

    osrm_coords: list[tuple[float, float]] = [
        (float(start_point["lon"]), float(start_point["lat"]))
    ]
    osrm_coords.extend(
        (float(p["lon"]), float(p["lat"])) for p in via_pois
    )
    osrm_coords.append((float(dest_point["lon"]), float(dest_point["lat"])))

    note = ""
    try:
        route = await _call_osrm(osrm_coords)
    except Exception:
        if via_pois:
            route = await _call_osrm(
                [
                    (float(start_point["lon"]), float(start_point["lat"])),
                    (float(dest_point["lon"]), float(dest_point["lat"])),
                ]
            )
            via_pois = []
            note = " (OSRM gặp lỗi khi chèn POI, đã fallback tuyến thẳng.)"
        else:
            raise

    summary = _build_summary(
        start_name=start_point["name"],
        dest_name=dest_point["name"],
        via_pois=via_pois,
        route=route,
        note=note,
    )

    return {
        "start": start_point,
        "destination": dest_point,
        "via_pois": via_pois,
        "route": route | {"geometry": route.get("geometry") or DEFAULT_GEOMETRY},
        "summary": summary,
    }
