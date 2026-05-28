from pydantic import BaseModel


class Location(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    city: str | None = None
    state: str | None = None
