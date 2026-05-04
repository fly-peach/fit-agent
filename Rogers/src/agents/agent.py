"""Agent 工厂 — 从 AppConfig 构建 Agent，不再使用硬编码全局变量。"""
from __future__ import annotations

from collections import OrderedDict
from typing import Callable
import asyncio

from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit, execute_python_code, ToolResponse

from .harness.tools.basic.read_data import (
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
)
from .harness.tools.basic.write_data import (
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
from .harness.tools.basic.image_view import view_image

from .config import AgentConfig, get_config, load_agent_config
from .harness.workspace.user_workspace import (
    ensure_user_workspace,
    load_user_sys_prompt,
    load_user_context,
)

# ---------------------------------------------------------------------------
# 工具注册表 — 映射工具名称到可调用函数
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
    "search_foods": search_foods,
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
    "add_custom_food": add_custom_food,
}

_MULTIMODAL_TOOL_MAP = {
    "view_image": view_image,
}

_ALL_TOOLS: dict[str, Callable] = {**_READ_TOOL_MAP, **_WRITE_TOOL_MAP, **_MULTIMODAL_TOOL_MAP}


def get_weather(location: str, date: str) -> ToolResponse:
    """获取指定位置和日期的天气数据。"""
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
    """根据 Agent 配置构建工具集。"""
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)
    toolkit.register_tool_function(get_weather)

    enabled = agent_cfg.get_enabled_tools()
    if enabled:
        # 配置驱动：仅注册 tool_groups 中明确启用的工具
        for name in enabled:
            func = _ALL_TOOLS.get(name)
            if func:
                toolkit.register_tool_function(func)
            else:
                # 外部/自定义工具不在映射表中，静默跳过
                pass
    else:
        # 未定义 tool_groups：注册所有工具以向后兼容
        for func in _ALL_TOOLS.values():
            toolkit.register_tool_function(func)

    return toolkit


# 内置支持思考模式的模型列表（DashScope 官方支持 enable_thinking=True 的模型）
_THINKING_MODELS = {
    # Qwen3.5 系列
    "qwen3.5-plus", "qwen3.5-flash",
    # Qwen3.6 系列
    "qwen3.6-plus", "qwen3.6-max-preview",
    # Qwen3 系列
    "qwen3-max", "qwen3-plus", "qwen3-turbo",
    # QwQ 系列
    "qwq-plus", "qwq-32b",
    # Qwen2.5 指令系列
    "qwen2.5-72b-instruct", "qwen2.5-32b-instruct",
    "qwen2.5-14b-instruct", "qwen2.5-7b-instruct",
    # Qwen-Max / Plus / Turbo 系列
    "qwen-max", "qwen-max-longcontext", "qwen-plus", "qwen-turbo",
}


def _model_supportes_thinking(model_name: str) -> bool:
    """根据模型名称判断是否支持思考模式。"""
    name = model_name.lower().strip()
    return name in _THINKING_MODELS


def _build_model(agent_cfg: AgentConfig) -> DashScopeChatModel:
    """根据 Agent 的模型配置创建模型实例。"""
    import os
    model_cfg = agent_cfg.model
    # 空字符串时回退到环境变量
    api_key = model_cfg.api_key or os.getenv("DASHSCOPE_API_KEY", "")
    # qwen3.5-flash 是视觉+文本模型，但不含 -vl 后缀，需要显式启用多模态 API
    return DashScopeChatModel(
        model_cfg.model_name,
        api_key=api_key,
        # enable_thinking=_model_supportes_thinking(model_cfg.model_name),
        enable_thinking=True,
        stream=model_cfg.stream,
        multimodality=True,
    )


def create_agent(agent_cfg: AgentConfig | None = None) -> ReActAgent:
    """从 AgentConfig 创建 ReActAgent。

    若未提供配置，则使用全局 AppConfig 中的活跃 Agent。
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


# 向后兼容：模块级单例，使用默认配置
rogers_agent = create_agent()


# ---------------------------------------------------------------------------
# 按用户创建 Agent 的工厂和缓存
# ---------------------------------------------------------------------------

# 共享工具集，在导入时构建一次 —— 安全，因为所有工具函数都使用
# contextvars 实现用户隔离。
_shared_toolkit: Toolkit | None = None


def _get_shared_toolkit() -> Toolkit:
    global _shared_toolkit
    if _shared_toolkit is None:
        cfg = get_config().get_active_agent()
        _shared_toolkit = _build_toolkit(cfg)
    return _shared_toolkit


def create_user_agent(user_id: int | str) -> ReActAgent:
    """为指定用户创建 ReActAgent，附带自定义系统提示词。

    确保用户工作区存在，加载 agents.md + soul.md，查询数据库获取用
    户上下文，初始化 ReMe 内存，并构建带有组合提示词的 Agent 实例。
    """
    ensure_user_workspace(user_id)

    # 使用 load_agent_config 以合并用户级 agent.json 覆盖
    agent_cfg = load_agent_config(user_id)

    # 从静态 Markdown 文件构建基础提示词
    custom_prompt = load_user_sys_prompt(user_id)
    base_prompt = custom_prompt or DEFAULT_SYSTEM_PROMPT

    # 从数据库获取用户上下文（姓名、目标、健康指标、连续记录）并前置
    user_context = load_user_context(user_id)
    if user_context:
        sys_prompt = f"{user_context}\n\n{base_prompt}"
    else:
        sys_prompt = base_prompt

    model = _build_model(agent_cfg)

    # --- ReMe 内存集成 ---
    from src.agents.harness.memory.reme_light import ReMeLightMemoryManager

    working_dir = str(ensure_user_workspace(user_id))
    memory_manager = ReMeLightMemoryManager(
        working_dir=working_dir,
        agent_id=str(user_id),
    )
    reme_memory = memory_manager.get_in_memory_memory()

    # 为每个用户构建独立的 toolkit，避免 memory_search 共享冲突
    toolkit = _build_toolkit(agent_cfg)

    # 注册 memory_search 工具
    from src.agents.harness.tools.memory_search import create_memory_search_tool
    toolkit.register_tool_function(
        create_memory_search_tool(memory_manager),
    )

    agent = ReActAgent(
        name=agent_cfg.name,
        model=model,
        sys_prompt=sys_prompt,
        toolkit=toolkit,
        memory=reme_memory if reme_memory else InMemoryMemory(),
        formatter=DashScopeChatFormatter(),
    )

    # 注册上下文压缩钩子
    from src.agents.harness.hooks.memory_compaction import create_memory_compaction_hook
    hook = create_memory_compaction_hook(memory_manager)
    agent.register_instance_hook(
        hook_type="pre_reasoning",
        hook_name="memory_compaction_hook",
        hook=hook,
    )

    # 在 Agent 上保存 memory_manager 引用，用于生命周期管理
    agent._memory_manager = memory_manager  # type: ignore[attr-defined]

    return agent


class AgentCache:
    """按用户缓存 ReActAgent 实例的 LRU 缓存。

    每个用户一个 Agent 实例（懒加载创建）。Agent 的内存通过 session
    的加载/保存在每次请求间交换，因此实例本身在调用之间是无状态的。
    """

    def __init__(self, maxsize: int = 50):
        self._maxsize = maxsize
        self._agents: OrderedDict[str, ReActAgent] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get_or_create(self, user_id: int | str) -> ReActAgent:
        async with self._lock:
            uid = str(user_id)
            if uid in self._agents:
                # 移到末尾（最近使用）
                self._agents.move_to_end(uid)
                return self._agents[uid]

            agent = create_user_agent(user_id)
            self._agents[uid] = agent
            self._evict_if_needed()
            return agent

    async def evict(self, user_id: int | str) -> None:
        """从缓存中移除用户的 Agent（例如配置变更后）。"""
        async with self._lock:
            self._agents.pop(str(user_id), None)

    def _evict_if_needed(self) -> None:
        while len(self._agents) > self._maxsize:
            self._agents.popitem(last=False)


# 全局 Agent 缓存单例
agent_cache = AgentCache()
