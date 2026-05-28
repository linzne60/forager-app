import logging

import httpx

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

WIND_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def weather_description(code: int) -> str:
    return WMO_CODES.get(code, "Unknown")


def wind_direction_label(degrees: float) -> str:
    index = round(degrees / 45) % 8
    return WIND_DIRECTIONS[index]


async def fetch_current_weather(latitude: float, longitude: float) -> dict | None:
    """Fetch current weather conditions from Open-Meteo."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPEN_METEO_URL, params={
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "current": "temperature_2m,weather_code,precipitation_probability,wind_speed_10m,wind_direction_10m",
                "daily": "precipitation_probability_max",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "timezone": "auto",
                "forecast_days": 1,
            })
            response.raise_for_status()
            data = response.json()

        current = data["current"]
        daily = data.get("daily", {})
        precip = daily.get("precipitation_probability_max", [None])[0]

        return {
            "temperature": round(current["temperature_2m"]),
            "temperature_unit": "F",
            "short_forecast": weather_description(current["weather_code"]),
            "detailed_forecast": None,
            "wind_speed": f"{round(current['wind_speed_10m'])} mph",
            "wind_direction": wind_direction_label(current["wind_direction_10m"]),
            "is_daytime": True,
            "precip_probability": precip,
        }

    except Exception as e:
        logger.warning("Open-Meteo current weather error for (%s, %s): %s: %s", latitude, longitude, type(e).__name__, e)
        return None


async def fetch_7day_forecast(latitude: float, longitude: float) -> list[dict] | None:
    """Fetch 7-day daily forecast from Open-Meteo."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPEN_METEO_URL, params={
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
                "temperature_unit": "fahrenheit",
                "timezone": "auto",
                "forecast_days": 7,
            })
            response.raise_for_status()
            data = response.json()

        daily = data["daily"]
        results = []

        for i in range(len(daily["time"])):
            date = daily["time"][i]
            results.append({
                "name": _day_name(date),
                "date": date,
                "temperature_high": round(daily["temperature_2m_max"][i]),
                "temperature_low": round(daily["temperature_2m_min"][i]),
                "temperature_unit": "F",
                "short_forecast": weather_description(daily["weather_code"][i]),
                "precip_probability": daily["precipitation_probability_max"][i],
            })

        return results

    except Exception as e:
        logger.warning("Open-Meteo forecast error for (%s, %s): %s: %s", latitude, longitude, type(e).__name__, e)
        return None


def _day_name(date_str: str) -> str:
    from datetime import date, timedelta

    d = date.fromisoformat(date_str)
    today = date.today()

    if d == today:
        return "Today"
    if d == today + timedelta(days=1):
        return "Tomorrow"
    return d.strftime("%A")
