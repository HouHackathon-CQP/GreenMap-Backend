import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def get_weather_description(code: int) -> str:
    """Chuyển mã WMO sang tiếng Việt"""
    wmo_codes = {
        0: "Trời quang đãng", 1: "Có mây rải rác", 2: "Nhiều mây", 3: "Âm u",
        45: "Sương mù", 48: "Sương muối", 
        51: "Mưa phùn nhẹ", 53: "Mưa phùn vừa", 55: "Mưa phùn dày",
        61: "Mưa nhỏ", 63: "Mưa vừa", 65: "Mưa to",
        80: "Mưa rào nhẹ", 81: "Mưa rào vừa", 82: "Mưa rào rất to",
        95: "Dông bão", 96: "Dông kèm mưa đá"
    }
    return wmo_codes.get(code, "Không xác định")

async def get_weather_forecast(lat: float, lon: float):
    """
    Lấy thời tiết hiện tại + Dự báo 24h + Dự báo 7 ngày.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "Asia/Bangkok",
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "hourly": "temperature_2m,weather_code,precipitation_probability",
        "forecast_days": 7,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,sunrise,sunset"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPEN_METEO_URL, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # --- Xử lý hiện tại ---
            current = data.get("current", {})
            result_current = {
                "temp": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "desc": get_weather_description(current.get("weather_code")),
                "time": current.get("time")
            }

            # --- Xử lý 24h tới (Hourly) ---
            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            temps = hourly.get("temperature_2m", [])
            codes = hourly.get("weather_code", [])
            probs = hourly.get("precipitation_probability", [])
            result_24h = []
            current_api_time = current.get("time") 
            
            start_index = 0
            if current_api_time:
                for i, t in enumerate(times):
                    if t >= current_api_time:
                        start_index = i
                        break
            
            for i in range(start_index, start_index + 24):
                if i < len(times):
                    result_24h.append({
                        "time": times[i],
                        "temp": temps[i],
                        "rain_prob": probs[i],
                        "desc": get_weather_description(codes[i])
                    })
            # --- Xử lý 7 ngày tới (Daily) ---   
            daily = data.get("daily", {})
            d_times = daily.get("time", [])
            d_max = daily.get("temperature_2m_max", [])
            d_min = daily.get("temperature_2m_min", [])
            d_codes = daily.get("weather_code", [])
            
            result_7days = []
            for i in range(len(d_times)):
                result_7days.append({
                    "date": d_times[i],
                    "temp_max": d_max[i],
                    "temp_min": d_min[i],
                    "desc": get_weather_description(d_codes[i])
                })

            return {
                "current": result_current,
                "hourly_24h": result_24h,
                "daily_7days": result_7days
            }

        except Exception as e:
            print(f"❌ [Weather Service] Lỗi: {e}")
            return None

async def get_weather_by_coords(lat: float, lon: float):
    return await get_weather_forecast(lat, lon)