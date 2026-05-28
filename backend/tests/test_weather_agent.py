from unittest.mock import AsyncMock, patch

import pytest

from app.agents.weather_agent import run_weather_agent


def make_open_meteo_response():
    return {
        "temperature": 62,
        "temperature_unit": "F",
        "short_forecast": "Partly cloudy",
        "detailed_forecast": None,
        "wind_speed": "8 mph",
        "wind_direction": "SW",
        "is_daytime": True,
        "precip_probability": 20,
    }


@pytest.mark.asyncio
async def test_weather_with_coords():
    mock_result = make_open_meteo_response()

    with patch(
        "app.agents.weather_agent.fetch_current_weather",
        new=AsyncMock(return_value=mock_result),
    ):
        result = await run_weather_agent(35.5, -82.5)

    assert result is not None
    assert result["temperature"] == 62
    assert result["temperature_unit"] == "F"
    assert result["short_forecast"] == "Partly cloudy"
    assert result["wind_speed"] == "8 mph"


@pytest.mark.asyncio
async def test_weather_no_coords():
    result = await run_weather_agent(None, None)
    assert result is None


@pytest.mark.asyncio
async def test_weather_api_failure_graceful():
    with patch(
        "app.agents.weather_agent.fetch_current_weather",
        new=AsyncMock(return_value=None),
    ):
        result = await run_weather_agent(35.5, -82.5)

    assert result is None
