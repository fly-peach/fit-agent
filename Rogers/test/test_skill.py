"""技能路由测试 — Skill CRUD、子技能、配置管理。"""
import pytest


class TestSkillsRouter:
    """技能基本 CRUD。"""

    def test_list_skills(self, client, auth_header):
        """GET /api/agent/skills — 返回列表，每个技能含完整字段。"""
        resp = client.get("/api/agent/skills", headers=auth_header)
        assert resp.status_code == 200
        skills = resp.json()
        assert isinstance(skills, list)
        if skills:
            for field in ("name", "version", "description", "enabled",
                          "path", "tags", "channels", "source"):
                assert field in skills[0], f"缺少字段: {field}"

    def test_skill_detail(self, client, auth_header):
        """GET /api/agent/skills/{name} — 返回技能详情。"""
        resp = client.get("/api/agent/skills/fitme-skills", headers=auth_header)
        assert resp.status_code == 200, resp.text
        detail = resp.json()
        for field in ("name", "version", "description", "content",
                      "body", "references", "scripts", "source", "tags",
                      "enabled", "channels"):
            assert field in detail, f"缺少字段: {field}"

    def test_skill_detail_404(self, client, auth_header):
        """GET /api/agent/skills/nonexistent — 404。"""
        resp = client.get("/api/agent/skills/nonexistent", headers=auth_header)
        assert resp.status_code == 404

    def test_sub_skills(self, client, auth_header):
        """GET /api/agent/skills/{name}/sub-skills — 返回子技能列表。"""
        resp = client.get("/api/agent/skills/fitme-skills/sub-skills",
                          headers=auth_header)
        assert resp.status_code == 200, resp.text
        subs = resp.json()
        assert isinstance(subs, list)

    def test_enable_skill(self, client, auth_header):
        """PUT enable — 技能启用。"""
        resp = client.put("/api/agent/skills/fitme-skills/enable",
                          headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_disable_skill(self, client, auth_header):
        """PUT disable — 技能禁用。"""
        resp = client.put("/api/agent/skills/fitme-skills/disable",
                          headers=auth_header)
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    def test_update_skill(self, client, auth_header):
        """PUT /{name} — 更新技能配置。"""
        resp = client.put(
            "/api/agent/skills/fitme-skills",
            json={"enabled": True, "priority": 2},
            headers=auth_header,
        )
        assert resp.status_code == 200

    def test_export_skill(self, client, auth_header):
        """GET /{name}/export — 导出技能 ZIP。"""
        resp = client.get("/api/agent/skills/fitme-skills/export",
                          headers=auth_header)
        assert resp.status_code in (200, 404)


class TestSkillsConfigRouter:
    """技能配置管理。"""

    @pytest.mark.parametrize("ep", ["/config", "/config/sync-status"])
    def test_config_endpoints(self, client, auth_header, ep):
        """GET /config 和 /config/sync-status 应返回 200。"""
        resp = client.get(f"/api/agent/skills{ep}", headers=auth_header)
        assert resp.status_code == 200, f"{ep}: {resp.text}"

    def test_initialize_config(self, client, auth_header):
        """POST /config/initialize — 初始化配置。"""
        resp = client.post(
            "/api/agent/skills/config/initialize",
            json={"default_skill_names": ["fitme-diet"]},
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.json()["initialized"] is True

    def test_sync_config(self, client, auth_header):
        """POST /config/sync — 同步配置。"""
        resp = client.post(
            "/api/agent/skills/config/sync",
            json={"direction": "two-way"},
            headers=auth_header,
        )
        assert resp.status_code == 200

    def test_update_package(self, client, auth_header):
        """PUT /config/packages/{name} — 更新技能包。"""
        resp = client.put(
            "/api/agent/skills/config/packages/fitme-diet",
            json={"enabled": True, "priority": 1},
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert "skill_packages" in resp.json()

    def test_reset_config(self, client, auth_header):
        """DELETE /config/reset — 重置配置。"""
        resp = client.delete("/api/agent/skills/config/reset",
                             headers=auth_header)
        assert resp.status_code == 200
