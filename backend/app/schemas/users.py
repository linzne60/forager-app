import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import Location


class DietaryInfo(BaseModel):
    gluten_free: bool = False
    dairy_free: bool = False
    coconut_free: bool = False
    shellfish_free: bool = False
    nut_free: bool = False
    egg_free: bool = False
    vegan: bool = False
    other: list[str] = Field(default_factory=list)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(max_length=100)
    session_id: uuid.UUID | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str | None
    display_name: str
    oauth_provider: str
    default_location: Location | None = None
    dietary_info: DietaryInfo | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    display_name: str | None = None
    default_location: Location | None = None
    dietary_info: DietaryInfo | None = None
