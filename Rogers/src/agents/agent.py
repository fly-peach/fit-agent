"""Agent 工厂 — 从 AppConfig 构建 Agent，不再使用硬编码全局变量。"""
from __future__ import annotations

import asyncio
import logging
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

# 确保在模块加载时就读取 .env
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit, execute_python_code

from .config import AgentConfig, ModelProvider, load_agent_config
from .harness import (
    execute_shell_command,
    add_custom_food,
    add_health_metric,
    add_meal,
    add_training_plan,
    complete_training,
    create_memory_search_tool,
    create_skill_resource_tool,
    delete_meal,
    delete_training_plan,
    get_diet_today,
    get_diet_weekly_trend,
    get_food_recommendations,
    get_full_overview,
    get_health_history,
    get_health_summary,
    get_training_recommendations,
    get_training_today,
    get_training_weekly,
    get_user_profile,
    get_user_settings,
    search_foods,
    update_meal,
    update_profile,
    update_settings,
)
from .harness.workspace.user_workspace import (
    ensure_user_workspace,
    load_user_sys_prompt,
    load_user_context,
)
from .harness.skills.skill_manager import SkillManager
from .harness.templates.templates import get_skills_template_path

DEFAULT_SYSTEM_PROMPT = (
    "你是 Rogers，一个专业的健身和健康管理助手。"
    "你帮助用户制定训练计划、记录饮食、跟踪健康指标。"
    "使用你拥有的技能和工具来读取和更新用户的数据，给出专业、温暖的建议。"
    "如果用户没有登录，提示他们先登录。"
    "如果数据不存在，返回友好的提示而不是错误。"
    "用中文回答。"
)

AGENT_SKILL_INSTRUCTION = (
    "# Agent Skills\n"
    "以下目录级技能已注册到当前智能体。"
    "每个技能目录都包含一个 `SKILL.md` 以及可选的 `references/`、`scripts/`。"
    "当你要使用某个技能时，必须先通过 `read_skill_resource` 读取该技能的 `SKILL.md`，"
    "再按需读取其他附件文件，不要凭猜测使用技能。"
)

AGENT_SKILL_TEMPLATE = """## {name}
{description}
技能目录：{dir}
先用 `read_skill_resource(skill_name="{name}", file_path="SKILL.md")` 阅读主说明，再按需读取 `references/` 或 `scripts/` 下的文件。"""

MEMORY_GUIDANCE_ZH = (
    "# Memory Guidance\n"
    "你可以使用 `memory_search` 检索历史记忆。"
    "当用户询问偏好、历史决定、之前任务结论、长期约束时，优先先检索再回答。"
    "若检索到相关记忆，应基于记忆回答并保持一致；若未检索到，再明确说明无法从记忆中确认。"
)


def _load_prompt_from_files(working_dir: str, agent_cfg: AgentConfig, user_id: int | str) -> str:
    """读取工作区系统提示词文件，并兼容旧的 `agents.md + soul.md`。

    使用 PromptBuilder 处理条件区块（heartbeat / memory）。
    """
    working_path = Path(working_dir)
    parts: list[str] = []

    # 判断心跳是否启用
    heartbeat_enabled = getattr(agent_cfg.heartbeat, "enabled", False)

    if agent_cfg.sys_prompt_files:
        for prompt_file in agent_cfg.sys_prompt_files:
            prompt_path = working_path / prompt_file
            if prompt_path.exists() and prompt_path.is_file():
                parts.append(prompt_path.read_text(encoding="utf-8"))
    else:
        # 使用 PromptBuilder 加载 agents.md + soul.md，处理条件区块
        from src.agents.harness.workspace.user_workspace import PromptBuilder
        builder = PromptBuilder(
            user_dir=working_path,
            heartbeat_enabled=heartbeat_enabled,
            memory_prompt_enabled=True,
        )
        prompt = builder.build()
        if prompt:
            parts.append(prompt)

    if agent_cfg.sys_prompt:
        parts.append(agent_cfg.sys_prompt)

    return "\n\n".join(part for part in parts if part.strip())


def _build_toolkit(
    agent_cfg: AgentConfig,
    memory_manager,
    skill_manager: SkillManager,
    channel_name: str,
) -> Toolkit:
    """根据 Agent 配置构建工具集。"""
    toolkit = Toolkit(
        agent_skill_instruction=AGENT_SKILL_INSTRUCTION,
        agent_skill_template=AGENT_SKILL_TEMPLATE,
    )
    enabled_tools = set(agent_cfg.get_enabled_tools())

    tool_functions = {
        "execute_python_code": execute_python_code,
        "execute_shell_command": execute_shell_command,
        "memory_search": create_memory_search_tool(memory_manager),
        "read_skill_resource": create_skill_resource_tool(skill_manager),
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

    for tool_name, tool_func in tool_functions.items():
        if enabled_tools and tool_name not in enabled_tools:
            continue
        toolkit.register_tool_function(tool_func)

    for skill in skill_manager.resolve_effective_skills(channel_name):
        try:
            toolkit.register_agent_skill(skill.path)
        except Exception:
            # Skill tooling is best-effort; keep the agent usable if one skill
            # directory is malformed.
            continue
    return toolkit


def _build_model(agent_cfg: AgentConfig) -> DashScopeChatModel:
    """根据 Agent 的模型配置创建模型实例。"""
    model_cfg = agent_cfg.model

    # 处理 model_cfg 可能是字符串的情况（引用）
    if isinstance(model_cfg, str):
        from src.agents.config import get_config
        config = get_config()
        if model_cfg in config.models:
            model_cfg = config.models[model_cfg]
        else:
            # 回退到默认模型
            model_cfg = ModelProvider()

    # API Key 只从用户配置读取，不再从环境变量读取
    api_key = model_cfg.api_key if hasattr(model_cfg, "api_key") else ""

    if not api_key:
        raise ValueError(
            "未配置 API Key！请在「Agent 配置」页面填入您的 API Key"
        )

    # 获取模型名称，设置默认值以防万一
    model_name = "qwen-turbo"
    if hasattr(model_cfg, "model_name") and model_cfg.model_name:
        model_name = model_cfg.model_name

    # 构建模型参数字典
    model_kwargs: dict = {
        "api_key": api_key,
        "stream": True,
        "enable_thinking": True,
    }

    return DashScopeChatModel(
        model_name,
        **model_kwargs
    )


# ---------------------------------------------------------------------------
# 按用户创建 Agent 的工厂
# ---------------------------------------------------------------------------


def create_user_agent(user_id: int | str, channel_name: str = "console") -> ReActAgent:
    """为指定用户创建 ReActAgent，附带自定义系统提示词。

    确保用户工作区存在，加载 agents.md + soul.md，查询数据库获取用
    户上下文，初始化 ReMe 内存，并构建带有组合提示词的 Agent 实例。
    """
    ensure_user_workspace(user_id)

    # 使用 load_agent_config 以合并用户级 agent.json 覆盖
    agent_cfg = load_agent_config(user_id)

    # --- ReMe 内存集成 ---
    from src.agents.harness.memory.reme_light import ReMeLightMemoryManager

    working_dir = str(ensure_user_workspace(user_id))

    template_skills_dir = get_skills_template_path()
    skill_manager = SkillManager(working_dir, skills_dir=template_skills_dir)
    skill_manager.scan_skills()

    # 先构建 model，传给 memory_manager
    model = _build_model(agent_cfg)

    memory_manager = ReMeLightMemoryManager(
        working_dir=working_dir,
        agent_id=str(user_id),
    )
    # 直接设置 model 和 formatter，不需要从缓存获取
    from agentscope.formatter import DashScopeChatFormatter
    memory_manager.chat_model = model
    memory_manager.formatter = DashScopeChatFormatter()

    reme_memory = memory_manager.get_in_memory_memory()

    # 从静态 Markdown 文件构建基础提示词
    custom_prompt = _load_prompt_from_files(working_dir, agent_cfg, user_id)
    base_prompt = custom_prompt or DEFAULT_SYSTEM_PROMPT

    # 从数据库获取用户上下文（姓名、目标、健康指标、连续记录）并前置
    user_context = load_user_context(user_id)
    if user_context:
        sys_prompt = f"{user_context}\n\n{base_prompt}"
    else:
        sys_prompt = base_prompt
    sys_prompt = f"{sys_prompt}\n\n{MEMORY_GUIDANCE_ZH}"

    # 为每个用户构建独立的 toolkit，避免 memory_search 共享冲突
    toolkit = _build_toolkit(
        agent_cfg,
        memory_manager,
        skill_manager,
        channel_name,
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
    from src.agents.harness.context.lifecycle_hooks import LifecycleHooksManager
    lifecycle_hooks = LifecycleHooksManager(
        agent_cfg=agent_cfg,
        memory_manager=memory_manager,
        working_dir=working_dir,
    )
    agent.register_instance_hook(
        hook_type="pre_reply",
        hook_name="pre_reply_hook",
        hook=lifecycle_hooks.pre_reply,
    )
    agent.register_instance_hook(
        hook_type="pre_reasoning",
        hook_name="memory_compaction_hook",
        hook=lifecycle_hooks.pre_reasoning,
    )
    agent.register_instance_hook(
        hook_type="post_acting",
        hook_name="post_acting_hook",
        hook=lifecycle_hooks.post_acting,
    )
    agent.register_instance_hook(
        hook_type="post_reply",
        hook_name="post_reply_hook",
        hook=lifecycle_hooks.post_reply,
    )

    # 在 Agent 上保存 lifecycle_hooks 引用，用于生命周期管理
    agent._lifecycle_hooks = lifecycle_hooks  # type: ignore[attr-defined]
    agent._memory_manager = memory_manager  # type: ignore[attr-defined]
    agent._skill_manager = skill_manager  # type: ignore[attr-defined]

    # --- Heartbeat 集成 ---
    if agent_cfg.heartbeat.enabled:
        from src.agents.harness.memory.heartbeat_manager import HeartbeatManager
        hb_manager = HeartbeatManager(
            agent=agent,
            agent_id=str(user_id),
            workspace_dir=Path(working_dir),
        )
        # 在事件循环中调度心跳启动
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(hb_manager.start(agent_cfg.heartbeat))
        except RuntimeError:
            # 没有运行中的事件循环，使用 run
            asyncio.run(hb_manager.start(agent_cfg.heartbeat))
        agent._heartbeat_manager = hb_manager  # type: ignore[attr-defined]
        logger.info(
            "Heartbeat enabled for user %s: every=%s",
            user_id, agent_cfg.heartbeat.every,
        )

    return agent


