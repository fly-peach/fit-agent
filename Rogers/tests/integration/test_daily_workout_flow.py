from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import Base, engine
from app.main import app

client = TestClient(app)


def _auth_headers() -> dict[str, str]:
    Base.metadata.create_all(bind=engine)
    email = f"daily-workout-{uuid4().hex[:8]}@example.com"
    register_resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd123", "name": "workout-user"},
    )
    assert register_resp.status_code == 200
    login_resp = client.post("/api/v1/auth/login", json={"account": email, "password": "Passw0rd123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_daily_workout_upsert_and_list():
    headers = _auth_headers()
    today = date.today().isoformat()
    payload = {
        "plan_title": "上肢训练",
        "items": [{"name": "卧推", "sets": 4, "reps": 10, "duration_minutes": 20}],
        "duration_minutes": 45,
        "is_completed": False,
        "notes": "注意肩胛稳定",
    }
    upsert_resp = client.put(f"/api/v1/daily-workout/{today}", headers=headers, json=payload)
    assert upsert_resp.status_code == 200
    assert upsert_resp.json()["data"]["plan_title"] == "上肢训练"

    list_resp = client.get(f"/api/v1/daily-workout?from={today}&to={today}", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 1
