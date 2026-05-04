"""Agent 工具集 — 工具、记忆、钩子、工作区、会话和上下文。"""
from .context import agent_context, NotAuthenticatedError, get_user_id_from_token
from .context.lifecycle_hooks import LifecycleHooksManager
from .tools.basic.read_data import (
    get_user_profile,
    get_health_summary,
    get_health_history,
    get_training_today,
    get_training_weekly,
    get_training_recommendations,
    get_diet_today,
    get_diet_weekly_trend,
    get_food_recommendations,
    get_user_settings,
    get_full_overview,
    search_foods,
    get_db,
    require_user,
    _current_user_id,
    _current_db,
)
from .tools.basic.write_data import (
    update_profile,
    add_health_metric,
    add_training_plan,
    complete_training,
    delete_training_plan,
    add_meal,
    update_meal,
    delete_meal,
    update_settings,
    add_custom_food,
)
from .tools.memory_search import create_memory_search_tool
from .memory.reme_light import ReMeLightMemoryManager
from .hooks.memory_compaction import create_memory_compaction_hook
from .workspace.user_workspace import (
    get_user_workspace,
    get_user_sessions_dir,
    ensure_user_workspace,
    load_user_sys_prompt,
    load_user_context,
)
from .sessions.user_session import UserSession
from .utils.token_counter import EstimateTokenCounter, get_token_counter

__all__ = [
    # 上下文
    "agent_context",
    "NotAuthenticatedError",
    "get_user_id_from_token",
    "LifecycleHooksManager",
    # 读取工具
    "get_user_profile",
    "get_health_summary",
    "get_health_history",
    "get_training_today",
    "get_training_weekly",
    "get_training_recommendations",
    "get_diet_today",
    "get_diet_weekly_trend",
    "get_food_recommendations",
    "get_user_settings",
    "get_full_overview",
    "search_foods",
    "get_db",
    "require_user",
    "_current_user_id",
    "_current_db",
    # 写入工具
    "update_profile",
    "add_health_metric",
    "add_training_plan",
    "complete_training",
    "delete_training_plan",
    "add_meal",
    "update_meal",
    "delete_meal",
    "update_settings",
    "add_custom_food",
    # 记忆
    "create_memory_search_tool",
    "ReMeLightMemoryManager",
    # 钩子
    "create_memory_compaction_hook",
    # 工作区
    "get_user_workspace",
    "get_user_sessions_dir",
    "ensure_user_workspace",
    "load_user_sys_prompt",
    "load_user_context",
    # 会话
    "UserSession",
    # 工具类
    "EstimateTokenCounter",
    "get_token_counter",
]
