import logging

from app.services.weather import fetch_current_weather

logger = logging.getLogger(__name__)


async def run_weather_agent(latitude: float, longitude: float) -> dict | None:

    if latitude is None or longitude is None:
        return None

    result = await fetch_current_weather(latitude, longitude)

    if result is None:
        logger.warning("Weather fetch failed for (%s, %s)", latitude, longitude)

    return result
