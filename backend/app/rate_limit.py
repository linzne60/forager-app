from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.auth.jwt import decode_token
from app.config import settings


def _get_key(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            payload = decode_token(auth_header[7:])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(
    key_func=_get_key,
    storage_uri=settings.redis_url,
    default_limits=["60/minute"],
)
