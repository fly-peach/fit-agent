"""会话路由测试 — 对话 Session CRUD。"""
import pytest


class TestSessionsRouter:
    """对话会话 CRUD。"""

    def test_list_sessions(self, client, auth_header):
        """GET /api/agent/sessions — 返回会话列表。"""
        resp = client.get("/api/agent/sessions", headers=auth_header)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_session(self, client, auth_header, test_session):
        """POST /api/agent/sessions — 创建新会话。"""
        # 直接使用 test_session fixture 创建的会话，验证它存在
        resp = client.get("/api/agent/sessions", headers=auth_header)
        assert resp.status_code == 200
        session_ids = [s.get("id") for s in resp.json()]
        assert test_session in session_ids, f"已创建的会话 {test_session} 未找到"

    def test_create_and_delete(self, client, auth_header):
        """创建 → 删除完整流程。"""
        import uuid
        sid = f"pytest-{uuid.uuid4().hex[:10]}"
        # 创建
        resp = client.post(
            "/api/agent/sessions",
            headers=auth_header,
            json={"id": sid, "name": "创建测试"},
        )
        assert resp.status_code == 200
        # 删除
        resp = client.delete(f"/api/agent/sessions/{sid}",
                             headers=auth_header)
        assert resp.status_code == 200
        # 验证已删除：GET 单条应返回 404
        resp = client.get(f"/api/agent/sessions/{sid}",
                          headers=auth_header)
        assert resp.status_code == 404, f"删除后 session 仍存在: {resp.text}"

    def test_delete_nonexistent(self, client, auth_header):
        """DELETE 不存在会话 — 404。"""
        import uuid
        fake_sid = f"pytest-nonexistent-{uuid.uuid4().hex[:10]}"
        resp = client.delete(f"/api/agent/sessions/{fake_sid}",
                             headers=auth_header)
        assert resp.status_code == 404

    def test_update_session_name(self, client, auth_header, test_session):
        """PUT /api/agent/sessions/{id} — 更新会话名称。"""
        resp = client.put(
            f"/api/agent/sessions/{test_session}",
            json={"name": "重命名测试"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        sessions = resp.json()
        target = [s for s in sessions if s.get("id") == test_session]
        assert target, f"未找到会话 {test_session}"
        assert target[0]["name"] == "重命名测试"

    def test_get_session_detail(self, client, auth_header, test_session):
        """GET /api/agent/sessions/{id} — 获取会话详情。"""
        resp = client.get(f"/api/agent/sessions/{test_session}",
                          headers=auth_header)
        assert resp.status_code == 200
        detail = resp.json()
        assert detail.get("id") == test_session
