import uuid
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
async def auth_token(client):
    unique = uuid.uuid4().hex[:8]
    response = await client.post("/api/auth/register", json={
        "email": f"weather_{unique}@example.com",
        "password": "testpassword123",
        "display_name": "Weather Tester",
    })
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


def make_mock_forecast():
    return [
        {
            "name": "Today",
            "date": "2026-04-13",
            "temperature_high": 72,
            "temperature_low": 55,
            "temperature_unit": "F",
            "short_forecast": "Partly cloudy",
            "precip_probability": 10,
        },
        {
            "name": "Tuesday",
            "date": "2026-04-14",
            "temperature_high": 68,
            "temperature_low": 50,
            "temperature_unit": "F",
            "short_forecast": "Clear sky",
            "precip_probability": 0,
        },
    ]


async def test_forecast_success(client, auth_headers):
    mock_forecast = make_mock_forecast()

    with patch(
        "app.api.routes.weather.fetch_7day_forecast",
        new=AsyncMock(return_value=mock_forecast),
    ):
        response = await client.get(
            "/api/weather/forecast?lat=35.5951&lng=-82.5515",
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["name"] == "Today"
    assert body[0]["temperature_high"] == 72
    assert body[0]["temperature_low"] == 55
    assert body[0]["short_forecast"] == "Partly cloudy"
    assert body[0]["precip_probability"] == 10


async def test_forecast_api_failure(client, auth_headers):
    with patch(
        "app.api.routes.weather.fetch_7day_forecast",
        new=AsyncMock(return_value=None),
    ):
        response = await client.get(
            "/api/weather/forecast?lat=35.5951&lng=-82.5515",
            headers=auth_headers,
        )

    assert response.status_code == 502


async def test_forecast_missing_params(client, auth_headers):
    response = await client.get("/api/weather/forecast", headers=auth_headers)
    assert response.status_code == 422


async def test_forecast_unauthenticated(client):
    response = await client.get("/api/weather/forecast?lat=35.5&lng=-82.5")
    assert response.status_code == 401


# --- Planning endpoint ---

def make_mock_current():
    return {
        "temperature": 65,
        "temperature_unit": "F",
        "short_forecast": "Partly cloudy",
        "detailed_forecast": None,
        "wind_speed": "8 mph",
        "wind_direction": "SW",
        "is_daytime": True,
        "precip_probability": 20,
    }


async def test_planning_weather_success(client, auth_headers):
    with patch(
        "app.api.routes.weather.fetch_current_weather",
        new=AsyncMock(return_value=make_mock_current()),
    ), patch(
        "app.api.routes.weather.fetch_7day_forecast",
        new=AsyncMock(return_value=make_mock_forecast()),
    ):
        response = await client.get(
            "/api/weather/planning?lat=35.5951&lng=-82.5515",
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["current"]["temperature"] == 65
    assert body["current"]["wind_speed"] == "8 mph"
    assert len(body["forecast"]) == 2
    assert body["forecast"][0]["temperature_high"] == 72


async def test_planning_weather_partial_failure(client, auth_headers):
    with patch(
        "app.api.routes.weather.fetch_current_weather",
        new=AsyncMock(return_value=None),
    ), patch(
        "app.api.routes.weather.fetch_7day_forecast",
        new=AsyncMock(return_value=make_mock_forecast()),
    ):
        response = await client.get(
            "/api/weather/planning?lat=35.5951&lng=-82.5515",
            headers=auth_headers,
        )

    assert response.status_code == 502


async def test_planning_weather_unauthenticated(client):
    response = await client.get("/api/weather/planning?lat=35.5&lng=-82.5")
    assert response.status_code == 401
