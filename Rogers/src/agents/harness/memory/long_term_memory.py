"""长期记忆管理器

管理 MEMORY.md 长期记忆文件和每日交互日志。
提供记忆的读取、写入、更新和日志管理功能。
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("fitagent")

MEMORY_FILENAME = "MEMORY.md"
MEMORY_DIR_NAME = "memory"
BACKUP_DIR_NAME = "backup"
MEMORY_CONFIG_FILENAME = "memory_config.json"

DEFAULT_MEMORY_CONFIG = {
    "heartbeat": {
        "enabled": False,
        "every": "6h",
        "target": "main",
        "active_hours": None,
    },
}

DEFAULT_MEMORY_TEMPLATE = """# 长期记忆

## 用户画像
- 姓名：
- 健身目标：
- 偏好训练类型：
- 饮食偏好：

## 关键信息
- 重要日期（开始日期、里程碑等）：
- 历史最佳记录：
- 特殊注意事项（伤病、禁忌等）：

## 交互总结
- 最近关注的话题：
- 待解决的问题：
- 用户反馈和调整：
"""


class LongTermMemory:
    """管理用户长期记忆和每日日志。"""

    def __init__(self, working_dir: str | Path):
        self.working_dir = Path(working_dir)
        self.memory_file = self.working_dir / MEMORY_FILENAME
        self.memory_dir = self.working_dir / MEMORY_DIR_NAME
        self.backup_dir = self.working_dir / BACKUP_DIR_NAME

    def init_memory_file(self) -> bool:
        """首次使用时创建 MEMORY.md。

        Returns:
            True 如果创建了文件，False 如果已存在
        """
        if self.memory_file.exists():
            return False

        self.memory_file.write_text(DEFAULT_MEMORY_TEMPLATE, encoding="utf-8")
        logger.info(f"Created default MEMORY.md at {self.memory_file}")
        return True

    def load_memory(self) -> str:
        """读取 MEMORY.md 内容。

        Returns:
            记忆文件内容，不存在时返回默认模板
        """
        if self.memory_file.exists():
            return self.memory_file.read_text(encoding="utf-8")
        return DEFAULT_MEMORY_TEMPLATE

    def save_memory(self, content: str) -> None:
        """覆写 MEMORY.md（状态覆盖，非追加）。

        Args:
            content: 新的记忆内容
        """
        max_size = 50 * 1024
        if len(content) > max_size:
            logger.warning(f"MEMORY.md content too large ({len(content)} bytes), truncating")
            content = content[:max_size]

        self.memory_file.write_text(content, encoding="utf-8")
        logger.info(f"Saved MEMORY.md ({len(content)} bytes)")

    def append_daily_log(self, date: str | None = None, content: str = "") -> Path:
        """追加内容到当日日志。

        Args:
            date: 日期字符串 (YYYY-MM-DD)，默认今天
            content: 日志内容

        Returns:
            日志文件路径
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        self.memory_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.memory_dir / f"{date}.md"

        if not log_file.exists():
            log_file.write_text(f"# 日志 {date}\n\n", encoding="utf-8")

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(content + "\n")

        logger.info(f"Appended daily log for {date}")
        return log_file

    def get_daily_log(self, date: str) -> str | None:
        """读取指定日期日志。

        Args:
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            日志内容，不存在时返回 None
        """
        log_file = self.memory_dir / f"{self._sanitize_filename(date)}.md"
        if log_file.exists():
            return log_file.read_text(encoding="utf-8")
        return None

    def list_log_dates(self) -> list[str]:
        """返回所有有日志的日期列表。"""
        if not self.memory_dir.exists():
            return []

        dates = []
        for f in self.memory_dir.iterdir():
            if f.is_file() and f.suffix == ".md":
                match = re.match(r"^(\d{4}-\d{2}-\d{2})\.md$", f.name)
                if match:
                    dates.append(match.group(1))

        return sorted(dates, reverse=True)

    def delete_daily_log(self, date: str) -> bool:
        """删除指定日期日志。

        Args:
            date: 日期字符串 (YYYY-MM-DD)

        Returns:
            True 如果删除成功，False 如果不存在
        """
        log_file = self.memory_dir / f"{self._sanitize_filename(date)}.md"
        if log_file.exists():
            log_file.unlink()
            logger.info(f"Deleted daily log for {date}")
            return True
        return False

    def create_backup(self, date: str | None = None) -> Path | None:
        """备份当前 MEMORY.md。

        Args:
            date: 备份标记日期，默认今天

        Returns:
            备份文件路径，MEMORY.md 不存在时返回 None
        """
        if not self.memory_file.exists():
            return None

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"memory_backup_{date}_{timestamp}.md"

        backup_file.write_text(self.memory_file.read_text(encoding="utf-8"), encoding="utf-8")
        logger.info(f"Created MEMORY.md backup at {backup_file}")
        return backup_file

    @staticmethod
    def _sanitize_filename(date: str) -> str:
        sanitized = re.sub(r'[\\/:*?"<>|]', "_", date)
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", sanitized):
            raise ValueError(f"Invalid date format: {date}")
        return sanitized

    # ------------------------------------------------------------------
    # Memory update config (nightly schedule + custom prompt)
    # ------------------------------------------------------------------

    @property
    def config_file(self) -> Path:
        return self.working_dir / MEMORY_CONFIG_FILENAME

    def load_config(self) -> dict:
        """加载记忆更新配置。"""
        if self.config_file.exists():
            try:
                data = json.loads(
                    self.config_file.read_text(encoding="utf-8")
                )
                # 合并默认值
                cfg = DEFAULT_MEMORY_CONFIG.copy()
                cfg.update(data)
                return cfg
            except Exception:
                pass
        return DEFAULT_MEMORY_CONFIG.copy()

    def save_config(self, cfg: dict) -> None:
        """保存记忆更新配置。"""
        valid = DEFAULT_MEMORY_CONFIG.copy()
        for key in valid:
            if key in cfg:
                valid[key] = cfg[key]
        self.config_file.write_text(
            json.dumps(valid, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"Saved memory config to {self.config_file}")
