import asyncio
from datetime import datetime

import httpx
from fastapi import HTTPException

from app.core.config import settings

BASE_URL = "https://api.openaq.org/v3"


async def fetch_sensor_measurement(client: httpx.AsyncClient, sensor_id: int, headers: dict):
    meas_url = f"{BASE_URL}/sensors/{sensor_id}/measurements"
    meas_params = {"limit": 1, "order_by": "datetime", "sort": "desc"}

    try:
        meas_res = await client.get(meas_url, params=meas_params, headers=headers)
        if meas_res.status_code == 404:
            return None
        meas_res.raise_for_status()
        data = meas_res.json().get("results", [])
        if data:
            return data[0]
    except httpx.RequestError as exc:
        print(f"Lỗi khi gọi sensor {sensor_id}: {exc}")
        return None
    return None


async def get_hanoi_aqi():
    try:
        headers = {"accept": "application/json"}
        if settings.openaq_api_key:
            headers["X-API-Key"] = settings.openaq_api_key

        async with httpx.AsyncClient() as client:
            loc_url = f"{BASE_URL}/locations"
            loc_params = {
                "coordinates": "21.0285,105.8542",
                "radius": 25000,
                "parameter": "pm25",
                "limit": 200,
            }
            loc_res = await client.get(loc_url, params=loc_params, headers=headers)
            if loc_res.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="OpenAQ yêu cầu API key. Thêm OPENAQ_API_KEY vào .env hoặc biến môi trường.",
                )
            loc_res.raise_for_status()
            locations = loc_res.json().get("results", [])

            sensors_to_fetch = []
            for loc in locations:
                coords = loc.get("coordinates", {})
                provider_name = loc.get("provider", {}).get("name", "Không rõ")
                station_name = loc.get("name", "Trạm không tên")

                for sensor in loc.get("sensors", []):
                    param_info = sensor.get("parameter", {})
                    if param_info.get("name") == "pm25":
                        sensors_to_fetch.append(
                            {
                                "sensor_id": sensor["id"],
                                "station_name": station_name,
                                "coordinates": coords,
                                "provider_name": provider_name,
                            }
                        )

            if not sensors_to_fetch:
                raise HTTPException(
                    status_code=404,
                    detail="Không tìm thấy sensor pm25 tại Hà Nội (dùng tọa độ)",
                )

            unique_sensors_map = {s["sensor_id"]: s for s in sensors_to_fetch}
            unique_sensors_list = list(unique_sensors_map.values())

            tasks = [
                fetch_sensor_measurement(client, sensor_info["sensor_id"], headers)
                for sensor_info in unique_sensors_list
            ]
            measurements_results = await asyncio.gather(*tasks)

            final_results = []
            for i, measurement_data in enumerate(measurements_results):
                if measurement_data:
                    sensor_info = unique_sensors_list[i]
                    datetime_obj = measurement_data.get("date", {})
                    utc_time_str = datetime_obj.get("utc") if datetime_obj else None

                    try:
                        if utc_time_str and utc_time_str.endswith("Z"):
                            utc_time_str = utc_time_str[:-1] + "+00:00"
                        datetime.fromisoformat(utc_time_str)
                        final_results.append(
                            {
                                "sensor_id": sensor_info["sensor_id"],
                                "station_name": sensor_info["station_name"],
                                "provider_name": sensor_info["provider_name"],
                                "coordinates": sensor_info["coordinates"],
                                "value": measurement_data.get("value"),
                                "unit": measurement_data.get("unit"),
                                "datetime_utc": utc_time_str,
                            }
                        )
                    except (ValueError, TypeError, AttributeError):
                        final_results.append(
                            {
                                "sensor_id": sensor_info["sensor_id"],
                                "station_name": sensor_info["station_name"],
                                "provider_name": sensor_info["provider_name"],
                                "coordinates": sensor_info["coordinates"],
                                "value": measurement_data.get("value"),
                                "unit": measurement_data.get("unit"),
                                "datetime_utc": None,
                            }
                        )

            return final_results

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Lỗi từ OpenAQ: {exc.response.text}",
        ) from exc
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"Lỗi server nội bộ: {exc}") from exc
