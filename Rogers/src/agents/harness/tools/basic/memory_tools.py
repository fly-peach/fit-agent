"""AI 本地记忆编辑工具

让 AI 代理能在对话中直接读取和编辑工作区的记忆文件（MEMORY.md 和每日日志）。
替代「AI 写日记 → MemoryOptimizer 提炼」的间接方案，改为 AI 自主维护。
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

from src.agents.harness.context import get_user_id_from_token, NotAuthenticatedError
from src.agents.harness.workspace.user_workspace import get_user_workspace
from src.agents.harness.tools.basic.read_data import (
    _current_user_id,
)

logger = logging.getLogger("fitagent")

# 安全限制
MAX_FILE_SIZE = 100 * 1024  # 100KB
ALLOWED_FILES = {"MEMORY.md"}
ALLOWED_DIR = "memory"


def _resolve_workspace_path() -> Path | None:
    """从当前 context 获取用户工作区路径。"""
    user_id = _current_user_id.get(None)
    if user_id is None:
        return None
    try:
        return get_user_workspace(int(user_id))
    except Exception:
        return None


def _validate_path(workspace: Path, filepath: str) -> Path | None:
    """校验文件路径，防止路径穿越。

    只允许读取：
    - MEMORY.md（工作区根目录）
    - memory/YYYY-MM-DD.md（记忆日志目录）
    """
    clean = Path(filepath).as_posix().strip("/")
    target = (workspace / clean).resolve()

    # 必须在工作区内
    if not str(target).startswith(str(workspace.resolve())):
        return None

    # 只允许 MEMORY.md 或 memory/*.md
    if target.name == "MEMORY.md" and target.parent == workspace:
        return target
    if target.parent == (workspace / "memory") and target.suffix == ".md":
        return target

    return None


def read_memory_file(filename: str = "MEMORY.md") -> ToolResponse:
    """读取指定的记忆文件内容。

    可读取 MEMORY.md（长期记忆）或 memory/YYYY-MM-DD.md（每日日志）。
    在回答需要参考历史记录、用户偏好、先前决策时优先使用此工具。

    Args:
        filename: 文件名，默认为 "MEMORY.md"。
                  也可指定 "memory/2026-05-07.md" 格式的每日日志。

    Returns:
        ToolResponse: 文件内容文本。
    """
    workspace = _resolve_workspace_path()
    if workspace is None:
        return ToolResponse(
            content=[TextBlock(type="text", text="错误：无法获取用户工作区，请确认已登录")],
        )

    target = _validate_path(workspace, filename)
    if target is None:
        return ToolResponse(
            content=[TextBlock(
                type="text",
                text=f"错误：不允许访问该文件。只允许读取 MEMORY.md 或 memory/ 目录下的 .md 文件。",
            )],
        )

    if not target.exists():
        return ToolResponse(
            content=[TextBlock(type="text", text=f"文件不存在：{filename}")],
        )

    content = target.read_text(encoding="utf-8")
    size = len(content)

    logger.info("memory_tool read: %s (%d bytes)", filename, size)
    return ToolResponse(
        content=[TextBlock(type="text", text=content)],
    )


def write_memory_file(filename: str, content: str) -> ToolResponse:
    """写入覆写指定的记忆文件。

    用于更新 MEMORY.md（精炼长期记忆）或创建每日日志。
    写入 MEMORY.md 时注意保持精简，删除过时内容，保留核心决策和用户偏好。

    Args:
        filename: 文件名，如 "MEMORY.md" 或 "memory/2026-05-07.md"。
        content: 要写入的完整内容（覆写模式，非追加）。

    Returns:
        ToolResponse: 操作结果。
    """
    workspace = _resolve_workspace_path()
    if workspace is None:
        return ToolResponse(
            content=[TextBlock(type="text", text="错误：无法获取用户工作区，请确认已登录")],
        )

    target = _validate_path(workspace, filename)
    if target is None:
        return ToolResponse(
            content=[TextBlock(type="text", text="错误：不允许写入该文件")],
        )

    if len(content) > MAX_FILE_SIZE:
        return ToolResponse(
            content=[TextBlock(
                type="text",
                text=f"错误：文件内容过大（{len(content)} bytes），最大允许 {MAX_FILE_SIZE} bytes",
            )],
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    logger.info("memory_tool write: %s (%d bytes)", filename, len(content))
    return ToolResponse(
        content=[TextBlock(type="text", text=f"已成功写入 {filename}（{len(content)} bytes）")],
    )


def append_daily_log(date: str | None = None, content: str = "") -> ToolResponse:
    """追加内容到指定日期的每日日志。

    用于记录对话中的重要信息、用户偏好、决策等，供后续记忆提炼参考。
    如需覆盖整个日志文件请使用 write_memory_file。

    Args:
        date: 日期 "YYYY-MM-DD" 格式，默认今天。
        content: 要追加的内容。

    Returns:
        ToolResponse: 操作结果。
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    workspace = _resolve_workspace_path()
    if workspace is None:
        return ToolResponse(
            content=[TextBlock(type="text", text="错误：无法获取用户工作区，请确认已登录")],
        )

    log_dir = workspace / "memory"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{date}.md"

    if not log_file.exists():
        log_file.write_text(f"# 日志 {date}\n\n", encoding="utf-8")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(content + "\n")

    total_size = log_file.stat().st_size
    logger.info("memory_tool append: memory/%s.md (+%d bytes, total=%d)", date, len(content), total_size)
    return ToolResponse(
        content=[TextBlock(type="text", text=f"已追加到 {date} 的日志（共 {total_size} bytes）")],
    )
