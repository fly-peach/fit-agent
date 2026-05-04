"""Skill 生命周期管理器

负责扫描、加载、启用/禁用工作目录中的技能。
技能以 SKILL.md 文件定义，包含 YAML frontmatter 和 Markdown 正文。
"""
from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from typing import Any

from src.agents.harness.skills.skill_models import SkillInfo, SkillMetadata

logger = logging.getLogger("fitagent")

SKILL_MD_FILENAME = "SKILL.md"
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_yaml_simple(text: str) -> dict[str, Any]:
    """简单 YAML frontmatter 解析器（支持基础类型）。

    避免引入额外依赖，仅解析 SKILL.md 所需的基础字段。
    """
    result: dict[str, Any] = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        if value.startswith("[") and value.endswith("]"):
            items = value[1:-1].split(",")
            result[key] = [item.strip().strip("'\"") for item in items if item.strip()]
        elif value.lower() in ("true", "yes"):
            result[key] = True
        elif value.lower() in ("false", "no"):
            result[key] = False
        elif value.isdigit():
            result[key] = int(value)
        else:
            result[key] = value.strip("'\"")
    return result


def _parse_skill_md(content: str) -> tuple[dict[str, Any], str]:
    """解析 SKILL.md 文件，返回 (frontmatter_dict, body_text)。"""
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content

    fm_text = match.group(1)
    body = content[match.end():]
    return _parse_yaml_simple(fm_text), body


class SkillManager:
    """管理工作目录中技能的管理器。"""

    def __init__(self, working_dir: str | Path):
        self.working_dir = Path(working_dir)
        self.skills_dir = self.working_dir / "skills"
        self._skills_cache: dict[str, SkillInfo] = {}

    def scan_skills(self) -> dict[str, SkillInfo]:
        """扫描 skills/ 目录，加载所有有效技能。

        Returns:
            {skill_name: SkillInfo} 字典
        """
        self._skills_cache = {}

        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created skills directory: {self.skills_dir}")
            return {}

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / SKILL_MD_FILENAME
            if not skill_md.exists():
                logger.warning(f"Skipping {skill_dir}: no {SKILL_MD_FILENAME} found")
                continue

            try:
                skill_info = self._load_skill_from_dir(skill_dir)
                if skill_info:
                    self._skills_cache[skill_info.name] = skill_info
            except Exception as e:
                logger.error(f"Failed to load skill from {skill_dir}: {e}")

        logger.info(f"Scanned {len(self._skills_cache)} skills from {self.skills_dir}")
        return self._skills_cache

    def _load_skill_from_dir(self, skill_dir: Path) -> SkillInfo | None:
        """从单个技能目录加载 SKILL.md。"""
        skill_md = skill_dir / SKILL_MD_FILENAME
        content = skill_md.read_text(encoding="utf-8")

        metadata, body = _parse_skill_md(content)

        if "name" not in metadata:
            logger.warning(f"Skill {skill_dir} missing 'name' in frontmatter")
            return None

        return SkillInfo(
            name=str(metadata["name"]),
            version=str(metadata.get("version", "1.0.0")),
            description=str(metadata.get("description", "")),
            content=content,
            enabled=bool(metadata.get("enabled", True)),
            path=str(skill_dir),
            tags=metadata.get("tags", []),
        )

    def get_skill(self, name: str) -> SkillInfo | None:
        """获取指定技能的详细信息。"""
        if not self._skills_cache:
            self.scan_skills()
        return self._skills_cache.get(name)

    def list_skills(self) -> list[SkillInfo]:
        """列出所有已扫描的技能。"""
        if not self._skills_cache:
            self.scan_skills()
        return list(self._skills_cache.values())

    def enable_skill(self, name: str) -> bool:
        """启用指定技能。"""
        skill = self.get_skill(name)
        if not skill:
            return False

        skill.enabled = True
        skill_dir = Path(skill.path)
        skill_md = skill_dir / SKILL_MD_FILENAME

        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            metadata, body = _parse_skill_md(content)
            metadata["enabled"] = True
            new_content = self._rebuild_skill_md(metadata, body)
            skill_md.write_text(new_content, encoding="utf-8")

        self._skills_cache[name] = skill
        logger.info(f"Enabled skill: {name}")
        return True

    def disable_skill(self, name: str) -> bool:
        """禁用指定技能。"""
        skill = self.get_skill(name)
        if not skill:
            return False

        skill.enabled = False
        skill_dir = Path(skill.path)
        skill_md = skill_dir / SKILL_MD_FILENAME

        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            metadata, body = _parse_skill_md(content)
            metadata["enabled"] = False
            new_content = self._rebuild_skill_md(metadata, body)
            skill_md.write_text(new_content, encoding="utf-8")

        self._skills_cache[name] = skill
        logger.info(f"Disabled skill: {name}")
        return True

    def delete_skill(self, name: str) -> bool:
        """删除指定技能（包括整个技能目录）。"""
        skill = self.get_skill(name)
        if not skill:
            return False

        skill_dir = Path(skill.path)
        if skill_dir.exists():
            shutil.rmtree(skill_dir)

        self._skills_cache.pop(name, None)
        logger.info(f"Deleted skill: {name}")
        return True

    def get_enabled_skills_content(self) -> str:
        """获取所有已启用技能的内容，用于注入到 system prompt。

        Returns:
            合并后的技能描述文本
        """
        if not self._skills_cache:
            self.scan_skills()

        enabled_skills = [s for s in self._skills_cache.values() if s.enabled]
        if not enabled_skills:
            return ""

        parts = ["\n## 可用技能扩展\n"]
        for skill in enabled_skills:
            parts.append(f"\n### {skill.name} (v{skill.version})\n")
            parts.append(f"{skill.description}\n")
            # 附加 SKILL.md 正文内容（去掉 frontmatter 后的使用说明和指令）
            _, body = _parse_skill_md(skill.content)
            if body.strip():
                parts.append(body)

        return "\n".join(parts)

    def install_skill_from_zip(self, zip_path: str | Path, target_name: str | None = None) -> str:
        """从 ZIP 文件安装技能。

        Args:
            zip_path: ZIP 文件路径
            target_name: 目标技能名称（可选，默认从 SKILL.md 读取）

        Returns:
            安装后的技能名称

        Raises:
            ValueError: 如果 ZIP 无效或不包含 SKILL.md
        """
        import zipfile

        zip_path = Path(zip_path)
        if not zip_path.exists():
            raise ValueError(f"ZIP file not found: {zip_path}")

        if not zip_path.suffix.lower() == ".zip":
            raise ValueError("Only ZIP files are supported")

        max_size = 200 * 1024 * 1024
        if zip_path.stat().st_size > max_size:
            raise ValueError("Skill package too large (max 200MB)")

        self.skills_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()

            for name in names:
                if ".." in name or name.startswith("/") or name.startswith("\\"):
                    raise ValueError(f"Invalid path in skill package: {name}")

            skill_md_name = None
            for n in names:
                if n.upper().endswith(SKILL_MD_FILENAME):
                    skill_md_name = n
                    break

            if not skill_md_name:
                raise ValueError(f"No {SKILL_MD_FILENAME} found in skill package")

            skill_md_content = zf.read(skill_md_name).decode("utf-8")
            metadata, _ = _parse_skill_md(skill_md_content)

            skill_name = target_name or metadata.get("name")
            if not skill_name:
                raise ValueError("Skill name not found in SKILL.md and not specified")

            skill_name = re.sub(r'[\\/:*?"<>|]', "_", str(skill_name))
            target_dir = self.skills_dir / skill_name

            if target_dir.exists():
                shutil.rmtree(target_dir)

            target_dir.mkdir(parents=True, exist_ok=True)

            # 安全解压：逐个提取文件，避免路径穿越
            for member in zf.infolist():
                member_name = member.filename.replace("\\", "/")
                if ".." in member_name or member_name.startswith("/"):
                    raise ValueError(f"Invalid path in skill package: {member.filename}")
                zf.extract(member, target_dir)

            self.scan_skills()
            return skill_name

    @staticmethod
    def _rebuild_skill_md(metadata: dict[str, Any], body: str) -> str:
        """重建 SKILL.md 文件内容。"""
        fm_lines = ["---"]
        for key, value in metadata.items():
            if isinstance(value, list):
                fm_lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
            elif isinstance(value, bool):
                fm_lines.append(f"{key}: {'true' if value else 'false'}")
            else:
                fm_lines.append(f"{key}: {value}")
        fm_lines.append("---")
        fm_lines.append("")
        return "\n".join(fm_lines) + body
