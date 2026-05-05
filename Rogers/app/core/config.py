"""App Configuration — unified entry point.

All config is now sourced from ``src.agents.config.AppConfig``.
Module-level globals (SERVER_HOST, etc.) are kept for
backward compatibility with existing imports.

API Key 不再从环境变量读取，只能通过 Agent 配置页面由用户自行设置。
"""
from __future__ import annotations

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# ---------------------------------------------------------------------------
# Unified config (new system)
# ---------------------------------------------------------------------------
from src.agents.config import AppConfig, get_config

# Eager-load so module-level globals below are populated
_config: AppConfig = get_config()

# Re-export the original Settings singleton for app-level consumers
from src.fitme.core.config import settings  # noqa: F401

# ---------------------------------------------------------------------------
# Backward-compatible module-level globals
# ---------------------------------------------------------------------------
SERVER_HOST: str = _config.server_host
SERVER_PORT: int = _config.server_port
REDIS_URL: str | None = _config.redis_url

__all__ = [
    "settings",
    "get_config",
    "SERVER_HOST",
    "SERVER_PORT",
    "REDIS_URL",
]
