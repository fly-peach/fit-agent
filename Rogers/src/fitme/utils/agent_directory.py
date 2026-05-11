"""Agent local directory management utilities"""
import os
import shutil
from pathlib import Path
from typing import Optional


def get_default_agent_directory() -> str:
    """获取默认的 Agent 工作目录路径"""
    home_dir = Path.home()
    if os.name == "nt":  # Windows
        return str(home_dir / ".fitagent")
    else:  # macOS, Linux
        return str(home_dir / ".fitagent")


def validate_and_create_agent_directory(local_dir: str) -> bool:
    """验证并创建 Agent 工作目录

    Args:
        local_dir: 用户指定的本地目录路径

    Returns:
        bool: 目录有效且可读写返回 True，否则返回 False
    """
    try:
        dir_path = Path(local_dir).resolve()
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path.is_dir() and os.access(dir_path, os.R_OK | os.W_OK)
    except Exception as e:
        print(f"验证目录失败: {e}")
        return False


def is_valid_directory(local_dir: str) -> bool:
    """检查目录是否有效（存在且可读写）

    Args:
        local_dir: 要检查的目录路径

    Returns:
        bool: 目录有效返回 True
    """
    try:
        dir_path = Path(local_dir).resolve()
        return dir_path.exists() and dir_path.is_dir() and os.access(dir_path, os.R_OK | os.W_OK)
    except Exception:
        return False


def initialize_agent_directory(local_dir: str) -> bool:
    """初始化 Agent 配置目录。

    仅创建根目录，不再创建 workspace/sessions/memory/skills/file_store 子目录
    （数据已迁移到数据库）。

    Args:
        local_dir: Agent 配置目录路径

    Returns:
        bool: 初始化成功返回 True
    """
    try:
        dir_path = Path(local_dir).resolve()
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"初始化目录失败: {e}")
        return False


def ensure_agent_directory_exists(local_dir: str) -> bool:
    """确保 Agent 目录存在，如不存在则创建

    Args:
        local_dir: Agent 工作目录路径

    Returns:
        bool: 目录存在或创建成功返回 True
    """
    try:
        dir_path = Path(local_dir).resolve()
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path.exists() and dir_path.is_dir()
    except Exception:
        return False


def get_agent_workspace_path(user_id: int, local_dir: str | None = None) -> str:
    """获取用户的 Agent 工作区路径

    Args:
        user_id: 用户 ID（在新架构中不再使用）
        local_dir: 用户配置的本地目录，如果为 None 则使用默认路径

    Returns:
        str: Agent 工作区的绝对路径
    """
    if local_dir:
        return os.path.abspath(local_dir)
    return get_default_agent_directory()
