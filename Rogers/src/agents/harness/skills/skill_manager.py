"""Skill 生命周期管理器。"""
from __future__ import annotations

import json
import logging
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from src.agents.harness.skills.skill_models import (
    SkillInfo,
    SkillManifestEntry,
)
from src.agents.harness.skills.skill_config import (
    SkillConfigManager,
    SkillPackageConfig,
    SkillSystemConfig,
)

logger = logging.getLogger("fitagent")

SKILL_MD_FILENAME = "SKILL.md"
SKILL_MANIFEST_FILENAME = "skill-manifest.json"
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
MAX_SKILL_PACKAGE_SIZE = 200 * 1024 * 1024
MAX_SKILL_FILE_SIZE = 10 * 1024 * 1024
BLOCKED_SCRIPT_SUFFIXES = {
    ".exe", ".bat", ".cmd", ".com", ".scr", ".msi", ".dll",
}


def _parse_yaml_simple(text: str) -> dict[str, Any]:
    """简单 YAML frontmatter 解析器（支持基础类型）。"""
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
        elif value.startswith("{") and value.endswith("}"):
            try:
                result[key] = json.loads(value)
            except json.JSONDecodeError:
                result[key] = value
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
    """解析 `SKILL.md` 文件，返回 `(frontmatter_dict, body_text)`。"""
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        return {}, content

    fm_text = match.group(1)
    body = content[match.end():]
    return _parse_yaml_simple(fm_text), body


class SkillManager:
    """管理工作目录中的 skills。"""

    def __init__(self, working_dir: str | Path):
        self.working_dir = Path(working_dir)
        self.skills_dir = self.working_dir / "skills"
        self.manifest_path = self.working_dir / SKILL_MANIFEST_FILENAME
        self._skills_cache: dict[str, SkillInfo] = {}
        self.config_manager = SkillConfigManager(working_dir)

    def _default_manifest(self) -> dict[str, Any]:
        return {"version": "1.0.0", "skills": {}}

    def _read_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return self._default_manifest()
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("manifest must be object")
            data.setdefault("version", "1.0.0")
            data.setdefault("skills", {})
            return data
        except Exception as exc:
            logger.warning("Failed to read skill manifest, using default: %s", exc)
            return self._default_manifest()

    def _write_manifest(self, manifest: dict[str, Any]) -> None:
        self.working_dir.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _normalize_channels(channels: Any) -> list[str]:
        if isinstance(channels, str) and channels.strip():
            return [channels.strip()]
        if isinstance(channels, list):
            normalized = [str(item).strip() for item in channels if str(item).strip()]
            if normalized:
                return normalized
        return ["all"]

    @staticmethod
    def _summarize_body(body: str, max_lines: int = 12, max_chars: int = 1200) -> str:
        lines = [line.rstrip() for line in body.strip().splitlines() if line.strip()]
        summary = "\n".join(lines[:max_lines])
        if len(summary) > max_chars:
            return summary[:max_chars].rstrip() + "\n..."
        return summary

    @staticmethod
    def _list_relative_files(base_dir: Path) -> list[str]:
        if not base_dir.exists():
            return []
        files: list[str] = []
        for path in sorted(base_dir.rglob("*")):
            if path.is_file():
                files.append(path.relative_to(base_dir.parent).as_posix())
        return files

    def reconcile_manifest(self) -> dict[str, Any]:
        """基于工作区真实目录更新 manifest。"""
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        manifest = self._read_manifest()
        existing = manifest.get("skills", {})
        reconciled: dict[str, Any] = {}

        for skill_dir in sorted(self.skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / SKILL_MD_FILENAME
            if not skill_md.exists():
                logger.warning("Skipping %s: no %s found", skill_dir, SKILL_MD_FILENAME)
                continue
            try:
                content = skill_md.read_text(encoding="utf-8")
                metadata, _ = _parse_skill_md(content)
                skill_name = str(metadata.get("name") or skill_dir.name)
                prior = existing.get(skill_name, {})
                entry = SkillManifestEntry(
                    enabled=bool(prior.get("enabled", metadata.get("enabled", True))),
                    channels=self._normalize_channels(
                        prior.get("channels", metadata.get("channels", ["all"])),
                    ),
                    config=prior.get("config", metadata.get("config", {})) or {},
                    source=str(prior.get("source", metadata.get("source", "workspace"))),
                    version=str(metadata.get("version", "1.0.0")),
                    description=str(metadata.get("description", "")),
                    tags=list(metadata.get("tags", [])),
                )
                reconciled[skill_name] = entry.model_dump()
            except Exception as exc:
                logger.error("Failed to reconcile skill from %s: %s", skill_dir, exc)

        manifest["skills"] = reconciled
        self._write_manifest(manifest)
        return manifest

    def scan_skills(self) -> dict[str, SkillInfo]:
        """扫描 `skills/` 目录并刷新缓存。"""
        self._skills_cache = {}
        manifest = self.reconcile_manifest()
        manifest_skills = manifest.get("skills", {})

        for skill_dir in sorted(self.skills_dir.iterdir()) if self.skills_dir.exists() else []:
            if not skill_dir.is_dir():
                continue
            try:
                skill_info = self._load_skill_from_dir(skill_dir, manifest_skills)
                if skill_info:
                    self._skills_cache[skill_info.name] = skill_info
            except Exception as exc:
                logger.error("Failed to load skill from %s: %s", skill_dir, exc)

        logger.info("Scanned %d skills from %s", len(self._skills_cache), self.skills_dir)
        return self._skills_cache

    def _load_skill_from_dir(
        self,
        skill_dir: Path,
        manifest_skills: dict[str, Any] | None = None,
    ) -> SkillInfo | None:
        """从单个技能目录加载结构化 skill 信息。"""
        skill_md = skill_dir / SKILL_MD_FILENAME
        if not skill_md.exists():
            return None

        content = skill_md.read_text(encoding="utf-8")
        metadata, body = _parse_skill_md(content)
        if "name" not in metadata:
            logger.warning("Skill %s missing 'name' in frontmatter", skill_dir)
            return None

        skill_name = str(metadata["name"])
        entry_dict = (manifest_skills or {}).get(skill_name, {})
        entry = SkillManifestEntry(
            enabled=bool(entry_dict.get("enabled", metadata.get("enabled", True))),
            channels=self._normalize_channels(
                entry_dict.get("channels", metadata.get("channels", ["all"])),
            ),
            config=entry_dict.get("config", metadata.get("config", {})) or {},
            source=str(entry_dict.get("source", metadata.get("source", "workspace"))),
            version=str(metadata.get("version", "1.0.0")),
            description=str(metadata.get("description", "")),
            tags=list(metadata.get("tags", [])),
        )

        return SkillInfo(
            name=skill_name,
            version=entry.version,
            description=entry.description,
            content=content,
            body=body,
            enabled=entry.enabled,
            path=str(skill_dir),
            tags=entry.tags,
            channels=entry.channels,
            config=entry.config,
            references=self._list_relative_files(skill_dir / "references"),
            scripts=self._list_relative_files(skill_dir / "scripts"),
            source=entry.source,
        )

    def get_skill(self, name: str) -> SkillInfo | None:
        if not self._skills_cache:
            self.scan_skills()
        return self._skills_cache.get(name)

    def list_skills(self) -> list[SkillInfo]:
        if not self._skills_cache:
            self.scan_skills()
        return list(self._skills_cache.values())

    def _update_manifest_entry(self, name: str, **updates: Any) -> bool:
        if not self._skills_cache:
            self.scan_skills()
        skill = self._skills_cache.get(name)
        if not skill:
            return False

        manifest = self._read_manifest()
        skills = manifest.setdefault("skills", {})
        current = skills.get(name, {})
        current.update(updates)
        skills[name] = current
        self._write_manifest(manifest)
        return True

    def _update_frontmatter(self, skill: SkillInfo, **updates: Any) -> None:
        skill_dir = Path(skill.path)
        skill_md = skill_dir / SKILL_MD_FILENAME
        if not skill_md.exists():
            return
        content = skill_md.read_text(encoding="utf-8")
        metadata, body = _parse_skill_md(content)
        metadata.update(updates)
        new_content = self._rebuild_skill_md(metadata, body)
        skill_md.write_text(new_content, encoding="utf-8")

    def enable_skill(self, name: str) -> bool:
        skill = self.get_skill(name)
        if not skill:
            return False
        skill.enabled = True
        self._update_frontmatter(skill, enabled=True)
        self._update_manifest_entry(name, enabled=True)
        self._skills_cache[name] = skill
        return True

    def disable_skill(self, name: str) -> bool:
        skill = self.get_skill(name)
        if not skill:
            return False
        skill.enabled = False
        self._update_frontmatter(skill, enabled=False)
        self._update_manifest_entry(name, enabled=False)
        self._skills_cache[name] = skill
        return True

    def update_skill_channels(self, name: str, channels: list[str]) -> bool:
        skill = self.get_skill(name)
        if not skill:
            return False
        normalized = self._normalize_channels(channels)
        skill.channels = normalized
        self._update_frontmatter(skill, channels=normalized)
        self._update_manifest_entry(name, channels=normalized)
        self._skills_cache[name] = skill
        return True

    def delete_skill(self, name: str) -> bool:
        skill = self.get_skill(name)
        if not skill:
            return False
        skill_dir = Path(skill.path)
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
        self._skills_cache.pop(name, None)
        manifest = self._read_manifest()
        manifest.get("skills", {}).pop(name, None)
        self._write_manifest(manifest)
        return True

    def resolve_effective_skills(self, channel_name: str = "all") -> list[SkillInfo]:
        if not self._skills_cache:
            self.scan_skills()
        resolved: list[SkillInfo] = []
        for skill in sorted(self._skills_cache.values(), key=lambda item: item.name):
            if not skill.enabled:
                continue
            if "all" in skill.channels or channel_name in skill.channels:
                resolved.append(skill)
        return resolved

    def get_enabled_skills_content(self, channel_name: str = "all") -> str:
        """返回适合注入 prompt 的精简 skill 摘要。"""
        effective_skills = self.resolve_effective_skills(channel_name)
        if not effective_skills:
            return ""

        parts = [
            "\n## 可用技能扩展",
            "以下技能已启用。默认先参考技能描述，只有在需要更多细节时，才使用 `read_skill_resource` 工具按需读取 skill 的 references/ 或 scripts/ 文件。",
        ]
        for skill in effective_skills:
            parts.append(f"\n### {skill.name} (v{skill.version})")
            if skill.description:
                parts.append(skill.description)
            parts.append(f"生效渠道：{', '.join(skill.channels)}")
            if skill.references:
                parts.append("可读参考文件：")
                parts.extend(f"- {path}" for path in skill.references)
            if skill.scripts:
                parts.append("可读脚本文件：")
                parts.extend(f"- {path}" for path in skill.scripts)
            summary = self._summarize_body(skill.body)
            if summary:
                parts.append("技能摘要：")
                parts.append(summary)
        return "\n".join(parts)

    def load_skill_file(self, skill_name: str, file_path: str) -> str | None:
        """按白名单路径读取 skill 内容。"""
        skill = self.get_skill(skill_name)
        if not skill:
            return None

        normalized = Path(file_path.replace("\\", "/"))
        normalized_text = normalized.as_posix().lstrip("/")
        if not normalized_text or normalized.is_absolute() or ".." in normalized.parts:
            return None
        if normalized_text != "SKILL.md" and not (
            normalized_text.startswith("references/")
            or normalized_text.startswith("scripts/")
        ):
            return None

        target_path = Path(skill.path) / normalized_text
        try:
            resolved = target_path.resolve(strict=True)
        except FileNotFoundError:
            return None

        skill_root = Path(skill.path).resolve()
        if skill_root not in resolved.parents:
            return None
        if not resolved.is_file():
            return None
        return resolved.read_text(encoding="utf-8")

    @staticmethod
    def _find_skill_root(extract_root: Path) -> Path:
        for skill_md in extract_root.rglob(SKILL_MD_FILENAME):
            return skill_md.parent
        raise ValueError(f"No {SKILL_MD_FILENAME} found in skill package")

    @staticmethod
    def _sanitize_skill_name(name: str) -> str:
        sanitized = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
        if not sanitized:
            raise ValueError("Skill name is empty")
        return sanitized

    def _validate_skill_tree(self, skill_root: Path) -> tuple[str, dict[str, Any]]:
        skill_md = skill_root / SKILL_MD_FILENAME
        content = skill_md.read_text(encoding="utf-8")
        metadata, _ = _parse_skill_md(content)
        skill_name = metadata.get("name")
        if not skill_name:
            raise ValueError("Skill name not found in SKILL.md")

        for file_path in skill_root.rglob("*"):
            if not file_path.is_file():
                continue
            relative = file_path.relative_to(skill_root).as_posix()
            if file_path.stat().st_size > MAX_SKILL_FILE_SIZE:
                raise ValueError(f"Skill file too large: {relative}")
            if relative.startswith("scripts/"):
                suffix = file_path.suffix.lower()
                if suffix in BLOCKED_SCRIPT_SUFFIXES:
                    raise ValueError(f"Blocked executable script: {relative}")
                if file_path.name.startswith(".") and suffix:
                    raise ValueError(f"Hidden script is not allowed: {relative}")

        return self._sanitize_skill_name(str(skill_name)), metadata

    def install_skill_from_zip(
        self,
        zip_path: str | Path,
        target_name: str | None = None,
    ) -> str:
        """从 ZIP 文件安全安装 skill。"""
        zip_path = Path(zip_path)
        if not zip_path.exists():
            raise ValueError(f"ZIP file not found: {zip_path}")
        if zip_path.suffix.lower() != ".zip":
            raise ValueError("Only ZIP files are supported")
        if zip_path.stat().st_size > MAX_SKILL_PACKAGE_SIZE:
            raise ValueError("Skill package too large (max 200MB)")

        self.skills_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            with zipfile.ZipFile(zip_path, "r") as zf:
                for member in zf.infolist():
                    member_name = member.filename.replace("\\", "/")
                    if not member_name or member_name.endswith("/"):
                        continue
                    if member.file_size > MAX_SKILL_FILE_SIZE:
                        raise ValueError(f"Skill file too large: {member.filename}")
                    if ".." in Path(member_name).parts or member_name.startswith("/"):
                        raise ValueError(f"Invalid path in skill package: {member.filename}")
                zf.extractall(temp_dir)

            skill_root = self._find_skill_root(temp_dir)
            extracted_name, metadata = self._validate_skill_tree(skill_root)
            skill_name = self._sanitize_skill_name(target_name or extracted_name)
            target_dir = self.skills_dir / skill_name
            staging_dir = self.skills_dir / f".tmp-{skill_name}"
            if staging_dir.exists():
                shutil.rmtree(staging_dir)
            shutil.copytree(skill_root, staging_dir)
            if target_dir.exists():
                shutil.rmtree(target_dir)
            staging_dir.replace(target_dir)

            self.reconcile_manifest()
            if metadata.get("enabled", True):
                self.enable_skill(skill_name)
            else:
                self.disable_skill(skill_name)
            self.scan_skills()
            return skill_name

    @staticmethod
    def _rebuild_skill_md(metadata: dict[str, Any], body: str) -> str:
        """重建 `SKILL.md` 内容。"""
        fm_lines = ["---"]
        for key, value in metadata.items():
            if isinstance(value, list):
                fm_lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
            elif isinstance(value, bool):
                fm_lines.append(f"{key}: {'true' if value else 'false'}")
            elif isinstance(value, dict):
                fm_lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
            else:
                fm_lines.append(f"{key}: {value}")
        fm_lines.append("---")
        fm_lines.append("")
        return "\n".join(fm_lines) + body

    def initialize_skill_config(
        self,
        default_skill_names: list[str] | None = None,
    ) -> SkillSystemConfig:
        if not self._skills_cache:
            self.scan_skills()
        config = self.config_manager.initialize_config(default_skill_names)
        self.sync_to_config()
        return config

    def sync_to_config(self) -> SkillSystemConfig:
        if not self._skills_cache:
            self.scan_skills()
        config = self.config_manager.get_config()
        for name, skill in self._skills_cache.items():
            if name not in config.skill_packages:
                config.skill_packages[name] = SkillPackageConfig(
                    name=name,
                    enabled=skill.enabled,
                    config=skill.config,
                )
            else:
                config.skill_packages[name].enabled = skill.enabled
                config.skill_packages[name].config = skill.config
        self.config_manager.save_config(config)
        return config

    def sync_from_config(self) -> None:
        if not self._skills_cache:
            self.scan_skills()
        config = self.config_manager.get_config()
        for name, pkg_config in config.skill_packages.items():
            if name not in self._skills_cache:
                continue
            skill = self._skills_cache[name]
            if skill.enabled != pkg_config.enabled:
                if pkg_config.enabled:
                    self.enable_skill(name)
                else:
                    self.disable_skill(name)

    def get_config(self) -> SkillSystemConfig:
        return self.config_manager.get_config()

    def get_sync_status(self) -> dict[str, Any]:
        if not self._skills_cache:
            self.scan_skills()
        status = self.config_manager.get_sync_status()
        status["total_scanned_skills"] = len(self._skills_cache)
        return status

    def reset_config(self) -> SkillSystemConfig:
        return self.config_manager.reset_config()
