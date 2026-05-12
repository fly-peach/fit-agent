"""pytest 配置：提供 TestClient fixture 和测试账户登录 token。"""
import sys
from pathlib import Path

# 确保 Rogers/ 目录在 Python path 中
_HERE = Path(__file__).resolve().parent
_ROGERS_ROOT = _HERE.parent  # Rogers/
if str(_ROGERS_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROGERS_ROOT))

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient fixture。"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def test_token(client):
    """使用测试账户登录获取 JWT token。"""
    resp = client.post(
        "/api/auth/login",
        json={"email": "user@test.com", "password": "password123"},
    )
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    data = resp.json()
    token = data.get("data", {}).get("token", "") or data.get("token", "")
    assert token, f"未获取到 token: {resp.json()}"
    return token


@pytest.fixture(scope="session")
def auth_header(test_token):
    """认证头 fixture。"""
    return {"authorization": f"Bearer {test_token}"}


@pytest.fixture(scope="session")
def auth_headers(test_token):
    """认证头 fixture（字典格式，用于 requests.get(headers=...)）。"""
    return {"Authorization": f"Bearer {test_token}"}
