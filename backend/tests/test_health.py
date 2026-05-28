async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "welcome to forager!"


async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_ready(client):
    response = await client.get("/api/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


async def test_health_db(client):
    response = await client.get("/api/health/db")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
