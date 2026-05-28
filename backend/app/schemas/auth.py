import uuid

from pydantic import BaseModel, EmailStr

from app.schemas.users import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    session_id: uuid.UUID | None = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
