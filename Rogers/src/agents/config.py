"""智能体配置模式

基于 Pydantic 的统一配置方案，用于 LLM 模型、智能体、工具和运行时行为。
替代了分散的 os.getenv + pydantic-settings 方案，采用单一的类型化模式。
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Literal, Optional, Union

_logger = logging.getLogger("fitagent.config")

_DEFAULT_JWT_SECRET = "your-secret-key-change-in-production"

from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator

# 确保在调用任何 os.getenv 之前加载 .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")

# 导入统一配置
from src.fitme.core.config import settings


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


class BuiltinToolConfig(BaseModel):
    """内置工具配置。"""

    name: str
    enabled: bool = True
    description: str = ""


def _default_builtin_tools() -> dict[str, BuiltinToolConfig]:
    return {
        "execute_python_code": BuiltinToolConfig(
            name="execute_python_code",
            enabled=True,
            description="执行 Python 代码",
        ),
        "execute_shell_command": BuiltinToolConfig(
            name="execute_shell_command",
            enabled=True,
            description="执行 shell/bash 命令",
        ),
        "memory_search": BuiltinToolConfig(
            name="memory_search",
            enabled=True,
            description="搜索长期记忆内容",
        ),
        "read_skill_resource": BuiltinToolConfig(
            name="read_skill_resource",
            enabled=True,
            description="按需读取技能 references/scripts 文件",
        ),
        "get_user_profile": BuiltinToolConfig(name="get_user_profile", enabled=True),
        "get_health_summary": BuiltinToolConfig(name="get_health_summary", enabled=True),
        "get_health_history": BuiltinToolConfig(name="get_health_history", enabled=True),
        "get_training_today": BuiltinToolConfig(name="get_training_today", enabled=True),
        "get_training_weekly": BuiltinToolConfig(name="get_training_weekly", enabled=True),
        "get_training_recommendations": BuiltinToolConfig(
            name="get_training_recommendations", enabled=True,
        ),
        "get_diet_today": BuiltinToolConfig(name="get_diet_today", enabled=True),
        "get_diet_weekly_trend": BuiltinToolConfig(
            name="get_diet_weekly_trend", enabled=True,
        ),
        "get_food_recommendations": BuiltinToolConfig(
            name="get_food_recommendations", enabled=True,
        ),
        "get_user_settings": BuiltinToolConfig(name="get_user_settings", enabled=True),
        "get_full_overview": BuiltinToolConfig(name="get_full_overview", enabled=True),
        "search_foods": BuiltinToolConfig(name="search_foods", enabled=True),
        "update_profile": BuiltinToolConfig(name="update_profile", enabled=True),
        "add_health_metric": BuiltinToolConfig(name="add_health_metric", enabled=True),
        "add_training_plan": BuiltinToolConfig(name="add_training_plan", enabled=True),
        "complete_training": BuiltinToolConfig(name="complete_training", enabled=True),
        "delete_training_plan": BuiltinToolConfig(
            name="delete_training_plan", enabled=True,
        ),
        "add_meal": BuiltinToolConfig(name="add_meal", enabled=True),
        "update_meal": BuiltinToolConfig(name="update_meal", enabled=True),
        "delete_meal": BuiltinToolConfig(name="delete_meal", enabled=True),
        "update_settings": BuiltinToolConfig(name="update_settings", enabled=True),
        "add_custom_food": BuiltinToolConfig(name="add_custom_food", enabled=True),
    }


class ToolsConfig(BaseModel):
    """智能体内置工具配置。"""

    builtin_tools: dict[str, BuiltinToolConfig] = Field(
        default_factory=_default_builtin_tools,
    )

    @model_validator(mode="after")
    def _merge_default_tools(self) -> "ToolsConfig":
        defaults = _default_builtin_tools()
        for name, tool in defaults.items():
            if name not in self.builtin_tools:
                self.builtin_tools[name] = tool
        return self


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
    token_counter_model: str = ""  # HuggingFace 模型名，如 "Qwen/Qwen2.5-7B-Instruct"，空则用估算
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
    context_enabled: bool = True  # 是否启用上下文管理（生命周期钩子、压缩等）
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
# Heartbeat 配置（参考 CoPaw HeartbeatConfig）
# ---------------------------------------------------------------------------

HEARTBEAT_DEFAULT_EVERY = "6h"
HEARTBEAT_DEFAULT_TARGET = "main"
HEARTBEAT_TARGET_LAST = "last"


class ActiveHoursConfig(BaseModel):
    """心跳活跃时段（例如 08:00–22:00）。"""

    start: str = "08:00"
    end: str = "22:00"


class HeartbeatConfig(BaseModel):
    """心跳：按固定间隔以 HEARTBEAT.md 内容作为查询运行 agent。

    支持两种调度方式：
    - interval 字符串：'30m', '1h', '2h30m', '90s'
    - cron 表达式：'0 */6 * * *'
    """

    enabled: bool = Field(
        default=False,
        description="是否启用心跳",
    )
    every: str = Field(
        default=HEARTBEAT_DEFAULT_EVERY,
        description="调度间隔（interval 字符串如 '30m' / '6h'，或 cron 表达式如 '0 */6 * * *'）",
    )
    target: str = Field(
        default=HEARTBEAT_DEFAULT_TARGET,
        description="路由目标：'main' 静默执行，'last' 路由到上次活跃频道",
    )
    active_hours: Optional[ActiveHoursConfig] = Field(
        default=None,
        description="可选活跃时段，非活跃时段跳过心跳",
    )


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
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    tool_groups: dict[str, ToolGroupConfig] = Field(default_factory=dict)
    running: RunningConfig = Field(default_factory=RunningConfig)
    heartbeat: HeartbeatConfig = Field(
        default_factory=HeartbeatConfig,
        description="心跳配置（按固定间隔以 HEARTBEAT.md 为查询运行 agent）",
    )

    # 已启用工具的派生列表
    def get_enabled_tools(self) -> list[str]:
        tools = [
            name for name, config in self.tools.builtin_tools.items() if config.enabled
        ]
        for group in self.tool_groups.values():
            if group.enabled:
                tools.extend(group.tool_names)
        return list(dict.fromkeys(tools))


# ---------------------------------------------------------------------------
# 根应用配置
# ---------------------------------------------------------------------------

class AppConfig(BaseModel):
    """从 config.json 和环境变量加载的根配置。"""
    # 应用级设置（镜像 src/fitme/core/config.py 中的 Settings）
    app_name: str = "FitAgent"
    app_version: str = "1.0.0"
    debug: bool = True
    database_url: str = "sqlite:///./data/fituser.db"
    jwt_secret_key: str = _DEFAULT_JWT_SECRET
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
        # 检查不安全的 JWT 密钥
        if self.jwt_secret_key == _DEFAULT_JWT_SECRET:
            raise ValueError(
                "必须设置 JWT_SECRET_KEY！请在 .env 中配置"
            )
        return self

    @classmethod
    def from_env(cls) -> "AppConfig":
        """纯从环境变量构建配置。

        API Key 不再从环境变量读取，只能通过 Agent 配置页面由用户自行设置。
        """
        # 注册默认模型（不含 API Key，需用户在配置页面填入）
        models: dict[str, ModelProvider] = {
            "primary": ModelProvider(
                provider="dashscope",
                model_name=os.getenv("DASHSCOPE_MODEL", "qwen-turbo"),
            ),
        }

        openai_base_url = os.getenv("OPENAI_BASE_URL", "")
        if openai_base_url:
            models["fallback"] = ModelProvider(
                provider="openai",
                base_url=openai_base_url or None,
                model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
            )

        return cls(
            app_name=os.getenv("APP_NAME", "FitAgent"),
            app_version=os.getenv("APP_VERSION", "1.0.0"),
            debug=False,
            database_url=os.getenv("DATABASE_URL", "sqlite:///./db/fitagent.db"),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", _DEFAULT_JWT_SECRET),
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

        # 清理所有模型配置中的 base_url
        if "models" in merged and isinstance(merged["models"], dict):
            for model_key in merged["models"]:
                if isinstance(merged["models"][model_key], dict) and "base_url" in merged["models"][model_key]:
                    del merged["models"][model_key]["base_url"]

        # 清理所有 agent 配置中的 base_url
        if "agents" in merged and isinstance(merged["agents"], dict):
            for agent_key in merged["agents"]:
                agent_config = merged["agents"][agent_key]
                if isinstance(agent_config, dict) and "model" in agent_config:
                    model_config = agent_config["model"]
                    if isinstance(model_config, dict) and "base_url" in model_config:
                        del model_config["base_url"]

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
_user_configs: dict[int, AppConfig] = {}  # 缓存每个用户的配置


def get_config(user_id: int | str | None = None) -> AppConfig:
    """返回全局 AppConfig 单例，如未加载则先加载。

    Args:
        user_id: 用户ID，如果提供则尝试从用户的本地目录加载配置
    """
    global _config

    # 如果有 user_id，尝试从用户本地目录加载
    if user_id is not None:
        uid = int(user_id)
        if uid not in _user_configs:
            _user_configs[uid] = _load_config_for_user(uid)
        return _user_configs[uid]

    # 全局配置
    if _config is None:
        # 使用统一配置的路径
        config_path = settings.AGENT_DB_DIR / "agent.json"
        _config = AppConfig.from_file(config_path)
    return _config


def _load_config_for_user(user_id: int) -> AppConfig:
    """为指定用户加载配置。

    优先从用户配置的本地目录加载，如果没有配置则使用默认目录。
    """
    try:
        from src.fitme.utils.database import UserSessionLocal
        from src.fitme.crud import agent_config as agent_crud
        from src.fitme.utils.agent_directory import get_default_agent_directory

        db = UserSessionLocal()
        try:
            config = agent_crud.get_user_agent_config(db, user_id)
            if config and config.local_working_dir:
                local_dir = config.local_working_dir
            else:
                local_dir = get_default_agent_directory()

            # 从用户本地目录加载 agent.json
            config_path = Path(local_dir) / "agent.json"
            if config_path.exists():
                return AppConfig.from_file(config_path)

            # 如果用户本地没有配置，使用全局配置
            return get_config()
        finally:
            db.close()
    except Exception:
        # 出错时回退到全局配置
        return get_config()


def load_agent_config(user_id: int | str) -> AgentConfig:
    """加载指定用户的智能体配置。

    返回全局 active_agent 配置，并可选地与用户本地目录中的
    agent.json 覆盖配置合并。
    """
    config = get_config(user_id)
    agent_cfg = config.get_active_agent()

    # 清理全局配置中的 base_url
    if hasattr(agent_cfg, "model"):
        model_cfg = agent_cfg.model
        if not isinstance(model_cfg, str) and hasattr(model_cfg, "base_url"):
            object.__setattr__(model_cfg, "base_url", None)

    # 尝试从用户本地目录加载覆盖配置
    try:
        user_local_config = _get_user_local_config_path(int(user_id))
        if user_local_config and user_local_config.exists():
            with open(user_local_config, encoding="utf-8") as f:
                user_data = json.load(f)
            merged = agent_cfg.model_dump()

            # 特殊处理 model 字段：
            if "model" in user_data and isinstance(user_data["model"], dict):
                if isinstance(merged.get("model"), str):
                    model_key = merged["model"]
                    if model_key in config.models:
                        merged["model"] = config.models[model_key].model_dump()

                if isinstance(merged.get("model"), dict):
                    user_model = user_data["model"]
                    # 只合并我们明确支持的字段，不处理 base_url
                    for key in ["api_key", "model_name", "provider", "stream"]:
                        if key in user_model and user_model[key] is not None and user_model[key] != "":
                            merged["model"][key] = user_model[key]
                    # 移除 base_url（不需要自定义）
                    if "base_url" in merged["model"]:
                        del merged["model"]["base_url"]
                    del user_data["model"]

            _deep_merge(merged, user_data)
            return AgentConfig(**merged)
    except Exception:
        pass

    return agent_cfg


def _get_user_local_config_path(user_id: int) -> Path | None:
    """获取用户本地配置文件路径"""
    try:
        from src.fitme.utils.database import UserSessionLocal
        from src.fitme.crud import agent_config as agent_crud
        from src.fitme.utils.agent_directory import get_default_agent_directory

        db = UserSessionLocal()
        try:
            config = agent_crud.get_user_agent_config(db, user_id)
            if config and config.local_working_dir:
                return Path(config.local_working_dir) / "agent.json"
            else:
                return Path(get_default_agent_directory()) / "agent.json"
        finally:
            db.close()
    except Exception:
        return None


def set_config(config: AppConfig, user_id: int | None = None) -> None:
    """设置全局配置（适用于测试或编程覆盖）。

    Args:
        config: 要设置的配置
        user_id: 如果提供则设置该用户的配置，否则设置全局配置
    """
    global _config
    if user_id is not None:
        _user_configs[int(user_id)] = config
    else:
        _config = config
