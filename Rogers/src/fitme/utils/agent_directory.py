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
    """初始化 Agent 工作目录结构

    创建必要的子目录并复制默认配置文件

    Args:
        local_dir: Agent 工作目录路径

    Returns:
        bool: 初始化成功返回 True
    """
    try:
        dir_path = Path(local_dir).resolve()

        # 创建必要的子目录
        workspace_dir = dir_path / "workspace"
        sessions_dir = workspace_dir / "sessions"
        memory_dir = workspace_dir / "memory"
        skills_dir = workspace_dir / "skills"
        file_store_dir = workspace_dir / "file_store"

        for d in [workspace_dir, sessions_dir, memory_dir, skills_dir, file_store_dir]:
            d.mkdir(exist_ok=True, parents=True)

        # 复制默认配置文件（如果有模板）
        project_root = Path(__file__).parent.parent.parent.parent
        default_config_path = project_root / "data" / "agent_db" / "agent.json"
        target_config_path = dir_path / "agent.json"

        if default_config_path.exists() and not target_config_path.exists():
            shutil.copy2(default_config_path, target_config_path)

        # 复制默认技能模板（如果有）
        default_skills_path = project_root / "data" / "agent_db" / "templates" / "skills"
        if default_skills_path.exists() and not any(skills_dir.iterdir()):
            for skill_dir in default_skills_path.iterdir():
                if skill_dir.is_dir():
                    shutil.copytree(skill_dir, skills_dir / skill_dir.name)

        # 复制默认的 AGENTS.md SOUL.md 等模板
        template_files = ["AGENTS.md", "SOUL.md"]
        templates_dir = project_root / "data" / "agent_db" / "templates"
        for template_file in template_files:
            src = templates_dir / template_file
            if src.exists():
                dst = dir_path / template_file
                if not dst.exists():
                    shutil.copy2(src, dst)

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


def get_agent_subdirectory(local_dir: str, subdir: str) -> Path:
    """获取 Agent 目录下的子目录路径

    Args:
        local_dir: Agent 工作目录
        subdir: 子目录名称（如 'sessions', 'memory', 'skills'）

    Returns:
        Path: 子目录的完整路径
    """
    return Path(local_dir) / "workspace" / subdir


def is_directory_structure_complete(local_dir: str) -> bool:
    """检查 Agent 目录结构是否完整

    Args:
        local_dir: Agent 工作目录

    Returns:
        bool: 目录结构完整返回 True
    """
    try:
        dir_path = Path(local_dir).resolve()
        if not dir_path.exists():
            return False

        required_subdirs = ["workspace", "agent.json"]
        for subdir in required_subdirs:
            item = dir_path / subdir
            if not item.exists():
                return False

        return True
    except Exception:
        return False
