from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.config import settings


def test_access_token_round_trip():
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"


def test_refresh_token_round_trip():
    token = create_refresh_token("user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"


def test_access_token_contains_expiry():
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert "exp" in payload


def test_access_token_type():
    token = create_access_token("user-123")
    payload = decode_token(token)
    assert payload["type"] == "access"


def test_refresh_token_type():
    token = create_refresh_token("user-123")
    payload = decode_token(token)
    assert payload["type"] == "refresh"


def test_expired_token_raises():
    expired = pyjwt.encode(
        {"sub": "user-123", "exp": datetime.now(UTC) - timedelta(seconds=1)},
        settings.secret_key,
        algorithm="HS256",
    )
    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_token(expired)


def test_invalid_token_raises():
    with pytest.raises(pyjwt.InvalidTokenError):
        decode_token("not.a.valid.token")


def test_tampered_token_raises():
    token = create_access_token("user-123")
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(pyjwt.InvalidTokenError):
        decode_token(tampered)
