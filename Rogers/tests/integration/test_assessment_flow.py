import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def get_token(client: TestClient, account: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"account": account, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_assessment_flow(client: TestClient):
    # 1. Create two members
    member_email = "member_ass3@test.com"
    other_email = "member_ass4@test.com"
    pwd = "password123"

    client.post("/api/v1/auth/register", json={"email": member_email, "password": pwd, "name": "Member A"})
    client.post("/api/v1/auth/register", json={"email": other_email, "password": pwd, "name": "Member B"})

    member_token = get_token(client, member_email, pwd)
    other_token = get_token(client, other_email, pwd)

    # 2. Member creates an assessment for self
    res = client.post(
        "/api/v1/assessments",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"goal": "增肌"}
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == "draft"
    assessment_id = data["id"]

    # 3. Owner reads the assessment
    res = client.get(
        f"/api/v1/assessments/{assessment_id}",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert res.status_code == 200
    assert res.json()["data"]["goal"] == "增肌"

    # 4. Another user cannot access this assessment
    res = client.get(
        f"/api/v1/assessments/{assessment_id}",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert res.status_code == 403

    # 5. Owner tries to read report (should fail since it's not completed)
    res = client.get(
        f"/api/v1/assessments/{assessment_id}/report",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert res.status_code == 400

    # 6. Owner completes the assessment
    report_payload = {
        "risk_level": "medium",
        "report_summary": {"note": "需要注意膝盖"}
    }
    res = client.post(
        f"/api/v1/assessments/{assessment_id}/complete",
        headers={"Authorization": f"Bearer {member_token}"},
        json=report_payload
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "completed"

    # 7. Owner reads report
    res = client.get(
        f"/api/v1/assessments/{assessment_id}/report",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert res.status_code == 200
    report_data = res.json()["data"]
    assert report_data["risk_level"] == "medium"
    assert report_data["report_summary"]["note"] == "需要注意膝盖"
