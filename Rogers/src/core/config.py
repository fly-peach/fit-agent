"""FitAgent Core Configuration

Unified configuration module containing both:
- Settings: Pydantic settings for database, JWT, etc.
- AppConfig: Dataclass for server, model, pipeline config
"""
from __future__ import annotations

import os
import logging
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings


# ── Load .env once ──────────────────────────────────────────────────────────
_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_env_path = _BASE_DIR / ".env"
load_dotenv(dotenv_path=_env_path)

logger = logging.getLogger("fitagent.config")

_DEFAULT_JWT_SECRET = "your-secret-key-change-in-production"

# 统一的数据根目录 - rogers/data
_DATA_DIR = _BASE_DIR / "data"


class Settings(BaseSettings):
    """Application settings (database, JWT, etc.)"""
    # 统一数据目录
    DATA_DIR: Path = _DATA_DIR

    # Base DB (基础数据库：健身动作库、食物库等系统预置数据)
    BASE_DB_URL: str = f"sqlite:///{_DATA_DIR / 'fitbase.db'}"

    # User DB (用户数据库：用户数据、自定义数据等)
    USER_DB_URL: str = f"sqlite:///{_DATA_DIR / 'fituser.db'}"

    # Agent Memory DB (智能体消息历史，独立文件避免表名冲突)
    AGENT_MEMORY_DB_URL: str = f"sqlite:///{_DATA_DIR / 'agent_memory.db'}"

    # 兼容旧代码 - 指向 user_db
    DATABASE_URL: str = f"sqlite:///{_DATA_DIR / 'fituser.db'}"

    JWT_SECRET_KEY: str = _DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # CORS 跨域配置：逗号分隔允许的前端域名
    CORS_ORIGINS: str = ""

    APP_NAME: str = "FitAgent"
    APP_VERSION: str = "1.0.0"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def _validate_security_settings(self) -> "Settings":
        if self.JWT_SECRET_KEY == _DEFAULT_JWT_SECRET:
            raise ValueError(
                "必须设置 JWT_SECRET_KEY！请在 .env 中配置 "
                "(生成命令: python -c \"import secrets; print(secrets.token_hex(32))\")"
            )

        if not self.CORS_ORIGINS:
            raise ValueError(
                "必须设置 CORS_ORIGINS！请在 .env 中配置允许的跨域域名（逗号分隔）"
            )

        return self


@dataclass
class AppConfig:
    """应用级配置，从环境变量读取（不含 API Key）。

    API Key 改为动态缓存方案（见 ``src.agents.utils.api_key_cache``），
    不再通过环境变量或此配置类读取。
    """
    # ── 服务器 ──
    server_host: str = field(
        default_factory=lambda: os.getenv("SERVER_HOST", "127.0.0.1"),
    )
    server_port: int = field(
        default_factory=lambda: int(os.getenv("SERVER_PORT", "8000")),
    )

    # ── Redis ──
    # fakeredis 占位标识。项目目前使用 fakeredis.FakeRedis，无需真实 Redis 实例。
    redis_url: str | None = field(
        default_factory=lambda: os.getenv("REDIS_URL", "fakeredis://"),
    )

    # ── 模型（仅模型名称，API Key 由缓存管理） ──
    vision_model: str = field(
        default_factory=lambda: os.getenv("VISION_MODEL", "qwen-vl-max"),
    )
    reasoning_model: str = field(
        default_factory=lambda: os.getenv("REASONING_MODEL", "qwen-max"),
    )

    # ── Pipeline ──
    fanout_enabled: bool = field(
        default_factory=lambda: os.getenv("FANOUT_ENABLED", "true").lower() == "true",
    )


# ── Singletons ──────────────────────────────────────────────────────────────

settings = Settings()

# 全局 AppConfig 单例（惰性加载）
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """获取全局 AppConfig 单例。"""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


# ── 向后兼容的模块级全局变量 ────────────────────────────────────────────────────
_config_singleton = get_config()

SERVER_HOST: str = _config_singleton.server_host
SERVER_PORT: int = _config_singleton.server_port
REDIS_URL: str | None = _config_singleton.redis_url

__all__ = [
    "Settings",
    "settings",
    "AppConfig",
    "get_config",
    "SERVER_HOST",
    "SERVER_PORT",
    "REDIS_URL",
]
