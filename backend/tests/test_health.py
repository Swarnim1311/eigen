from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "eigen-backend"}


def test_root_points_to_health():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["health"] == "/health"
