import uuid
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
async def auth_token(client):
    unique = uuid.uuid4().hex[:8]
    response = await client.post("/api/auth/register", json={
        "email": f"loc_{unique}@example.com",
        "password": "testpassword123",
        "display_name": "Location Tester",
    })
    assert response.status_code == 201
    body = response.json()
    return body["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_location():
    return {
        "label": "Blue Ridge Parkway",
        "city": "Asheville",
        "state": "NC",
        "latitude": 35.5951,
        "longitude": -82.5515,
    }


# --- CRUD ---

async def test_create_location(client, auth_headers, sample_location):
    response = await client.post("/api/locations", json=sample_location, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["label"] == "Blue Ridge Parkway"
    assert body["city"] == "Asheville"
    assert body["latitude"] == 35.5951
    assert body["is_pinned"] is False


async def test_list_locations_empty(client, auth_headers):
    response = await client.get("/api/locations", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_locations(client, auth_headers, sample_location):
    await client.post("/api/locations", json=sample_location, headers=auth_headers)
    response = await client.get("/api/locations", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_delete_location(client, auth_headers, sample_location):
    create = await client.post("/api/locations", json=sample_location, headers=auth_headers)
    loc_id = create.json()["id"]

    response = await client.delete(f"/api/locations/{loc_id}", headers=auth_headers)
    assert response.status_code == 204

    listing = await client.get("/api/locations", headers=auth_headers)
    assert len(listing.json()) == 0


async def test_delete_nonexistent(client, auth_headers):
    fake_id = uuid.uuid4()
    response = await client.delete(f"/api/locations/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


# --- Pin ---

async def test_pin_location(client, auth_headers, sample_location):
    create = await client.post("/api/locations", json=sample_location, headers=auth_headers)
    loc_id = create.json()["id"]

    response = await client.patch(f"/api/locations/{loc_id}/pin", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_pinned"] is True


async def test_pin_unpins_previous(client, auth_headers):
    loc1 = await client.post("/api/locations", json={
        "label": "Spot A", "latitude": 35.0, "longitude": -82.0,
    }, headers=auth_headers)
    loc2 = await client.post("/api/locations", json={
        "label": "Spot B", "latitude": 36.0, "longitude": -83.0,
    }, headers=auth_headers)

    # Pin first
    await client.patch(f"/api/locations/{loc1.json()['id']}/pin", headers=auth_headers)
    # Pin second — should unpin first
    await client.patch(f"/api/locations/{loc2.json()['id']}/pin", headers=auth_headers)

    listing = await client.get("/api/locations", headers=auth_headers)
    locations = listing.json()
    pinned = [loc for loc in locations if loc["is_pinned"]]
    assert len(pinned) == 1
    assert pinned[0]["label"] == "Spot B"


async def test_pinned_location_listed_first(client, auth_headers):
    await client.post("/api/locations", json={
        "label": "Spot A", "latitude": 35.0, "longitude": -82.0,
    }, headers=auth_headers)
    loc2 = await client.post("/api/locations", json={
        "label": "Spot B", "latitude": 36.0, "longitude": -83.0,
    }, headers=auth_headers)

    await client.patch(f"/api/locations/{loc2.json()['id']}/pin", headers=auth_headers)

    listing = await client.get("/api/locations", headers=auth_headers)
    locations = listing.json()
    assert locations[0]["label"] == "Spot B"
    assert locations[0]["is_pinned"] is True


# --- Geocoding ---

async def test_create_location_with_city_state_geocodes(client, auth_headers):
    with patch(
        "app.api.routes.locations.geocode_location",
        new=AsyncMock(return_value=(35.5951, -82.5515)),
    ):
        response = await client.post("/api/locations", json={
            "label": "Downtown Asheville",
            "city": "Asheville",
            "state": "NC",
        }, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["latitude"] == 35.5951
    assert body["longitude"] == -82.5515


async def test_create_location_geocode_failure(client, auth_headers):
    with patch(
        "app.api.routes.locations.geocode_location",
        new=AsyncMock(return_value=None),
    ):
        response = await client.post("/api/locations", json={
            "label": "Nowhere",
            "city": "Faketown",
            "state": "XX",
        }, headers=auth_headers)

    assert response.status_code == 422


async def test_create_location_with_zip_code(client, auth_headers):
    with patch(
        "app.api.routes.locations.geocode_zip",
        new=AsyncMock(return_value=(35.2271, -80.8431)),
    ):
        response = await client.post("/api/locations", json={
            "label": "Charlotte Area",
            "zip_code": "28202",
        }, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["latitude"] == 35.2271
    assert body["longitude"] == -80.8431


async def test_create_location_zip_code_failure(client, auth_headers):
    with patch(
        "app.api.routes.locations.geocode_zip",
        new=AsyncMock(return_value=None),
    ):
        response = await client.post("/api/locations", json={
            "label": "Bad Zip",
            "zip_code": "00000",
        }, headers=auth_headers)

    assert response.status_code == 422


# --- Auth ---

async def test_locations_unauthenticated(client):
    response = await client.get("/api/locations")
    assert response.status_code == 401
