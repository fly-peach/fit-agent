"""Shell command tool for agent basic tools."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


def _tool_resp(text: str) -> ToolResponse:
    return ToolResponse(content=[TextBlock(type="text", text=text)])


def execute_shell_command(
    command: str,
    timeout: float = 60.0,
    cwd: str | None = None,
) -> ToolResponse:
    """Execute a shell command and return stdout/stderr.

    This mirrors QwenPaw's `execute_shell_command` name so prompts and skills
    can reuse the same calling convention.
    """
    cmd = (command or "").strip()
    if not cmd:
        return _tool_resp("命令不能为空")

    workdir = Path(cwd).expanduser() if cwd else Path.cwd()
    if not workdir.exists() or not workdir.is_dir():
        return _tool_resp(f"工作目录不存在: {workdir}")

    if isinstance(timeout, str):
        try:
            timeout = float(timeout)
        except (TypeError, ValueError):
            timeout = 60.0

    env = os.environ.copy()
    env.setdefault("PAGER", "cat")

    try:
        completed = subprocess.run(
            cmd,
            shell=True,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return _tool_resp(
            f"命令执行超时（>{timeout} 秒）: {cmd}",
        )
    except Exception as e:
        return _tool_resp(f"命令执行失败: {e}")

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if completed.returncode == 0:
        if stdout:
            if stderr:
                return _tool_resp(f"{stdout}\n[stderr]\n{stderr}")
            return _tool_resp(stdout)
        if stderr:
            return _tool_resp(f"命令执行成功（无 stdout）\n[stderr]\n{stderr}")
        return _tool_resp("命令执行成功（无输出）")

    parts = [f"命令执行失败，退出码: {completed.returncode}"]
    if stdout:
        parts.append(f"[stdout]\n{stdout}")
    if stderr:
        parts.append(f"[stderr]\n{stderr}")
    return _tool_resp("\n".join(parts))

