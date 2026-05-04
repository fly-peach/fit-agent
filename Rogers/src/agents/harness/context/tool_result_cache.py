"""工具结果文件缓存

当工具执行结果过大时，保存到文件并在上下文中替换为引用。
"""
from __future__ import annotations

import glob
import logging
import os
import re
import time
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel

logger = logging.getLogger("fitagent")


class CacheEntry(BaseModel):
    id: str
    tool_name: str
    size_bytes: int
    created_at: str


class ToolResultCache:
    """管理工具结果文件缓存。"""

    def __init__(self, working_dir: str | Path, cache_dir: str = "tool_results_cache"):
        self.working_dir = Path(working_dir)
        self.cache_dir = self.working_dir / cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def cache_result(self, session_id: str, tool_name: str, content: str) -> str:
        """保存大结果到文件。

        Args:
            session_id: 会话 ID
            tool_name: 工具名称
            content: 结果内容

        Returns:
            缓存文件 ID
        """
        safe_session = re.sub(r'[\\/:*?"<>|]', "_", session_id)
        safe_tool = re.sub(r'[\\/:*?"<>|]', "_", tool_name)

        session_cache_dir = self.cache_dir / safe_session
        session_cache_dir.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time() * 1000)
        filename = f"{timestamp}_{safe_tool}.txt"
        cache_file = session_cache_dir / filename

        cache_file.write_text(content, encoding="utf-8")
        logger.info(f"Cached tool result: {cache_file} ({len(content)} bytes)")

        return f"{safe_session}/{filename}"

    def get_cached_result(self, cache_id: str) -> str | None:
        """读取缓存结果。

        Args:
            cache_id: 缓存文件 ID (session/filename)

        Returns:
            缓存内容，不存在时返回 None
        """
        parts = cache_id.split("/", 1)
        if len(parts) != 2:
            return None

        cache_file = self.cache_dir / parts[0] / parts[1]
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")
        return None

    def list_cache(self) -> List[CacheEntry]:
        """列出所有缓存文件。"""
        entries = []
        if not self.cache_dir.exists():
            return entries

        for session_dir in self.cache_dir.iterdir():
            if not session_dir.is_dir():
                continue
            for cache_file in session_dir.iterdir():
                if cache_file.is_file():
                    stat = cache_file.stat()
                    entries.append(CacheEntry(
                        id=f"{session_dir.name}/{cache_file.name}",
                        tool_name=cache_file.stem.split("_", 1)[-1] if "_" in cache_file.stem else cache_file.stem,
                        size_bytes=stat.st_size,
                        created_at=str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))),
                    ))

        return sorted(entries, key=lambda e: e.created_at, reverse=True)

    def delete_cache(self, cache_id: str) -> bool:
        """删除指定缓存。"""
        parts = cache_id.split("/", 1)
        if len(parts) != 2:
            return False

        cache_file = self.cache_dir / parts[0] / parts[1]
        if cache_file.exists():
            cache_file.unlink()
            return True
        return False

    def clear_all(self) -> int:
        """清理所有缓存。"""
        count = 0
        if not self.cache_dir.exists():
            return 0

        for session_dir in self.cache_dir.iterdir():
            if session_dir.is_dir():
                for cache_file in session_dir.iterdir():
                    if cache_file.is_file():
                        cache_file.unlink()
                        count += 1

        logger.info(f"Cleared {count} cache files")
        return count

    def cleanup_expired(self, retention_days: int = 7) -> int:
        """清理过期缓存。

        Args:
            retention_days: 保留天数

        Returns:
            清理的文件数
        """
        cutoff = time.time() - (retention_days * 86400)
        count = 0

        if not self.cache_dir.exists():
            return 0

        for session_dir in self.cache_dir.iterdir():
            if session_dir.is_dir():
                for cache_file in session_dir.iterdir():
                    if cache_file.is_file() and cache_file.stat().st_mtime < cutoff:
                        cache_file.unlink()
                        count += 1

        logger.info(f"Cleaned up {count} expired cache files")
        return count
