"""Agent 工厂 — 从 AppConfig 构建 Agent，不再使用硬编码全局变量。

注意：数据读写工具已迁移到 fitme-skills CLI，不再在此注册。
Agent 通过 execute_shell_command 调用 cli.py 完成数据操作。
"""
from __future__ import annotations

import logging
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

# 确保在模块加载时就读取 .env
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit

from src.agents.harness.memory.fitagent_memory import FitAgentSQLMemory
from .config import AgentConfig, ModelProvider, load_agent_config
from .harness import (
    create_skill_resource_tool,
)
from .harness.tools.safe_shell import create_safe_shell_tool
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


def _load_prompt_from_files(working_dir: str, agent_cfg: AgentConfig, user_id: int | str) -> str:
    """读取工作区系统提示词文件，并兼容旧的 `agents.md + soul.md`。

    使用 PromptBuilder 处理条件区块（memory）。
    """
    working_path = Path(working_dir)
    parts: list[str] = []

    if agent_cfg.sys_prompt_files:
        for prompt_file in agent_cfg.sys_prompt_files:
            prompt_path = working_path / prompt_file
            if prompt_path.exists() and prompt_path.is_file():
                parts.append(prompt_path.read_text(encoding="utf-8"))
    else:
        # 使用 PromptBuilder 加载 agents.md + soul.md，处理条件区块
        from src.agents.harness.workspace.user_workspace import (
            PromptBuilder,
            load_user_sys_prompt,
        )
        prompt = load_user_sys_prompt(
            user_id,
            memory_prompt_enabled=True,
        )
        if prompt:
            parts.append(prompt)

    if agent_cfg.sys_prompt:
        parts.append(agent_cfg.sys_prompt)

    return "\n\n".join(part for part in parts if part.strip())


async def _build_toolkit(
    agent_cfg: AgentConfig,
    skill_manager: SkillManager,
    channel_name: str,
    user_id: int | str,
    skill_filter: list[str] | None = None,
) -> Toolkit:
    """根据 Agent 配置构建工具集。

    Args:
        skill_filter: 如果提供，只注册这些名称的技能（用于 SubAgent）
    """
    toolkit = Toolkit(
        agent_skill_instruction=AGENT_SKILL_INSTRUCTION,
        agent_skill_template=AGENT_SKILL_TEMPLATE,
    )
    enabled_tools = set(agent_cfg.get_enabled_tools())

    tool_functions = {
        "read_skill_resource": create_skill_resource_tool(skill_manager),
        "execute_shell_command": create_safe_shell_tool(),
    }

    for tool_name, tool_func in tool_functions.items():
        if enabled_tools and tool_name not in enabled_tools:
            continue
        toolkit.register_tool_function(tool_func)

    # 注册技能（fitme-skills 通过 CLI 完成数据操作）
    skill_names = skill_filter if skill_filter is not None else skill_manager.get_enabled_skill_names(channel_name)
    for skill_name in skill_names:
        skill_dir = skill_manager.get_skill_dir(skill_name)
        if skill_dir is None:
            continue
        try:
            toolkit.register_agent_skill(skill_dir)
        except Exception:
            continue

    return toolkit




# ---------------------------------------------------------------------------
# 按用户创建 Agent 的工厂
# ---------------------------------------------------------------------------


async def create_main_agent(
    user_id: int | str,
    api_key: str,
    channel_name: str = "console",
    db_memory: "FitAgentSQLMemory | None" = None,
    agent_cfg: AgentConfig | None = None,
) -> ReActAgent:
    """为主子 Agent 创建 ReActAgent，拥有所有技能和数据访问权限。

    用于视觉分析后的复杂度判断和基础回复。如果任务复杂，主子 Agent
    会输出结构化标记触发 Fanout Pipeline。
    """
    if agent_cfg is None:
        agent_cfg = load_agent_config(user_id)

    working_dir = str(ensure_user_workspace(user_id))
    template_skills_dir = get_skills_template_path()
    skill_manager = SkillManager(working_dir, skills_dir=template_skills_dir)
    skill_manager.scan_skills()

    # 主子 Agent 用 reasoning_model（deepseek-v4-flash）
    model = DashScopeChatModel(
        model_name="deepseek-v4-flash",
        api_key=api_key,
        stream=True,
        enable_thinking=True,
    )

    custom_prompt = _load_prompt_from_files(working_dir, agent_cfg, user_id)
    base_prompt = custom_prompt or DEFAULT_SYSTEM_PROMPT
    user_context = load_user_context(user_id)
    sys_prompt = f"{user_context}\n\n{base_prompt}" if user_context else base_prompt

    toolkit = await _build_toolkit(agent_cfg, skill_manager, channel_name, user_id)
    agent_memory = db_memory

    agent = ReActAgent(
        name=f"{agent_cfg.name}-main",
        model=model,
        sys_prompt=sys_prompt,
        toolkit=toolkit,
        memory=agent_memory,
        formatter=DashScopeChatFormatter(),
    )
    agent._skill_manager = skill_manager
    return agent


async def create_sub_agent(
    user_id: int | str,
    api_key: str,
    sub_type: str,
    agent_cfg: AgentConfig | None = None,
) -> ReActAgent:
    """创建附子 Agent（diet / training）。

    附子 Agent 只挂载对应数据集相关的 skills，不挂载无关技能。
    """
    if agent_cfg is None:
        agent_cfg = load_agent_config(user_id)

    working_dir = str(ensure_user_workspace(user_id))
    template_skills_dir = get_skills_template_path()
    skill_manager = SkillManager(working_dir, skills_dir=template_skills_dir)
    skill_manager.scan_skills()

    model = DashScopeChatModel(
        model_name="deepseek-v4-flash",
        api_key=api_key,
        stream=True,
        enable_thinking=True,
    )

    # 根据子 Agent 类型筛选技能
    sub_skills = {
        "diet": ["fitme-diet"],
        "training": ["fitme-training", "fitme-exercise"],
    }
    skill_filter = sub_skills.get(sub_type, [])
    if not skill_filter:
        raise ValueError(f"Unknown sub agent type: {sub_type}")

    toolkit = await _build_toolkit(
        agent_cfg, skill_manager, "console", user_id,
        skill_filter=skill_filter,
    )

    sys_prompt = (
        f"你是 {sub_type} 分析子 Agent。你只能使用以下技能分析数据：{', '.join(skill_filter)}。\n"
        f"调用 CLI 时只使用与 {sub_type} 相关的命令。\n"
        f"将分析结果以结构化格式返回，供主 Agent 汇总。"
    )

    agent = ReActAgent(
        name=f"{sub_type}-analyzer",
        model=model,
        sys_prompt=sys_prompt,
        toolkit=toolkit,
        formatter=DashScopeChatFormatter(),
    )
    agent._skill_manager = skill_manager
    return agent


async def create_vision_agent(
    api_key: str,
) -> "DashScopeChatModel | None":
    """创建视觉识别模型实例（无工具，纯图像理解）。

    如果未配置 vision API Key，返回 None，表示跳过视觉分析。
    """
    if not api_key:
        return None

    return DashScopeChatModel(
        model_name="qwen-vl-max",
        api_key=api_key,
        stream=False,
    )


# 保留旧别名兼容已调用的地方
create_user_agent = create_main_agent


