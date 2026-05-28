from pydantic import BaseModel


class CurrentWeather(BaseModel):
    temperature: int
    temperature_unit: str
    short_forecast: str
    wind_speed: str | None = None
    wind_direction: str | None = None
    precip_probability: int | None = None


class ForecastDay(BaseModel):
    name: str
    date: str
    temperature_high: int
    temperature_low: int
    temperature_unit: str
    short_forecast: str
    precip_probability: int | None = None


class PlanningWeather(BaseModel):
    current: CurrentWeather
    forecast: list[ForecastDay]
