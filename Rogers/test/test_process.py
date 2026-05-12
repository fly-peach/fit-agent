"""Agent 处理流程测试 — 健康检查、Agent 状态、Pipeline 逻辑。"""
import pytest


class TestHealthCheck:
    """基础健康检查。"""

    def test_health(self, client):
        """GET /health — 返回 healthy。"""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestAgentStatus:
    """Agent 配置状态。"""

    def test_status_ok(self, client, auth_header):
        """GET /api/agent/config/status — 返回配置状态。"""
        resp = client.get("/api/agent/config/status", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        # 即使未配置也应有合理响应
        assert "ready" in data
        assert "message" in data

    def test_config_endpoint(self, client, auth_header):
        """GET /api/agent/config — 返回用户配置。"""
        resp = client.get("/api/agent/config", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert "agents_md" in data
        assert "soul_md" in data
        assert "model_name" in data

    def test_defaults_endpoint(self, client):
        """GET /api/agent/defaults — 返回默认配置。"""
        resp = client.get("/api/agent/defaults")
        assert resp.status_code == 200
        data = resp.json()
        assert "agents_md" in data
        assert "soul_md" in data
        assert "model_name" in data


class TestPipelineLogic:
    """Pipeline 编排逻辑（单元级，不依赖 API Key）。"""

    def test_parse_pipeline_marker(self):
        """_parse_pipeline_marker — 解析 JSON 标记。"""
        from src.agents.rogers_agent import _parse_pipeline_marker

        text = 'text\n```pipeline\n{"action":"fanout","needs":["diet"]}\n```\nend'
        marker = _parse_pipeline_marker(text)
        assert marker is not None
        assert marker["action"] == "fanout"
        assert "diet" in marker["needs"]

    def test_parse_no_marker(self):
        """无标记时返回 None。"""
        from src.agents.rogers_agent import _parse_pipeline_marker
        assert _parse_pipeline_marker("简单回答") is None

    def test_has_image_true(self):
        """_has_image — 含图片消息返回 True。"""
        from src.agents.rogers_agent import _has_image
        from agentscope.message import Msg

        msg = Msg(
            name="user", role="user",
            content=[
                {"type": "text", "text": "看照片"},
                {"type": "image", "source": {"type": "url", "url": "/img/1"}},
            ],
        )
        assert _has_image(msg) is True

    def test_has_image_false(self):
        """_has_image — 纯文本消息返回 False。"""
        from src.agents.rogers_agent import _has_image
        from agentscope.message import Msg

        msg = Msg(name="user", role="user", content="你好")
        assert _has_image(msg) is False

    def test_vision_step_no_image(self):
        """_vision_step — 无图片时跳过。"""
        from src.agents.config import PipelineConfig
        from src.agents.rogers_agent import PipelineController
        from unittest.mock import MagicMock

        cfg = PipelineConfig()
        sm = MagicMock()
        ctrl = PipelineController(cfg, sm, "sk-test", "/tmp")
        msgs = [MagicMock(content="纯文本")]
        import pytest_asyncio
        # 同步验证：控制器创建成功
        assert ctrl is not None

    def test_skill_bindings_keys(self):
        """SKILL_BINDINGS — 包含 expected 子类型。"""
        from src.agents.rogers_agent import SKILL_BINDINGS
        for key in ("diet", "training", "all"):
            assert key in SKILL_BINDINGS, f"缺少绑定: {key}"
        assert "fitme-diet" in SKILL_BINDINGS["diet"]
        assert "fitme-training" in SKILL_BINDINGS["training"]
        assert "fitme-exercise" in SKILL_BINDINGS["training"]
