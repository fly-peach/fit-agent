from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import Base, engine
from app.main import app

client = TestClient(app)


def _auth_headers() -> dict[str, str]:
    Base.metadata.create_all(bind=engine)
    email = f"daily-metrics-{uuid4().hex[:8]}@example.com"
    register_resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd123", "name": "metrics-user"},
    )
    assert register_resp.status_code == 200
    login_resp = client.post("/api/v1/auth/login", json={"account": email, "password": "Passw0rd123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_daily_metrics_upsert_and_list():
    headers = _auth_headers()
    today = date.today().isoformat()

    upsert_resp = client.put(
        f"/api/v1/daily-metrics/{today}",
        headers=headers,
        json={"weight": 70.5, "body_fat_rate": 18.2, "bmi": 24.3},
    )
    assert upsert_resp.status_code == 200
    assert upsert_resp.json()["data"]["weight"] == 70.5

    upsert_resp2 = client.put(
        f"/api/v1/daily-metrics/{today}",
        headers=headers,
        json={"weight": 71.0, "body_fat_rate": 18.4, "bmi": 24.5},
    )
    assert upsert_resp2.status_code == 200
    assert upsert_resp2.json()["data"]["weight"] == 71.0

    list_resp = client.get(f"/api/v1/daily-metrics?from={today}&to={today}", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 1
