from fastapi.testclient import TestClient
from uuid import uuid4

from app.db.session import Base, engine
from app.main import app

client = TestClient(app)


def test_auth_register_login_me_flow():
    Base.metadata.create_all(bind=engine)
    unique_email = f"test-auth-{uuid4().hex[:8]}@example.com"
    register_payload = {
        "email": unique_email,
        "password": "Passw0rd123",
    }
    register_resp = client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code in {200, 409}

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"account": unique_email, "password": "Passw0rd123"},
    )
    assert login_resp.status_code == 200
    access_token = login_resp.json()["access_token"]

    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == unique_email
    assert "name" in me_resp.json()
