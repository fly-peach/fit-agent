"""Skill 配置管理（保留兼容桩，实际配置逻辑已迁移到 SkillManager）。"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

logger = __import__("logging").getLogger("fitagent")

SKILL_CONFIG_FILENAME = "skill-config.json"
SKILL_CONFIG_VERSION = "1.0.0"


class SkillPackageConfig(BaseModel):
    """单个技能包的配置（兼容桩）。"""
    name: str
    enabled: bool = True
    auto_update: bool = True
    priority: int = 0
    config: dict[str, Any] = Field(default_factory=dict)


class SkillSystemConfig(BaseModel):
    """技能系统的全局配置（兼容桩）。"""
    version: str = SKILL_CONFIG_VERSION
    initialized: bool = False
    initialized_at: str | None = None
    last_synced_at: str | None = None
    default_skills_enabled: list[str] = Field(default_factory=list)
    skill_packages: dict[str, SkillPackageConfig] = Field(default_factory=dict)
    global_settings: dict[str, Any] = Field(default_factory=dict)


class SkillConfigManager:
    """技能配置管理器（兼容桩）。

    实际配置管理已迁移到 SkillManager 内部。
    保留此类用于向后兼容。
    """

    def __init__(self, working_dir: str | Path):
        self.working_dir = Path(working_dir)
        self.config_path = self.working_dir / SKILL_CONFIG_FILENAME
        self._config_cache: SkillSystemConfig | None = None

    def get_config(self, force_reload: bool = False) -> SkillSystemConfig:
        if self._config_cache is None or force_reload:
            self._config_cache = SkillSystemConfig()
        return self._config_cache

    def save_config(self, config: SkillSystemConfig) -> None:
        self.working_dir.mkdir(parents=True, exist_ok=True)
        config.last_synced_at = datetime.now().isoformat()
        self._config_cache = config

    def initialize_config(self, default_skill_names: list[str] | None = None) -> SkillSystemConfig:
        config = self.get_config()
        config.initialized = True
        config.initialized_at = datetime.now().isoformat()
        if default_skill_names:
            config.default_skills_enabled = default_skill_names
        self.save_config(config)
        return config

    def update_skill_package(self, **kwargs: Any) -> SkillSystemConfig:
        return self.get_config()

    def get_skill_package(self, name: str) -> SkillPackageConfig | None:
        return self.get_config().skill_packages.get(name)

    def is_skill_enabled(self, name: str) -> bool:
        config = self.get_config()
        return name in config.default_skills_enabled

    def sync_with_skill_manager(self, skill_manager: Any) -> SkillSystemConfig:
        return self.get_config()

    def get_sync_status(self) -> dict[str, Any]:
        config = self.get_config()
        return {
            "initialized": config.initialized,
            "initialized_at": config.initialized_at,
            "last_synced_at": config.last_synced_at,
            "total_skill_packages": len(config.skill_packages),
            "enabled_skills": [name for name, pkg in config.skill_packages.items() if pkg.enabled],
        }

    def reset_config(self) -> SkillSystemConfig:
        new_config = SkillSystemConfig()
        self.save_config(new_config)
        return new_config
