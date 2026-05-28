import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SafetyVerdict = Literal["safe", "caution", "danger"]


class WeatherSnapshot(BaseModel):
    temperature: float
    temperature_unit: str                   # "F" or "C"
    short_forecast: str
    detailed_forecast: str | None = None
    wind_speed: str | None = None
    wind_direction: str | None = None
    precip_probability: int | None = None   # 0–100%
    is_daytime: bool | None = None


class SafetyDetails(BaseModel):
    confidence_tier: str | None = None                                                   
    candidates: list[dict[str, Any]] | None = None      
    safety_info: dict[str, Any] | None = None                          
    lookalike_findings: list[dict[str, Any]] | None = None
    protection_findings: list[dict[str, Any]] | None = None
    warning_message: str = "Consult a local expert before consumption."


# ML & Identification
# details may change based on api response
class SpeciesResult(BaseModel):
    common_name: str
    scientific_name: str | None = None
    kingdom: str | None = None
    category: str | None = None
    confidence: float = Field(ge=0, le=1)  # confidence score between 0 and 1


class NotableNutrient(BaseModel):
    nutrient: str
    amount: str
    percent_dv: int | None = None


class NutritionInfo(BaseModel):
    species: str
    common_name: str
    confidence: str
    source: str
    edible_parts: list[str] = []
    calories_per_100g: float | None = None
    protein_g: float | None = None
    fat_g: float | None = None
    carbs_g: float | None = None
    fiber_g: float | None = None
    notable_nutrients: list[NotableNutrient] = []
    notes: str | None = None


class DiscoveryUpdate(BaseModel):
    user_notes: str


class DiscoveryListItem(BaseModel):
    id: uuid.UUID
    photo_url: str | None
    species_prediction: dict[str, Any] | None = None
    confidence_score: float | None = None
    safety_verdict: str | None = None
    discovered_at: datetime | None = None
    location: dict[str, Any] | None = None
    user_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DiscoveryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    session_id: uuid.UUID | None
    photo_url: str | None
    heatmap_url: str | None = None
    discovered_at: datetime | None = None
    location: dict[str, Any] | None = None

    species_prediction: SpeciesResult | None = None
    all_predictions: list[SpeciesResult] | None = None
    safety_verdict: str | None = None
    safety_details: SafetyDetails | None = None
    nutrition_info: NutritionInfo | None = None
    weather_context: WeatherSnapshot | None = None
    user_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)