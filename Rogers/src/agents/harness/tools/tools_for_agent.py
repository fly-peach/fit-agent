"""Agent 工具注册模块

集中管理所有工具函数的注册，通过 ``build_toolkit()`` 统一构建 Toolkit。
"""
from agentscope.tool import ToolResponse, Toolkit
from agentscope.message import TextBlock

from .basic_tools.image_view import analyze_image
from .basic_tools.fitme_shell_command import execute_fitme_command
from .basic_tools.memory_tools import record_user_fact, get_user_memory, delete_user_fact_tool
from .profile_tool import get_user_profile
from .approval import create_approval_wrapper
from .skill_manager import register_all_skills, register_card_skills


async def my_search(query: str, api_key: str) -> ToolResponse:
    """一个简单的示例工具函数。

    Args:
        query (str):
            搜索查询。
        api_key (str):
            用于身份验证的 API Key。
    """
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"正在使用 API 密钥 '{api_key}' 搜索 '{query}'",
            ),
        ],
    )


# ---- 构建 Toolkit，注册所有工具和技能 ----

def build_toolkit(api_key: str = "", auth_token: str | None = None) -> Toolkit:
    """构建并返回配置好的 Toolkit，注册所有可用工具和技能。

    兼容性入口，等价于 build_master_toolkit。

    Args:
        api_key (str):
            可选的预设 DashScope API Key。如果提供，
            智能体调用图片工具时无需自行传入 api_key 参数。
        auth_token (str | None):
            可选的用户登录 Token，用于 fitme-cli 命令。
    """
    return build_master_toolkit(api_key, auth_token)


def build_master_toolkit(api_key: str = "", auth_token: str | None = None) -> Toolkit:
    """为 Master Agent 构建完整 Toolkit。

    Master Agent 拥有所有工具和技能权限。

    Args:
        api_key (str):
            可选的预设 DashScope API Key。
        auth_token (str | None):
            可选的用户登录 Token，用于 fitme-cli 命令。
    """
    toolkit = Toolkit()
    # ── 工具注册 ──
    toolkit.register_tool_function(
        create_approval_wrapper(execute_fitme_command, "execute_fitme_command"),
        preset_kwargs={"auth_token": auth_token} if auth_token else {},
    )
    toolkit.register_tool_function(my_search)
    # 图片分析工具（预设 api_key 以便智能体无需关心凭据）
    toolkit.register_tool_function(
        analyze_image,
        preset_kwargs={"api_key": api_key} if api_key else {},
    )

    # ── 用户记忆画像工具 ──
    toolkit.register_tool_function(create_approval_wrapper(record_user_fact, "record_user_fact"))
    toolkit.register_tool_function(get_user_memory)
    toolkit.register_tool_function(create_approval_wrapper(delete_user_fact_tool, "delete_user_fact_tool"))

    # ── 用户画像只读工具（无需审批） ──
    toolkit.register_tool_function(
        get_user_profile,
        preset_kwargs={"auth_token": auth_token} if auth_token else {},
    )

    # ── 技能注册（注册所有技能） ──
    register_all_skills(toolkit, include_skills=None)
    register_card_skills(toolkit, include_cards=None)

    return toolkit


def build_diet_toolkit(api_key: str = "", auth_token: str | None = None) -> Toolkit:
    """为 DietAnalyst 构建专用 Toolkit。

    DietAnalyst 只拥有饮食相关的工具和技能。

    Args:
        api_key (str):
            可选的预设 DashScope API Key。
        auth_token (str | None):
            可选的用户登录 Token，用于 fitme-cli 命令。
    """
    toolkit = Toolkit()
    # ── 工具注册 ──
    toolkit.register_tool_function(
        create_approval_wrapper(execute_fitme_command, "execute_fitme_command"),
        preset_kwargs={"auth_token": auth_token} if auth_token else {},
    )
    # 图片分析工具（预设 api_key 以便智能体无需关心凭据）
    toolkit.register_tool_function(
        analyze_image,
        preset_kwargs={"api_key": api_key} if api_key else {},
    )

    # ── 用户记忆画像工具 ──
    toolkit.register_tool_function(create_approval_wrapper(record_user_fact, "record_user_fact"))
    toolkit.register_tool_function(get_user_memory)
    toolkit.register_tool_function(create_approval_wrapper(delete_user_fact_tool, "delete_user_fact_tool"))

    # ── 用户画像只读工具（无需审批） ──
    toolkit.register_tool_function(
        get_user_profile,
        preset_kwargs={"auth_token": auth_token} if auth_token else {},
    )

    # ── 技能注册（只注册饮食相关技能） ──
    register_all_skills(
        toolkit,
        include_skills=["fitme-diet", "fitme-user", "fitme-health", "fitme-memory"]
    )

    return toolkit


def build_training_toolkit(api_key: str = "", auth_token: str | None = None) -> Toolkit:
    """为 TrainingAnalyst 构建专用 Toolkit。

    TrainingAnalyst 只拥有训练相关的工具和技能。

    Args:
        api_key (str):
            可选的预设 DashScope API Key。
        auth_token (str | None):
            可选的用户登录 Token，用于 fitme-cli 命令。
    """
    toolkit = Toolkit()
    # ── 工具注册 ──
    toolkit.register_tool_function(
        create_approval_wrapper(execute_fitme_command, "execute_fitme_command"),
        preset_kwargs={"auth_token": auth_token} if auth_token else {},
    )
    # 图片分析工具（预设 api_key 以便智能体无需关心凭据）
    toolkit.register_tool_function(
        analyze_image,
        preset_kwargs={"api_key": api_key} if api_key else {},
    )

    # ── 用户记忆画像工具 ──
    toolkit.register_tool_function(create_approval_wrapper(record_user_fact, "record_user_fact"))
    toolkit.register_tool_function(get_user_memory)
    toolkit.register_tool_function(create_approval_wrapper(delete_user_fact_tool, "delete_user_fact_tool"))

    # ── 用户画像只读工具（无需审批） ──
    toolkit.register_tool_function(
        get_user_profile,
        preset_kwargs={"auth_token": auth_token} if auth_token else {},
    )

    # ── 技能注册（只注册训练相关技能） ──
    register_all_skills(
        toolkit,
        include_skills=["fitme-training", "fitme-exercise", "fitme-user", "fitme-health", "fitme-memory"]
    )

    return toolkit


# 默认 Toolkit 实例（无预设 API Key）
register_tools = build_toolkit()