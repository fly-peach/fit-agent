"""Skill 系统数据模型。"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SkillMetadata(BaseModel):
    """Skill 元数据（从 `SKILL.md` frontmatter 解析）。"""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    enabled: bool = True
    channels: list[str] = Field(default_factory=lambda: ["all"])
    config: dict[str, Any] = Field(default_factory=dict)
    source: str = "workspace"


class SkillInfo(BaseModel):
    """Skill 运行时信息。"""

    name: str
    version: str
    description: str
    content: str
    body: str
    enabled: bool
    path: str
    tags: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=lambda: ["all"])
    config: dict[str, Any] = Field(default_factory=dict)
    references: list[str] = Field(default_factory=list)
    scripts: list[str] = Field(default_factory=list)
    source: str = "workspace"


class SkillManifestEntry(BaseModel):
    """Skill registry 条目。"""

    enabled: bool = True
    channels: list[str] = Field(default_factory=lambda: ["all"])
    config: dict[str, Any] = Field(default_factory=dict)
    source: str = "workspace"
    version: str = "1.0.0"
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class SkillConfig(BaseModel):
    """Skill 配置选项。"""

    env_vars: dict[str, str] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
