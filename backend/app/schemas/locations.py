import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LocationCreate(BaseModel):
    label: str
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class LocationResponse(BaseModel):
    id: uuid.UUID
    label: str
    city: str | None = None
    state: str | None = None
    latitude: float
    longitude: float
    is_pinned: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
