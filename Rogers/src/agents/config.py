"""Agent Configuration Schema

Unified Pydantic-based configuration for LLM models, agents, tools, and runtime behavior.
Replaces the split os.getenv + pydantic-settings approach with a single typed schema.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal, Optional, Union

from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator

# Ensure .env is loaded before any os.getenv calls
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")


# ---------------------------------------------------------------------------
# Model provider configuration
# ---------------------------------------------------------------------------

class ModelProvider(BaseModel):
    """Configuration for a single LLM provider endpoint."""
    provider: Literal["dashscope", "openai", "custom"] = "dashscope"
    api_key: str = ""
    base_url: Optional[str] = None
    model_name: str = "qwen-turbo"
    enable_thinking: bool = True
    stream: bool = True


# ---------------------------------------------------------------------------
# Tool group configuration
# ---------------------------------------------------------------------------

class ToolGroupConfig(BaseModel):
    """A named group of tools that can be enabled/disabled per agent."""
    enabled: bool = True
    tool_names: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Runtime / running configuration
# ---------------------------------------------------------------------------

class RunningConfig(BaseModel):
    """Runtime behavior for an agent."""
    max_iters: int = 20
    history_max_length: int = 50
    max_input_length: int = 8000
    compact_token_threshold: int = 6000


# ---------------------------------------------------------------------------
# Agent configuration (per-agent, inspired by CoPaw's AgentProfileConfig)
# ---------------------------------------------------------------------------

class AgentConfig(BaseModel):
    """Complete configuration for a single agent instance.

    ``model`` can be either a ``ModelProvider`` object or a string reference
    (e.g. ``"primary"``) that gets resolved to ``AppConfig.models[key]``.
    """
    id: str = "default"
    name: str = "Rogers"
    description: str = ""
    sys_prompt: str = ""
    sys_prompt_files: list[str] = Field(default_factory=list)
    model: Union[str, ModelProvider] = Field(default_factory=ModelProvider)
    tool_groups: dict[str, ToolGroupConfig] = Field(default_factory=dict)
    running: RunningConfig = Field(default_factory=RunningConfig)

    # Derived list of enabled tool names
    def get_enabled_tools(self) -> list[str]:
        tools: list[str] = []
        for group in self.tool_groups.values():
            if group.enabled:
                tools.extend(group.tool_names)
        return tools


# ---------------------------------------------------------------------------
# Root application config
# ---------------------------------------------------------------------------

class AppConfig(BaseModel):
    """Root configuration loaded from config.json + environment variables."""
    # App-level settings (mirrors Settings from src/fitme/core/config.py)
    app_name: str = "FitAgent"
    app_version: str = "1.0.0"
    debug: bool = True
    database_url: str = "sqlite:///./db/fitagent.db"
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Server
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    redis_url: Optional[str] = None

    # LLM models (keyed by provider alias, e.g. "primary", "fallback")
    models: dict[str, ModelProvider] = Field(default_factory=dict)

    # Agents (keyed by agent id)
    agents: dict[str, AgentConfig] = Field(default_factory=dict)

    # Active agent (which agent handles requests)
    active_agent: str = "default"

    @model_validator(mode="after")
    def _resolve_model_refs_and_ensure_default(self) -> "AppConfig":
        """Resolve string model references and ensure a default agent exists."""
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
        # Ensure active_agent points to a valid agent
        if self.active_agent not in self.agents:
            self.active_agent = "default"
        return self

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Build config purely from environment variables (backward compatible)."""
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
        """Load config from a JSON file, merging with env as fallback."""
        path = Path(path)
        if not path.exists():
            return cls.from_env()
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        env = cls.from_env()
        # Merge: file values take precedence, env fills gaps
        merged: dict[str, Any] = env.model_dump()
        _deep_merge(merged, data)
        return cls(**merged)

    def get_active_agent(self) -> AgentConfig:
        """Return the currently active agent config."""
        return self.agents.get(self.active_agent, self.agents["default"])

    def save_to_file(self, path: str | Path) -> None:
        """Persist current config to a JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)


def _deep_merge(base: dict, override: dict) -> None:
    """Recursively merge *override* into *base* in-place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


# ---------------------------------------------------------------------------
# Module-level singleton (replaces app/core/config.py globals)
# ---------------------------------------------------------------------------

_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Return the global AppConfig singleton, loading if needed."""
    global _config
    if _config is None:
        # Try loading from default config path, fall back to env
        config_path = Path(__file__).resolve().parent.parent.parent / "config" / "agent.json"
        _config = AppConfig.from_file(config_path)
    return _config


def set_config(config: AppConfig) -> None:
    """Set the global config (useful for testing or programmatic override)."""
    global _config
    _config = config
