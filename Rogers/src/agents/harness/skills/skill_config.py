"""Skill 配置管理

提供技能配置的持久化、初始化和同步功能。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime

from pydantic import BaseModel, Field

from src.agents.harness.skills.skill_models import SkillMetadata, SkillInfo

logger = logging.getLogger("fitagent")

# 配置文件名
SKILL_CONFIG_FILENAME = "skill-config.json"
SKILL_CONFIG_VERSION = "1.0.0"


class SkillPackageConfig(BaseModel):
    """单个技能包的配置"""
    name: str
    enabled: bool = True
    auto_update: bool = True
    priority: int = 0
    config: dict[str, Any] = Field(default_factory=dict)


class SkillSystemConfig(BaseModel):
    """技能系统的全局配置"""
    version: str = SKILL_CONFIG_VERSION
    initialized: bool = False
    initialized_at: str | None = None
    last_synced_at: str | None = None
    default_skills_enabled: list[str] = Field(default_factory=list)
    skill_packages: dict[str, SkillPackageConfig] = Field(default_factory=dict)
    global_settings: dict[str, Any] = Field(default_factory=dict)


class SkillConfigManager:
    """技能配置管理器

    负责技能配置的加载、保存、初始化和同步。
    """

    def __init__(self, working_dir: str | Path):
        self.working_dir = Path(working_dir)
        self.config_path = self.working_dir / SKILL_CONFIG_FILENAME
        self._config_cache: SkillSystemConfig | None = None

    def get_config(self, force_reload: bool = False) -> SkillSystemConfig:
        """获取当前技能系统配置"""
        if self._config_cache is None or force_reload:
            if self.config_path.exists():
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._config_cache = SkillSystemConfig(**data)
                except Exception as e:
                    logger.warning(f"Failed to load skill config, using default: {e}")
                    self._config_cache = SkillSystemConfig()
            else:
                self._config_cache = SkillSystemConfig()
        return self._config_cache

    def save_config(self, config: SkillSystemConfig) -> None:
        """保存技能系统配置"""
        self.working_dir.mkdir(parents=True, exist_ok=True)
        config.last_synced_at = datetime.now().isoformat()
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
        self._config_cache = config
        logger.info(f"Saved skill config to {self.config_path}")

    def initialize_config(self, default_skill_names: list[str] | None = None) -> SkillSystemConfig:
        """初始化技能配置

        Args:
            default_skill_names: 默认启用的技能名称列表

        Returns:
            初始化后的配置
        """
        config = self.get_config()

        if config.initialized:
            logger.info("Skill config already initialized, skipping")
            return config

        config.initialized = True
        config.initialized_at = datetime.now().isoformat()

        if default_skill_names:
            config.default_skills_enabled = default_skill_names

        self.save_config(config)
        logger.info(f"Initialized skill config with {len(default_skill_names or [])} default skills")
        return config

    def update_skill_package(self, name: str, enabled: bool | None = None,
                            auto_update: bool | None = None,
                            priority: int | None = None,
                            config: dict[str, Any] | None = None) -> SkillSystemConfig:
        """更新单个技能包的配置"""
        sys_config = self.get_config()

        if name not in sys_config.skill_packages:
            sys_config.skill_packages[name] = SkillPackageConfig(name=name)

        pkg_config = sys_config.skill_packages[name]
        if enabled is not None:
            pkg_config.enabled = enabled
        if auto_update is not None:
            pkg_config.auto_update = auto_update
        if priority is not None:
            pkg_config.priority = priority
        if config is not None:
            pkg_config.config = config

        self.save_config(sys_config)
        return sys_config

    def get_skill_package(self, name: str) -> SkillPackageConfig | None:
        """获取指定技能包的配置"""
        config = self.get_config()
        return config.skill_packages.get(name)

    def is_skill_enabled(self, name: str) -> bool:
        """检查技能是否在配置中启用"""
        pkg_config = self.get_skill_package(name)
        if pkg_config:
            return pkg_config.enabled
        # 默认根据 default_skills_enabled 判断
        config = self.get_config()
        return name in config.default_skills_enabled

    def sync_with_skill_manager(self, skill_manager: Any) -> SkillSystemConfig:
        """与 SkillManager 同步配置

        从 SkillManager 扫描的技能更新配置。
        """
        config = self.get_config()

        # 获取当前所有技能
        skills = skill_manager.list_skills()

        # 更新技能包配置
        for skill in skills:
            if skill.name not in config.skill_packages:
                config.skill_packages[skill.name] = SkillPackageConfig(
                    name=skill.name,
                    enabled=skill.enabled
                )

        self.save_config(config)
        logger.info(f"Synced skill config with {len(skills)} skills")
        return config

    def get_sync_status(self) -> dict[str, Any]:
        """获取同步状态"""
        config = self.get_config()
        return {
            "initialized": config.initialized,
            "initialized_at": config.initialized_at,
            "last_synced_at": config.last_synced_at,
            "total_skill_packages": len(config.skill_packages),
            "enabled_skills": [name for name, pkg in config.skill_packages.items() if pkg.enabled]
        }

    def reset_config(self) -> SkillSystemConfig:
        """重置配置到初始状态"""
        new_config = SkillSystemConfig()
        self.save_config(new_config)
        logger.info("Reset skill config to default")
        return new_config
