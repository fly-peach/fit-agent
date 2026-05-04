"""Skill 系统数据模型

定义 Skill 的元数据、运行时信息和配置结构。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SkillMetadata(BaseModel):
    """Skill 元数据（从 SKILL.md frontmatter 解析）。"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    enabled: bool = True


class SkillInfo(BaseModel):
    """Skill 运行时信息。"""
    name: str
    version: str
    description: str
    content: str
    enabled: bool
    path: str
    tags: list[str] = Field(default_factory=list)


class SkillConfig(BaseModel):
    """Skill 配置选项。"""
    env_vars: dict[str, str] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
