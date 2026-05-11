"""Agent 工厂 — 从 AppConfig 构建 Agent，不再使用硬编码全局变量。

注意：数据读写工具已迁移到 fitme-skills CLI，不再在此注册。
Agent 通过 execute_shell_command 调用 cli.py 完成数据操作。

代码执行已迁移到 AgentScope Runtime 沙箱（SandboxService），通过 BaseSandbox
提供安全的 run_ipython_cell / run_shell_command，替代直接 execute_python_code / execute_shell_command。
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
from .harness.tools.sandbox_manager import SandboxToolManager
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
    sandbox_manager: "SandboxToolManager | None" = None,
) -> Toolkit:
    """根据 Agent 配置构建工具集。

    代码执行工具使用 AgentScope Runtime 沙箱（BaseSandbox）：
    - run_ipython_cell: 在隔离 Docker 容器中执行 Python 代码
    - run_shell_command: 在隔离 Docker 容器中执行 shell 命令
    """
    toolkit = Toolkit(
        agent_skill_instruction=AGENT_SKILL_INSTRUCTION,
        agent_skill_template=AGENT_SKILL_TEMPLATE,
    )
    enabled_tools = set(agent_cfg.get_enabled_tools())

    tool_functions = {
        "read_skill_resource": create_skill_resource_tool(skill_manager),
    }

    for tool_name, tool_func in tool_functions.items():
        if enabled_tools and tool_name not in enabled_tools:
            continue
        toolkit.register_tool_function(tool_func)

    # 注册沙箱工具（替代原生 execute_python_code / execute_shell_command）
    if sandbox_manager is not None:
        sandbox = await sandbox_manager.connect(session_id="default", user_id=user_id)
        sandbox_manager.register_tools(toolkit, sandbox)

    # 注册技能（fitme-skills 通过 CLI 完成数据操作）
    for skill_name in skill_manager.get_enabled_skill_names(channel_name):
        skill_dir = skill_manager.get_skill_dir(skill_name)
        if skill_dir is None:
            continue
        try:
            toolkit.register_agent_skill(skill_dir)
        except Exception:
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

    # 最简单的调用方式，只传必要的参数
    return DashScopeChatModel(
        model_name=model_name,
        api_key=api_key,
        stream=True,
        enable_thinking=True,
    )


# ---------------------------------------------------------------------------
# 按用户创建 Agent 的工厂
# ---------------------------------------------------------------------------


async def create_user_agent(
    user_id: int | str,
    channel_name: str = "console",
    db_memory: "FitAgentSQLMemory | None" = None,
    sandbox_manager: "SandboxToolManager | None" = None,
) -> ReActAgent:
    """为指定用户创建 ReActAgent，附带自定义系统提示词。

    确保用户工作区存在，加载 agents.md + soul.md，查询数据库获取用
    户上下文，并构建 Agent 实例。

    若传入 db_memory（FitAgentSQLMemory），则 Agent 的对话消息会自
    动持久化到 agent_memory.db，无需手动 add_message。
    """
    ensure_user_workspace(user_id)

    # 使用 load_agent_config 以合并用户级 agent.json 覆盖
    agent_cfg = load_agent_config(user_id)

    working_dir = str(ensure_user_workspace(user_id))

    template_skills_dir = get_skills_template_path()
    skill_manager = SkillManager(working_dir, skills_dir=template_skills_dir)
    skill_manager.scan_skills()

    # 构建 model
    model = _build_model(agent_cfg)

    # 从静态 Markdown 文件构建基础提示词
    custom_prompt = _load_prompt_from_files(working_dir, agent_cfg, user_id)
    base_prompt = custom_prompt or DEFAULT_SYSTEM_PROMPT

    # 从数据库获取用户上下文（姓名、目标、健康指标、连续记录）并前置
    user_context = load_user_context(user_id)
    if user_context:
        sys_prompt = f"{user_context}\n\n{base_prompt}"
    else:
        sys_prompt = base_prompt

    # 为每个用户构建独立的 toolkit
    toolkit = await _build_toolkit(
        agent_cfg,
        skill_manager,
        channel_name,
        user_id,
        sandbox_manager,
    )

    # 优先使用 db_memory（FitAgentSQLMemory），否则回退到纯内存
    agent_memory = db_memory

    agent = ReActAgent(
        name=agent_cfg.name,
        model=model,
        sys_prompt=sys_prompt,
        toolkit=toolkit,
        memory=agent_memory,
        formatter=DashScopeChatFormatter(),
    )

    agent._skill_manager = skill_manager  # type: ignore[attr-defined]

    return agent


