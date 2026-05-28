import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user
from app.models.users import User
from app.schemas.weather import ForecastDay, PlanningWeather
from app.services.weather import fetch_7day_forecast, fetch_current_weather

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/forecast", response_model=list[ForecastDay])
async def get_forecast(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    user: User = Depends(get_current_user),
):
    try:
        periods = await fetch_7day_forecast(lat, lng)
    except Exception as e:
        logger.error("Forecast fetch error: %s: %s", type(e).__name__, e)
        raise HTTPException(status_code=502, detail="Unable to fetch forecast") from e

    if periods is None:
        logger.warning("Open-Meteo returned no data for (%s, %s)", lat, lng)
        raise HTTPException(status_code=502, detail="Unable to fetch forecast")
    return periods


@router.get("/planning", response_model=PlanningWeather)
async def get_planning_weather(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    user: User = Depends(get_current_user),
):
    try:
        current = await fetch_current_weather(lat, lng)
        forecast = await fetch_7day_forecast(lat, lng)
    except Exception as e:
        logger.error("Planning weather fetch error: %s: %s", type(e).__name__, e)
        raise HTTPException(status_code=502, detail="Unable to fetch weather data") from e

    if current is None or forecast is None:
        logger.warning("Open-Meteo returned incomplete data for (%s, %s)", lat, lng)
        raise HTTPException(status_code=502, detail="Unable to fetch weather data")

    return {
        "current": current,
        "forecast": forecast,
    }
