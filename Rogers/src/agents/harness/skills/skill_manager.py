"""Skill 配置持久化层 — 轻量，其余委托官方 AgentScope Toolkit API。

官方 API 参考：https://doc.agentscope.io/zh_CN/tutorial/task_agent_skill.html

设计原则：
- 扫描技能目录 → 收集 dir name → 调用 toolkit.register_agent_skill(dir) 注册
- Prompt 生成 → 委托给 toolkit.get_agent_skill_prompt()
- YAML frontmatter 解析 → 官方内部处理
- enable/disable/channel → 仅通过 skill-config.json 持久化，供前端 UI 使用
- 文件读取（load_skill_file）→ 保留白名单安全检查，供 read_skill_resource 工具使用
- ZIP 安装 → 保留，用于技能包导入
"""
from __future__ import annotations

import json
import logging
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("fitagent")

SKILL_CONFIG_FILENAME = "skill-config.json"
SKILL_MD_FILENAME = "SKILL.md"
MAX_SKILL_PACKAGE_SIZE = 200 * 1024 * 1024
MAX_SKILL_FILE_SIZE = 10 * 1024 * 1024
BLOCKED_SCRIPT_SUFFIXES = {".exe", ".bat", ".cmd", ".com", ".scr", ".msi", ".dll"}

# 文件名和目录名白名单（只允许读取这些）
SAFE_DIRS = {"SKILL.md", "references", "scripts"}


# ---------------------------------------------------------------------------
# 轻量配置模型（替代 Pydantic SkillInfo / SkillPackageConfig 等）
# ---------------------------------------------------------------------------

class SkillConfig:
    """单个技能的持久化配置。"""

    __slots__ = ("enabled", "channels", "priority", "auto_update", "extras")

    def __init__(
        self,
        enabled: bool = True,
        channels: list[str] | None = None,
        priority: int = 0,
        auto_update: bool = True,
        extras: dict[str, Any] | None = None,
    ):
        self.enabled = enabled
        self.channels = channels if channels else ["all"]
        self.priority = priority
        self.auto_update = auto_update
        self.extras = extras or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "channels": self.channels,
            "priority": self.priority,
            "auto_update": self.auto_update,
            "extras": self.extras,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillConfig":
        return cls(
            enabled=data.get("enabled", True),
            channels=data.get("channels", ["all"]),
            priority=data.get("priority", 0),
            auto_update=data.get("auto_update", True),
            extras=data.get("extras", {}),
        )


# ---------------------------------------------------------------------------
# SkillManager
# ---------------------------------------------------------------------------


class SkillManager:
    """轻量级技能管理器。

    职责：
    - 管理 skill-config.json 持久化（enable/disable/channel）
    - 扫描技能目录，区分可用 skills
    - 文件安全读取（供 read_skill_resource 工具）
    - ZIP 安装/导出
    - 委托官方 Toolkit API 完成注册和 prompt 生成

    使用方式：
        sm = SkillManager(working_dir, skills_dir)
        sm.scan_skills()
        # 在 _build_toolkit 中：
        for name in sm.get_enabled_skill_names(channel):
            toolkit.register_agent_skill(sm.get_skill_dir(name))
    """

    def __init__(self, working_dir: str | Path, skills_dir: str | Path | None = None):
        self.working_dir = Path(working_dir)
        if skills_dir is not None:
            self.skills_dir = Path(skills_dir)
        else:
            self.skills_dir = self.working_dir / "workspace" / "skills"
        self.config_path = self.working_dir / SKILL_CONFIG_FILENAME
        # name → SkillConfig
        self._configs: dict[str, SkillConfig] = {}
        # name → absolute dir path
        self._skill_dirs: dict[str, Path] = {}
        self._scanned = False

    # ------------------------------------------------------------------
    # 配置持久化
    # ------------------------------------------------------------------

    def _load_config(self) -> dict[str, dict[str, Any]]:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return {k: v for k, v in data.items() if isinstance(v, dict)}
            except Exception as exc:
                logger.warning("无法读取 skill-config.json，使用默认配置: %s", exc)
        return {}

    def _save_config(self) -> None:
        self.working_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(
                {name: cfg.to_dict() for name, cfg in self._configs.items()},
                f,
                indent=2,
                ensure_ascii=False,
            )

    # ------------------------------------------------------------------
    # 扫描
    # ------------------------------------------------------------------

    def scan_skills(self) -> dict[str, SkillConfig]:
        """扫描技能目录，与持久化配置合并。

        返回 name → SkillConfig 的字典。
        """
        self._skill_dirs.clear()
        saved = self._load_config()

        if self.skills_dir.exists():
            for skill_dir in sorted(self.skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / SKILL_MD_FILENAME
                if not skill_md.exists():
                    continue
                name = skill_dir.name
                self._skill_dirs[name] = skill_dir.resolve()
                if name in saved:
                    self._configs[name] = SkillConfig.from_dict(saved[name])
                else:
                    self._configs[name] = SkillConfig()
                    saved[name] = self._configs[name].to_dict()

        # 清理已不存在目录的配置
        stale = set(saved) - set(self._skill_dirs)
        for name in stale:
            saved.pop(name, None)
            self._configs.pop(name, None)

        self._save_config()
        self._scanned = True
        logger.info("扫描到 %d 个技能: %s", len(self._skill_dirs), list(self._skill_dirs.keys()))
        return self._configs

    def ensure_scanned(self) -> None:
        if not self._scanned:
            self.scan_skills()

    # ------------------------------------------------------------------
    # 注入到 Toolkit 的辅助方法（委托官方 API）
    # ------------------------------------------------------------------

    def get_skill_dir(self, name: str) -> str | None:
        """获取技能目录绝对路径（用于 toolkit.register_agent_skill）。"""
        self.ensure_scanned()
        path = self._skill_dirs.get(name)
        return str(path) if path else None

    def get_enabled_skill_names(self, channel_name: str = "all") -> list[str]:
        """获取指定渠道下已启用的技能名称列表（按 priority 排序）。"""
        self.ensure_scanned()
        result: list[tuple[int, str]] = []
        for name, cfg in self._configs.items():
            if not cfg.enabled:
                continue
            if "all" in cfg.channels or channel_name in cfg.channels:
                result.append((cfg.priority, name))
        result.sort(key=lambda x: x[0])
        return [name for _, name in result]

    def get_all_skill_names(self) -> list[str]:
        """获取所有技能名称（包括禁用的）。"""
        self.ensure_scanned()
        return sorted(self._skill_dirs.keys())

    # ------------------------------------------------------------------
    # 查询（供前端 API 使用）
    # ------------------------------------------------------------------

    def get_skill_config(self, name: str) -> SkillConfig | None:
        self.ensure_scanned()
        return self._configs.get(name)

    def list_skills(self) -> list[dict[str, Any]]:
        """列出所有技能的基本信息。"""
        self.ensure_scanned()
        result: list[dict[str, Any]] = []
        for name in sorted(self._skill_dirs.keys()):
            cfg = self._configs.get(name, SkillConfig())
            result.append({
                "name": name,
                "path": str(self._skill_dirs[name]),
                "enabled": cfg.enabled,
                "channels": cfg.channels,
                "priority": cfg.priority,
                "auto_update": cfg.auto_update,
            })
        return result

    def get_skill_detail(self, name: str) -> dict[str, Any] | None:
        """获取单个技能详情（含 SKILL.md 内容）。"""
        self.ensure_scanned()
        skill_dir = self._skill_dirs.get(name)
        if skill_dir is None:
            return None
        cfg = self._configs.get(name, SkillConfig())

        content = ""
        skill_md = skill_dir / SKILL_MD_FILENAME
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")

        files = self._list_skill_files(name)
        return {
            "name": name,
            "path": str(skill_dir),
            "enabled": cfg.enabled,
            "channels": cfg.channels,
            "priority": cfg.priority,
            "auto_update": cfg.auto_update,
            "content": content,
            "references": files.get("references", []),
            "scripts": files.get("scripts", []),
        }

    # ------------------------------------------------------------------
    # 修改
    # ------------------------------------------------------------------

    def set_enabled(self, name: str, enabled: bool) -> bool:
        self.ensure_scanned()
        if name not in self._configs:
            return False
        self._configs[name].enabled = enabled
        self._save_config()
        return True

    def enable_skill(self, name: str) -> bool:
        return self.set_enabled(name, True)

    def disable_skill(self, name: str) -> bool:
        return self.set_enabled(name, False)

    def set_channels(self, name: str, channels: list[str]) -> bool:
        self.ensure_scanned()
        if name not in self._configs:
            return False
        self._configs[name].channels = channels
        self._save_config()
        return True

    def update_config(self, name: str, **kwargs: Any) -> bool:
        """批量更新配置字段。"""
        self.ensure_scanned()
        if name not in self._configs:
            return False
        cfg = self._configs[name]
        if "enabled" in kwargs:
            cfg.enabled = bool(kwargs["enabled"])
        if "channels" in kwargs:
            cfg.channels = kwargs["channels"]
        if "priority" in kwargs:
            cfg.priority = int(kwargs["priority"])
        if "auto_update" in kwargs:
            cfg.auto_update = bool(kwargs["auto_update"])
        self._save_config()
        return True

    def delete_skill(self, name: str) -> bool:
        """删除技能目录及配置。"""
        self.ensure_scanned()
        path = self._skill_dirs.get(name)
        if path is None:
            return False
        shutil.rmtree(path, ignore_errors=True)
        self._skill_dirs.pop(name, None)
        self._configs.pop(name, None)
        self._save_config()
        return True

    # ------------------------------------------------------------------
    # 安全文件读取（供 read_skill_resource 工具使用）
    # ------------------------------------------------------------------

    def read_skill_file(self, skill_name: str, file_path: str) -> str | None:
        """安全读取技能目录内的文件。

        只允许读取：
        - SKILL.md
        - references/ 下的文件
        - scripts/ 下的文件

        Args:
            skill_name: 技能名称（目录名）
            file_path: 相对路径，如 "SKILL.md" 或 "references/api.md"

        Returns:
            文件内容，或 None
        """
        self.ensure_scanned()
        skill_dir = self._skill_dirs.get(skill_name)
        if skill_dir is None:
            logger.warning("技能不存在: %s", skill_name)
            return None

        normalized = Path(file_path.replace("\\", "/"))
        normalized_text = normalized.as_posix().lstrip("/")
        if not normalized_text or normalized.is_absolute() or ".." in normalized.parts:
            logger.warning("非法的文件路径: %s", file_path)
            return None

        parts = normalized_text.split("/")
        if parts[0] not in SAFE_DIRS:
            logger.warning("不允许读取的路径前缀: %s (仅允许 %s)", parts[0], SAFE_DIRS)
            return None

        target = skill_dir / normalized_text
        try:
            resolved = target.resolve(strict=True)
        except FileNotFoundError:
            return None

        if skill_dir not in resolved.parents and resolved != skill_dir:
            logger.warning("路径越权: %s", file_path)
            return None

        return resolved.read_text(encoding="utf-8")

    # ---- 兼容旧 API 别名 ----
    load_skill_file = read_skill_file

    # ------------------------------------------------------------------
    # 技能文件列表
    # ------------------------------------------------------------------

    def _list_skill_files(self, name: str) -> dict[str, list[str]]:
        """列出技能目录下 SAFE_DIRS 中的文件。"""
        skill_dir = self._skill_dirs.get(name)
        if skill_dir is None:
            return {}
        result: dict[str, list[str]] = {}
        for safe_dir in SAFE_DIRS:
            p = skill_dir / safe_dir
            if p.is_file():
                result[safe_dir] = [safe_dir]
            elif p.is_dir():
                files = []
                for f in sorted(p.rglob("*")):
                    if f.is_file():
                        files.append(f.relative_to(skill_dir).as_posix())
                result[safe_dir] = files
        return result

    # ------------------------------------------------------------------
    # ZIP 安装 / 导出
    # ------------------------------------------------------------------

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
            extracted_name = self._sanitize_skill_name(skill_root.name)
            skill_name = self._sanitize_skill_name(target_name or extracted_name)
            target_dir = self.skills_dir / skill_name
            staging_dir = self.skills_dir / f".tmp-{skill_name}"
            if staging_dir.exists():
                shutil.rmtree(staging_dir)
            shutil.copytree(skill_root, staging_dir)
            if target_dir.exists():
                shutil.rmtree(target_dir)
            staging_dir.replace(target_dir)

            self.scan_skills()
            return skill_name

    def export_skill_to_zip(self, name: str, zip_path: str | Path) -> None:
        """导出 skill 为 ZIP 文件。"""
        self.ensure_scanned()
        skill_dir = self._skill_dirs.get(name)
        if skill_dir is None:
            raise ValueError(f"Skill not found: {name}")
        tmp_base = Path(tempfile.mkdtemp())
        shutil.make_archive(str(tmp_base / name), "zip", skill_dir.parent, skill_dir.name)
        Path(str(tmp_base / name) + ".zip").rename(zip_path)
        shutil.rmtree(tmp_base, ignore_errors=True)
