"""Agent 工具集 — 工具、工作区和上下文。

注意：数据读取/写入工具（get_* / add_* / update_* / delete_*）
已迁移到 fitme-skills CLI，不再在此导出。
Agent 通过 execute_shell_command 调用 fitme-cli 完成数据操作。
"""
from .context import agent_context, NotAuthenticatedError, get_user_id_from_token
from agentscope.tool import execute_shell_command
from .tools.skill_resource import create_skill_resource_tool
from .tools.sandbox_manager import SandboxToolManager
from .workspace.user_workspace import (
    get_user_workspace,
    ensure_user_workspace,
    load_user_sys_prompt,
    load_user_context,
)
from .templates.templates import (
    get_template_path,
    get_skills_template_path,
    get_agent_template_path,
    get_soul_template_path,
)
from .utils.token_counter import (
    EstimateTokenCounter,
    CompatTokenCounter,
    get_token_counter,
)

__all__ = [
    # 上下文
    "agent_context",
    "NotAuthenticatedError",
    "get_user_id_from_token",
    # 系统工具
    "execute_shell_command",
    "create_skill_resource_tool",
    "SandboxToolManager",
    # 工作区
    "get_user_workspace",
    "ensure_user_workspace",
    "load_user_sys_prompt",
    "load_user_context",
    # 模板
    "get_template_path",
    "get_skills_template_path",
    "get_agent_template_path",
    "get_soul_template_path",
    # 工具类
    "EstimateTokenCounter",
    "CompatTokenCounter",
    "get_token_counter",
]
