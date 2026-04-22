from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def register_and_login(email: str, password: str) -> str:
    client.post("/api/v1/auth/register", json={"email": email, "password": password, "name": "User"})
    resp = client.post("/api/v1/auth/login", json={"account": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_dashboard_me_with_body_composition_and_assessment():
    email = f"dash-{uuid4().hex[:8]}@example.com"
    password = "Passw0rd123"
    token = register_and_login(email, password)

    headers = {"Authorization": f"Bearer {token}"}

    assess = client.post("/api/v1/assessments", json={"goal": "减脂"}, headers=headers)
    assert assess.status_code == 200
    assessment_id = assess.json()["data"]["id"]

    complete = client.post(
        f"/api/v1/assessments/{assessment_id}/complete",
        json={"risk_level": "low", "report_summary": {"notes": "保持规律训练"}},
        headers=headers,
    )
    assert complete.status_code == 200

    t1 = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 2, 1, 8, 0, tzinfo=timezone.utc)

    r1 = client.post(
        "/api/v1/body-composition",
        json={"measured_at": t1.isoformat(), "weight": 80.0, "body_fat_rate": 20.0},
        headers=headers,
    )
    assert r1.status_code == 200
    id1 = r1.json()["data"]["id"]

    r2 = client.post(
        "/api/v1/body-composition",
        json={"measured_at": t2.isoformat(), "weight": 78.0, "body_fat_rate": 19.5},
        headers=headers,
    )
    assert r2.status_code == 200
    id2 = r2.json()["data"]["id"]

    trend = client.get("/api/v1/body-composition/trend?metric=weight", headers=headers)
    assert trend.status_code == 200
    assert len(trend.json()["data"]) >= 2

    compare = client.get(f"/api/v1/body-composition/compare?a={id1}&b={id2}", headers=headers)
    assert compare.status_code == 200
    assert compare.json()["data"]["diff"]["weight"] == -2.0

    dashboard = client.get("/api/v1/dashboard/me", headers=headers)
    assert dashboard.status_code == 200
    data = dashboard.json()["data"]
    assert data["me"]["email"] == email
    assert data["latest_assessment"]["id"] == assessment_id
    assert data["body_composition_summary"]["latest"]["id"] == id2


def test_dashboard_behavior_alerts():
    email = f"dash-alert-{uuid4().hex[:8]}@example.com"
    password = "Passw0rd123"
    token = register_and_login(email, password)
    headers = {"Authorization": f"Bearer {token}"}

    today = datetime.now(timezone.utc).date()
    # 构造体脂率连续2周上升（最近三周均值：18.0 -> 19.0 -> 20.0）
    client.put(
        f"/api/v1/daily-metrics/{(today - timedelta(days=20)).isoformat()}",
        json={"body_fat_rate": 18.0, "weight": 75.0, "bmi": 24.0},
        headers=headers,
    )
    client.put(
        f"/api/v1/daily-metrics/{(today - timedelta(days=13)).isoformat()}",
        json={"body_fat_rate": 19.0, "weight": 75.5, "bmi": 24.2},
        headers=headers,
    )
    client.put(
        f"/api/v1/daily-metrics/{(today - timedelta(days=6)).isoformat()}",
        json={"body_fat_rate": 20.0, "weight": 76.0, "bmi": 24.4},
        headers=headers,
    )

    # 训练记录都在3天之前，触发“3天未训练”
    client.put(
        f"/api/v1/daily-workout/{(today - timedelta(days=5)).isoformat()}",
        json={
            "plan_title": "下肢训练",
            "items": [{"name": "深蹲", "sets": 4, "reps": 10, "duration_minutes": 20}],
            "duration_minutes": 45,
            "is_completed": True,
            "notes": None,
        },
        headers=headers,
    )

    dashboard = client.get("/api/v1/dashboard/me", headers=headers)
    assert dashboard.status_code == 200
    alerts = dashboard.json()["data"]["growth_analytics"]["alerts"]
    messages = [a["message"] for a in alerts]
    assert any("3天未训练" in m for m in messages)
    assert any("体脂率连续2周上升" in m for m in messages)
