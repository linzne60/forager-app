import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from app.config import settings


@pytest.fixture
def user_payload():
    # unique email per test run to avoid conflicts with the dev DB
    unique = uuid.uuid4().hex[:8]
    return {
        "email": f"test_{unique}@example.com",
        "password": "testpassword123",
        "display_name": "Test User",
    }


@pytest.fixture
async def registered_user(client, user_payload):
    response = await client.post("/api/auth/register", json=user_payload)
    assert response.status_code == 201
    return {"payload": user_payload, "response": response.json(), "cookies": dict(response.cookies)}


# --- register ---

async def test_register_success(client, user_payload):
    response = await client.post("/api/auth/register", json=user_payload)
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == user_payload["email"]
    assert body["user"]["display_name"] == user_payload["display_name"]
    assert "hashed_password" not in body["user"]


async def test_register_duplicate_email(client, user_payload):
    await client.post("/api/auth/register", json=user_payload)
    response = await client.post("/api/auth/register", json=user_payload)
    assert response.status_code == 409


# --- login ---

async def test_login_success(client, registered_user):
    payload = registered_user["payload"]
    response = await client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["user"]["email"] == payload["email"]


async def test_login_wrong_password(client, registered_user):
    payload = registered_user["payload"]
    response = await client.post(
        "/api/auth/login",
        json={"email": payload["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_login_nonexistent_email(client):
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 401


# --- /me ---

async def test_me_authenticated(client, registered_user):
    token = registered_user["response"]["access_token"]
    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == registered_user["payload"]["email"]


async def test_me_unauthenticated(client):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


# --- refresh ---

async def test_refresh_success(client, registered_user):
    client.cookies.set("refresh_token", registered_user["cookies"]["refresh_token"])
    response = await client.post("/api/auth/refresh")
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_refresh_expired_token(client):
    expired = pyjwt.encode(
        {"sub": str(uuid.uuid4()), "exp": datetime.now(UTC) - timedelta(seconds=1)},
        settings.secret_key,
        algorithm="HS256",
    )
    client.cookies.set("refresh_token", expired)
    response = await client.post("/api/auth/refresh")
    assert response.status_code == 401


async def test_refresh_invalid_token(client):
    client.cookies.set("refresh_token", "not.a.valid.token")
    response = await client.post("/api/auth/refresh")
    assert response.status_code == 401
