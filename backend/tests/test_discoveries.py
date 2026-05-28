import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.models.discoveries import Discovery


@pytest.fixture
async def auth_token(client):
    """Register a user and return their token + user ID."""
    unique = uuid.uuid4().hex[:8]
    response = await client.post("/api/auth/register", json={
        "email": f"journal_{unique}@example.com",
        "password": "testpassword123",
        "display_name": "Journal Tester",
    })
    assert response.status_code == 201
    body = response.json()
    return body["access_token"], body["user"]["id"]


@pytest.fixture
def auth_headers(auth_token):
    token, _ = auth_token
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def seed_discoveries(auth_token, db):
    """Insert test discoveries directly via the DB session."""
    _, user_id = auth_token
    uid = uuid.UUID(user_id)

    now = datetime.now(UTC)
    records = [
        Discovery(
            user_id=uid,
            photo_url="/media/uploads/1.jpg",
            species_prediction={"common_name": "goldenrod", "confidence": 0.95},
            confidence_score=0.95,
            safety_verdict="safe",
            location={"city": "Asheville", "state": "NC"},
            user_notes="Found near the river",
            discovered_at=now - timedelta(days=5),
        ),
        Discovery(
            user_id=uid,
            photo_url="/media/uploads/2.jpg",
            species_prediction={"common_name": "poison_ivy", "confidence": 0.88},
            confidence_score=0.88,
            safety_verdict="danger",
            location={"city": "Boone", "state": "NC"},
            user_notes=None,
            discovered_at=now - timedelta(days=3),
        ),
        Discovery(
            user_id=uid,
            photo_url="/media/uploads/3.jpg",
            species_prediction={"common_name": "chanterelle", "confidence": 0.72},
            confidence_score=0.72,
            safety_verdict="caution",
            location={"city": "Gatlinburg", "state": "TN"},
            user_notes="Yellow mushroom on oak log",
            discovered_at=now - timedelta(days=1),
        ),
        Discovery(
            user_id=uid,
            photo_url="/media/uploads/4.jpg",
            species_prediction=None,
            confidence_score=0.30,
            safety_verdict="unknown",
            location=None,
            user_notes=None,
            discovered_at=now,
        ),
    ]

    for r in records:
        db.add(r)
    await db.commit()

    # Refresh to get generated IDs and timestamps
    for r in records:
        await db.refresh(r)

    return records


# --- Basic listing ---

async def test_list_discoveries_authenticated(client, auth_headers, seed_discoveries):
    response = await client.get("/api/discoveries", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 4
    # Ordered by discovered_at desc — newest first
    assert body[0]["species_prediction"] is None  # the unidentified one (most recent)


async def test_list_discoveries_unauthenticated(client):
    response = await client.get("/api/discoveries")
    assert response.status_code == 401


# --- Cursor pagination ---

async def test_cursor_pagination(client, auth_headers, seed_discoveries):
    # First page: get 2 items
    response = await client.get("/api/discoveries?limit=2", headers=auth_headers)
    assert response.status_code == 200
    page1 = response.json()
    assert len(page1) == 2

    # Second page: use discovered_at of last item as cursor
    cursor = page1[-1]["discovered_at"]
    response = await client.get(f"/api/discoveries?limit=2&cursor={cursor}", headers=auth_headers)
    assert response.status_code == 200
    page2 = response.json()
    assert len(page2) == 2

    # No overlap between pages
    page1_ids = {d["id"] for d in page1}
    page2_ids = {d["id"] for d in page2}
    assert page1_ids.isdisjoint(page2_ids)


# --- Text search ---

async def test_search_by_species_name(client, auth_headers, seed_discoveries):
    response = await client.get("/api/discoveries?q=goldenrod", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["species_prediction"]["common_name"] == "goldenrod"


async def test_search_by_location(client, auth_headers, seed_discoveries):
    response = await client.get("/api/discoveries?q=Asheville", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["location"]["city"] == "Asheville"


async def test_search_by_notes(client, auth_headers, seed_discoveries):
    response = await client.get("/api/discoveries?q=river", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert "river" in body[0]["user_notes"]


async def test_search_case_insensitive(client, auth_headers, seed_discoveries):
    response = await client.get("/api/discoveries?q=GOLDENROD", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_search_no_match(client, auth_headers, seed_discoveries):
    response = await client.get("/api/discoveries?q=nonexistent", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 0


# --- Safety filter ---

async def test_filter_safety_single(client, auth_headers, seed_discoveries):
    response = await client.get("/api/discoveries?safety=safe", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["safety_verdict"] == "safe"


async def test_filter_safety_multiple(client, auth_headers, seed_discoveries):
    response = await client.get("/api/discoveries?safety=safe,danger", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    verdicts = {d["safety_verdict"] for d in body}
    assert verdicts == {"safe", "danger"}


# --- Confidence filter ---

async def test_filter_confidence_min(client, auth_headers, seed_discoveries):
    response = await client.get("/api/discoveries?confidence_min=0.90", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["confidence_score"] == 0.95


async def test_filter_confidence_range(client, auth_headers, seed_discoveries):
    response = await client.get("/api/discoveries?confidence_min=0.70&confidence_max=0.90", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    for d in body:
        assert 0.70 <= d["confidence_score"] <= 0.90


# --- Date filter ---

async def test_filter_date_range(client, auth_headers, seed_discoveries):
    now = datetime.now(UTC)
    date_from = (now - timedelta(days=4)).isoformat()
    date_to = (now - timedelta(days=2)).isoformat()
    response = await client.get(
        "/api/discoveries",
        params={"date_from": date_from, "date_to": date_to},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["species_prediction"]["common_name"] == "poison_ivy"


# --- Combined filters ---

async def test_combined_search_and_safety(client, auth_headers, seed_discoveries):
    response = await client.get("/api/discoveries?q=NC&safety=safe", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["species_prediction"]["common_name"] == "goldenrod"
