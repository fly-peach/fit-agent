"""安全的 Shell 命令执行工具

包装 execute_shell_command，只允许执行：
1. fitme-cli 的合法命令
2. 白名单内的通用安全命令
"""
from __future__ import annotations

import shlex
from typing import Any, Callable

from agentscope.tool import ToolResponse, execute_shell_command


# =============================================================================
# 白名单配置
# =============================================================================

# fitme-cli 允许的子命令
FITME_ALLOWED_SUBCOMMANDS = {
    # 读取命令
    "get-user-profile",
    "get-health-summary",
    "get-health-history",
    "get-training-today",
    "get-training-weekly",
    "get-training-monthly",
    "get-training-weekly-progress",
    "get-training-recommendations",
    "get-diet-today",
    "get-diet-weekly-trend",
    "get-nutrition-progress",
    "get-food-recommendations",
    "get-user-settings",
    "search-foods",
    "get-food-categories",
    "analyze-diet-gap",
    "get-full-overview",
    "get-training-plan-detail",
    "search-exercises",
    "get-exercise-detail",
    "get-exercise-categories",
    "get-pinned-exercises",
    # 写入命令
    "update-profile",
    "add-health-metric",
    "update-health-metric",
    "delete-health-metric",
    "add-training-plan",
    "update-training-plan",
    "complete-training",
    "update-plan-exercise",
    "delete-training-plan",
    "renew-recurring-training-plan",
    "pin-exercise",
    "unpin-exercise",
    "reorder-pinned-exercises",
    "add-meal",
    "update-meal",
    "delete-meal",
    "add-custom-food",
    "update-custom-food",
    "delete-custom-food",
    "update-settings",
}

# 通用安全命令白名单
SAFE_GENERAL_COMMANDS = {
    "cd",
    "ls",
    "dir",
    "pwd",
    "echo",
}

# 危险字符/模式检测
DANGEROUS_PATTERNS = [
    ";",
    "&&",
    "||",
    "|",
    ">",
    ">>",
    "<",
    "&",
    "$(",
    "`",
    "\\",
    "*",
    "?",
    "[",
    "]",
    "{",
    "}",
    "!",
    "~",
]


# =============================================================================
# 验证逻辑
# =============================================================================


def _is_safe_general_command(parts: list[str]) -> bool:
    """检查是否是安全的通用命令。"""
    if not parts:
        return False

    cmd = parts[0].lower()

    # Windows 兼容
    if cmd.endswith(".exe"):
        cmd = cmd[:-4]

    if cmd not in SAFE_GENERAL_COMMANDS:
        return False

    # 对 cd/ls/dir/pwd/echo 进行额外检查，防止参数注入
    if cmd in ("cd", "ls", "dir", "echo", "pwd"):
        # 检查是否有危险的参数
        for part in parts[1:]:
            for pattern in DANGEROUS_PATTERNS:
                if pattern in part:
                    return False
        return True

    return False


def _is_fitme_cli_command(parts: list[str]) -> tuple[bool, str]:
    """检查是否是合法的 fitme-cli 命令。

    返回: (is_safe, error_message)
    """
    if not parts:
        return False, "命令为空"

    # 检查是否以 python 开头
    cmd = parts[0].lower()
    if cmd not in ("python", "python3", "py"):
        return False, "不是 Python 命令"

    # 寻找 cli.py
    cli_script_found = False
    token_found = False
    subcommand_found = False
    subcommand = ""

    i = 1
    while i < len(parts):
        part = parts[i]

        # 检查是否是 cli.py
        if part.endswith("cli.py") or "cli.py" in part:
            cli_script_found = True
            i += 1
            continue

        # 检查 --token
        if part == "--token":
            token_found = True
            i += 2  # 跳过 token 值
            continue

        # 找到子命令（第一个不以 - 开头的非脚本参数）
        if cli_script_found and token_found and not part.startswith("-"):
            subcommand = part
            subcommand_found = True
            break

        i += 1

    # 验证必需组件
    if not cli_script_found:
        return False, "未找到 cli.py 脚本"

    if not token_found:
        return False, "缺少 --token 参数"

    if not subcommand_found:
        return False, "缺少子命令"

    # 验证子命令
    if subcommand not in FITME_ALLOWED_SUBCOMMANDS:
        return False, f"不允许的子命令: {subcommand}"

    # 检查所有参数是否有危险字符
    for part in parts:
        for pattern in DANGEROUS_PATTERNS:
            if pattern in part:
                return False, f"包含不允许的字符: {pattern}"

    return True, ""


def validate_shell_command(command: str) -> tuple[bool, str]:
    """验证 shell 命令是否安全。

    返回: (is_safe, error_message)
    """
    try:
        parts = shlex.split(command)
    except Exception as e:
        return False, f"命令解析失败: {e}"

    if not parts:
        return False, "命令为空"

    # 检查是否是 fitme-cli
    is_fitme, fitme_error = _is_fitme_cli_command(parts)
    if is_fitme:
        return True, ""

    # 检查是否是通用安全命令
    if _is_safe_general_command(parts):
        return True, ""

    # 都不是，拒绝执行
    return False, fitme_error or "该命令不在白名单中，只允许执行 fitme-cli 和常用目录命令"


# =============================================================================
# 安全工具工厂
# =============================================================================


def create_safe_shell_tool() -> Callable:
    """创建安全的 shell 命令执行工具。

    返回的函数签名与 execute_shell_command 兼容。
    """

    async def safe_execute_shell_command(
        command: str,
        timeout: int = 300,
        **kwargs: Any,
    ) -> ToolResponse:
        """安全地执行 shell 命令。"""
        # 验证命令
        is_safe, error_msg = validate_shell_command(command)
        if not is_safe:
            return ToolResponse(
                content=f"[安全拦截] {error_msg}\n\n只允许执行：\n1. fitme-cli 命令\n2. 常用目录命令 (cd/ls/pwd/echo)",
                name="safe_shell_error",
            )

        # 验证通过，执行原命令
        return await execute_shell_command(command, timeout=timeout, **kwargs)

    return safe_execute_shell_command
