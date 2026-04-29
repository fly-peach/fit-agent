"""App Configuration — unified entry point.

All config is now sourced from ``src.agents.config.AppConfig``.
Module-level globals (REDIS_URL, SERVER_HOST, etc.) are kept for
backward compatibility with existing imports.
"""
from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Unified config (new system)
# ---------------------------------------------------------------------------
from src.agents.config import AppConfig, get_config, ModelProvider

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

# LLM config (legacy aliases, new code should use get_config() instead)
def _resolve_model(name: str) -> ModelProvider:
    """Resolve a model by name, falling back to the default agent's model."""
    if name in _config.models:
        return _config.models[name]
    default = _config.agents.get("default", None)
    if default and isinstance(default.model, ModelProvider):
        return default.model
    return ModelProvider()

_primary = _resolve_model("primary")
_fallback = _resolve_model("fallback")

DASHSCOPE_API_KEY: str = _primary.api_key
DASHSCOPE_MODEL: str = _primary.model_name
OPENAI_API_KEY: str = _fallback.api_key
OPENAI_BASE_URL: str = _fallback.base_url or ""
OPENAI_MODEL: str = _fallback.model_name

__all__ = [
    "settings",
    "get_config",
    "SERVER_HOST",
    "SERVER_PORT",
    "REDIS_URL",
    "DASHSCOPE_API_KEY",
    "DASHSCOPE_MODEL",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
]
