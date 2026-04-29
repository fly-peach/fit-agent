"""Agent factory — builds agents from AppConfig instead of hard-coded globals."""
from __future__ import annotations

from collections import OrderedDict
from typing import Callable
import asyncio

from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit, execute_python_code, ToolResponse

from .harness.basic_tools.read_data import (
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
)
from .harness.basic_tools.write_data import (
    update_profile,
    add_health_metric,
    add_training_plan,
    complete_training,
    delete_training_plan,
    add_meal,
    update_meal,
    delete_meal,
    update_settings,
)

from .config import AgentConfig, get_config
from .user_workspace import ensure_user_workspace, load_user_sys_prompt

# ---------------------------------------------------------------------------
# Tool registry — maps tool names to callable functions
# ---------------------------------------------------------------------------

_READ_TOOL_MAP = {
    "get_user_profile": get_user_profile,
    "get_health_summary": get_health_summary,
    "get_health_history": get_health_history,
    "get_training_today": get_training_today,
    "get_training_weekly": get_training_weekly,
    "get_training_recommendations": get_training_recommendations,
    "get_diet_today": get_diet_today,
    "get_diet_weekly_trend": get_diet_weekly_trend,
    "get_food_recommendations": get_food_recommendations,
    "get_user_settings": get_user_settings,
    "get_full_overview": get_full_overview,
}

_WRITE_TOOL_MAP = {
    "update_profile": update_profile,
    "add_health_metric": add_health_metric,
    "add_training_plan": add_training_plan,
    "complete_training": complete_training,
    "delete_training_plan": delete_training_plan,
    "add_meal": add_meal,
    "update_meal": update_meal,
    "delete_meal": delete_meal,
    "update_settings": update_settings,
}

_ALL_TOOLS: dict[str, Callable] = {**_READ_TOOL_MAP, **_WRITE_TOOL_MAP}


def get_weather(location: str, date: str) -> ToolResponse:
    """Get weather data for a location and date."""
    return ToolResponse(
        content=[{"type": "text", "text": f"The weather in {location} is sunny with a temperature of 25°C."}]
    )


DEFAULT_SYSTEM_PROMPT = (
    "你是 Rogers，一个专业的健身和健康管理助手。"
    "你帮助用户制定训练计划、记录饮食、跟踪健康指标。"
    "使用你拥有的工具来读取和更新用户的数据，给出专业、温暖的建议。"
    "如果用户没有登录，提示他们先登录。"
    "如果数据不存在，返回友好的提示而不是错误。"
    "用中文回答。"
)


def _build_toolkit(agent_cfg: AgentConfig) -> Toolkit:
    """Build a Toolkit from the agent config's tool_groups."""
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)
    toolkit.register_tool_function(get_weather)

    enabled = agent_cfg.get_enabled_tools()
    if enabled:
        # Config-driven: only register tools explicitly enabled in tool_groups
        for name in enabled:
            func = _ALL_TOOLS.get(name)
            if func:
                toolkit.register_tool_function(func)
            else:
                # External/custom tool not in our map; skip silently
                pass
    else:
        # No tool_groups defined: register all tools for backward compat
        for func in _ALL_TOOLS.values():
            toolkit.register_tool_function(func)

    return toolkit


def _build_model(agent_cfg: AgentConfig) -> DashScopeChatModel:
    """Create the model instance from the agent's model config."""
    model_cfg = agent_cfg.model
    return DashScopeChatModel(
        model_cfg.model_name,
        api_key=model_cfg.api_key,
        enable_thinking=model_cfg.enable_thinking,
        stream=model_cfg.stream,
    )


def create_agent(agent_cfg: AgentConfig | None = None) -> ReActAgent:
    """Create a ReActAgent from an AgentConfig.

    If no config is provided, the active agent from the global AppConfig is used.
    """
    if agent_cfg is None:
        agent_cfg = get_config().get_active_agent()

    toolkit = _build_toolkit(agent_cfg)
    model = _build_model(agent_cfg)
    sys_prompt = agent_cfg.sys_prompt or DEFAULT_SYSTEM_PROMPT

    return ReActAgent(
        name=agent_cfg.name,
        model=model,
        sys_prompt=sys_prompt,
        toolkit=toolkit,
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
    )


# Backward compat: module-level singleton using default config
rogers_agent = create_agent()


# ---------------------------------------------------------------------------
# Per-user agent factory and cache
# ---------------------------------------------------------------------------

# Shared toolkit built once at import time — safe because all tool functions
# use contextvars for user isolation.
_shared_toolkit: Toolkit | None = None


def _get_shared_toolkit() -> Toolkit:
    global _shared_toolkit
    if _shared_toolkit is None:
        cfg = get_config().get_active_agent()
        _shared_toolkit = _build_toolkit(cfg)
    return _shared_toolkit


def create_user_agent(user_id: int | str) -> ReActAgent:
    """Create a ReActAgent for a specific user with their custom sys_prompt.

    Ensures the user workspace exists (copies templates on first use),
    loads agents.md + soul.md, and builds an agent instance.
    """
    ensure_user_workspace(user_id)

    app_cfg = get_config()
    agent_cfg = app_cfg.get_active_agent()

    custom_prompt = load_user_sys_prompt(user_id)
    sys_prompt = custom_prompt or DEFAULT_SYSTEM_PROMPT

    model = _build_model(agent_cfg)
    toolkit = _get_shared_toolkit()

    return ReActAgent(
        name=agent_cfg.name,
        model=model,
        sys_prompt=sys_prompt,
        toolkit=toolkit,
        memory=InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
    )


class AgentCache:
    """LRU cache of per-user ReActAgent instances.

    Each user gets one agent instance (created lazily). The agent's memory
    is swapped per-request via session load/save, so the instance itself
    is stateless between calls.
    """

    def __init__(self, maxsize: int = 50):
        self._maxsize = maxsize
        self._agents: OrderedDict[str, ReActAgent] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get_or_create(self, user_id: int | str) -> ReActAgent:
        async with self._lock:
            uid = str(user_id)
            if uid in self._agents:
                # Move to end (most recently used)
                self._agents.move_to_end(uid)
                return self._agents[uid]

            agent = create_user_agent(user_id)
            self._agents[uid] = agent
            self._evict_if_needed()
            return agent

    async def evict(self, user_id: int | str) -> None:
        """Remove a user's agent from cache (e.g. after config change)."""
        async with self._lock:
            self._agents.pop(str(user_id), None)

    def _evict_if_needed(self) -> None:
        while len(self._agents) > self._maxsize:
            self._agents.popitem(last=False)


# Global agent cache singleton
agent_cache = AgentCache()
