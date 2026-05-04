"""智能体配置模式

基于 Pydantic 的统一配置方案，用于 LLM 模型、智能体、工具和运行时行为。
替代了分散的 os.getenv + pydantic-settings 方案，采用单一的类型化模式。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal, Optional, Union

from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator

# 确保在调用任何 os.getenv 之前加载 .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")


# ---------------------------------------------------------------------------
# 模型提供方配置
# ---------------------------------------------------------------------------

class ModelProvider(BaseModel):
    """单个 LLM 提供方端点的配置。"""
    provider: Literal["dashscope", "openai", "custom"] = "dashscope"
    api_key: str = ""
    base_url: Optional[str] = None
    model_name: str = "qwen-turbo"
    stream: bool = True


# ---------------------------------------------------------------------------
# 工具组配置
# ---------------------------------------------------------------------------

class ToolGroupConfig(BaseModel):
    """可被每个智能体启用/禁用的命名工具组。"""
    enabled: bool = True
    tool_names: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 运行时配置
# ---------------------------------------------------------------------------

class EmbeddingConfig(BaseModel):
    """ReMe 记忆的嵌入模型配置。"""
    backend: str = "openai"
    api_key: str = ""
    base_url: str = ""
    model_name: str = ""
    dimensions: int = 1024
    enable_cache: bool = True
    use_dimensions: bool = False
    max_cache_size: int = 3000
    max_input_length: int = 8192
    max_batch_size: int = 10


class ContextCompactConfig(BaseModel):
    """上下文压缩和令牌计数配置。"""
    token_count_estimate_divisor: float = 3.75
    context_compact_enabled: bool = True
    memory_compact_ratio: float = 0.75
    memory_reserve_ratio: float = 0.1
    compact_with_thinking_block: bool = False


class ToolResultCompactConfig(BaseModel):
    """工具结果压缩阈值和保留配置。"""
    enabled: bool = True
    recent_n: int = 2
    old_max_bytes: int = 3000
    recent_max_bytes: int = 50000
    retention_days: int = 5


class MemorySummaryConfig(BaseModel):
    """记忆摘要和搜索配置。"""
    memory_summary_enabled: bool = True
    force_memory_search: bool = False
    force_max_results: int = 1
    force_min_score: float = 0.3
    force_memory_search_timeout: float = 10.0
    rebuild_memory_index_on_start: bool = False
    recursive_file_watcher: bool = False


class RunningConfig(BaseModel):
    """智能体的运行时行为配置。"""
    max_iters: int = 20
    history_max_length: int = 50
    max_input_length: int = 131072  # 128K 令牌
    compact_token_threshold: int = 6000
    embedding_config: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    context_compact: ContextCompactConfig = Field(default_factory=ContextCompactConfig)
    tool_result_compact: ToolResultCompactConfig = Field(default_factory=ToolResultCompactConfig)
    memory_summary: MemorySummaryConfig = Field(default_factory=MemorySummaryConfig)

    @property
    def memory_compact_reserve(self) -> int:
        """记忆压缩保留大小（令牌数）。"""
        return int(self.max_input_length * self.context_compact.memory_reserve_ratio)

    @property
    def memory_compact_threshold(self) -> int:
        """记忆压缩阈值大小（令牌数）。"""
        return int(self.max_input_length * self.context_compact.memory_compact_ratio)


# ---------------------------------------------------------------------------
# 智能体配置（每个智能体实例的配置，参考 CoPaw 的 AgentProfileConfig）
# ---------------------------------------------------------------------------

class AgentConfig(BaseModel):
    """单个智能体实例的完整配置。

    ``model`` 可以是 ``ModelProvider`` 对象，也可以是字符串引用
    （例如 ``"primary"``），会被解析为 ``AppConfig.models[key]``。
    """
    id: str = "default"
    name: str = "Rogers"
    description: str = ""
    sys_prompt: str = ""
    sys_prompt_files: list[str] = Field(default_factory=list)
    model: Union[str, ModelProvider] = Field(default_factory=ModelProvider)
    tool_groups: dict[str, ToolGroupConfig] = Field(default_factory=dict)
    running: RunningConfig = Field(default_factory=RunningConfig)

    # 已启用工具的派生列表
    def get_enabled_tools(self) -> list[str]:
        tools: list[str] = []
        for group in self.tool_groups.values():
            if group.enabled:
                tools.extend(group.tool_names)
        return tools


# ---------------------------------------------------------------------------
# 根应用配置
# ---------------------------------------------------------------------------

class AppConfig(BaseModel):
    """从 config.json 和环境变量加载的根配置。"""
    # 应用级设置（镜像 src/fitme/core/config.py 中的 Settings）
    app_name: str = "FitAgent"
    app_version: str = "1.0.0"
    debug: bool = True
    database_url: str = "sqlite:///./db/fitagent.db"
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # 服务器
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    redis_url: Optional[str] = None

    # LLM 模型（以提供方别名作为键，例如 "primary"、"fallback"）
    models: dict[str, ModelProvider] = Field(default_factory=dict)

    # 智能体（以智能体 id 作为键）
    agents: dict[str, AgentConfig] = Field(default_factory=dict)

    # 活动智能体（处理请求的智能体）
    active_agent: str = "default"

    @model_validator(mode="after")
    def _resolve_model_refs_and_ensure_default(self) -> "AppConfig":
        """解析字符串模型引用并确保默认智能体存在。"""
        for agent in self.agents.values():
            if isinstance(agent.model, str) and agent.model in self.models:
                agent.model = self.models[agent.model]
        if "default" not in self.agents:
            primary_model = self.models.get("primary", ModelProvider())
            self.agents["default"] = AgentConfig(
                id="default",
                name="Rogers",
                model=primary_model,
            )
        # 确保 active_agent 指向有效的智能体
        if self.active_agent not in self.agents:
            self.active_agent = "default"
        return self

    @classmethod
    def from_env(cls) -> "AppConfig":
        """纯从环境变量构建配置（向后兼容）。"""
        models: dict[str, ModelProvider] = {}

        dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
        if dashscope_key:
            models["primary"] = ModelProvider(
                provider="dashscope",
                api_key=dashscope_key,
                model_name=os.getenv("DASHSCOPE_MODEL", "qwen-turbo"),
            )

        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            models["fallback"] = ModelProvider(
                provider="openai",
                api_key=openai_key,
                base_url=os.getenv("OPENAI_BASE_URL") or None,
                model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
            )

        return cls(
            app_name=os.getenv("APP_NAME", "FitAgent"),
            app_version=os.getenv("APP_VERSION", "1.0.0"),
            debug=os.getenv("DEBUG", "true").lower() in ("true", "1"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./db/fitagent.db"),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
            server_host=os.getenv("SERVER_HOST", "127.0.0.1"),
            server_port=int(os.getenv("SERVER_PORT", "8000")),
            redis_url=os.getenv("REDIS_URL") or None,
            models=models,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "AppConfig":
        """从 JSON 文件加载配置，并与环境变量合并。"""
        path = Path(path)
        if not path.exists():
            return cls.from_env()
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        env = cls.from_env()
        # 合并：文件值优先，环境变量填充缺失项
        merged: dict[str, Any] = env.model_dump()
        _deep_merge(merged, data)
        return cls(**merged)

    def get_active_agent(self) -> AgentConfig:
        """返回当前活动的智能体配置。"""
        return self.agents.get(self.active_agent, self.agents["default"])

    def save_to_file(self, path: str | Path) -> None:
        """将当前配置持久化到 JSON 文件。"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)


def _deep_merge(base: dict, override: dict) -> None:
    """将 *override* 递归合并到 *base* 中（原地修改）。"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


# ---------------------------------------------------------------------------
# 模块级单例（替代 app/core/config.py 的全局变量）
# ---------------------------------------------------------------------------

_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """返回全局 AppConfig 单例，如未加载则先加载。"""
    global _config
    if _config is None:
        # 尝试从默认配置路径加载，失败则回退到环境变量
        config_path = Path(__file__).resolve().parent.parent.parent / "agent_db" / "agent.json"
        _config = AppConfig.from_file(config_path)
    return _config


def load_agent_config(user_id: int | str) -> AgentConfig:
    """加载指定用户的智能体配置。

    返回全局 active_agent 配置，并可选地与
    workspace/users/{uid}/agent.json 中的用户级覆盖配置合并。
    """
    config = get_config()
    agent_cfg = config.get_active_agent()
    # 检查每个用户的配置文件
    workspace_root = Path(__file__).resolve().parent.parent.parent / "agent_db" / "workspace"
    user_config_path = workspace_root / "users" / str(user_id) / "agent.json"
    if user_config_path.exists():
        with open(user_config_path, encoding="utf-8") as f:
            user_data = json.load(f)
        merged = agent_cfg.model_dump()
        _deep_merge(merged, user_data)
        return AgentConfig(**merged)
    return agent_cfg


def set_config(config: AppConfig) -> None:
    """设置全局配置（适用于测试或编程覆盖）。"""
    global _config
    _config = config
