"""
Rogers Agent - Pipeline 多智能体编排

基于 AgentScope 的多智能体管道工作流：
- Master Agent: 判断问题复杂度 → 输出思考过程 → 简单回答 or 触发 Fanout
- Fanout: SubAgent DietAnalyst + SubAgent TrainingAnalyst 依次分析
- Master Agent: 汇总 SubAgent 输出 → 流式输出最终回复

所有输出均为 SSE 流式，并标注 [Master] / [SubAgent:xxx] 标识。
"""
import asyncio
import logging
from typing import AsyncGenerator

from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.tool import Toolkit
from agentscope.pipeline import stream_printing_messages
from agentscope.memory import InMemoryMemory

from src.agents.utils.api_key_cache import api_key_cache

logger = logging.getLogger(__name__)

# ============================================================================
# Agent 工厂 & System Prompts
# ============================================================================

def _build_model(model_name: str = "qwen-turbo", user_id: int | None = None) -> DashScopeChatModel:
    api_key = api_key_cache.get(user_id) if user_id else ""
    return DashScopeChatModel(
        model_name=model_name,
        api_key=api_key,
        stream=True,
        enable_thinking=True
    )


MASTER_SYS_PROMPT = (
    "你是 Rogers，专业的健身和健康管理助手（Master Agent）。"
    "当用户提问时，先判断问题复杂度：\n"
    "1. 简单问题（闲聊、问候、常识问答）→ 直接回答。\n"
    "2. 涉及「饮食营养 + 运动训练」两方面 → 在回复末尾明确写出"
    "【需要专项分析】，并简要列出 DietAnalyst 和 TrainingAnalyst 各自的分析方向。\n"
    "用中文回答，专业且友好。"
)

DIET_SYS_PROMPT = (
    "你是 DietAnalyst，专业饮食营养分析助手。"
    "根据用户目标、身体状况和饮食偏好，给出科学、个性化的饮食建议。"
    "用中文回答。注意：输出必须精简，控制在 30 行以内，列出要点即可，严禁长篇大论。"
)

TRAINING_SYS_PROMPT = (
    "你是 TrainingAnalyst，专业运动训练分析助手。"
    "根据用户目标、体能水平和训练偏好，给出科学、个性化的训练计划建议。"
    "用中文回答。注意：输出必须精简，控制在 30 行以内，列出要点即可，严禁长篇大论。"
)


# ============================================================================
# 辅助工具
# ============================================================================

def _content_text(msg: 'Msg') -> str:
    """从 Msg 的 content 中提取纯文本，兼容 dict 和 ContentBlock 对象。"""
    c = getattr(msg, "content", msg)
    if c is None:
        return ""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for block in c:
            if hasattr(block, "text"):          # ContentBlock 对象
                parts.append(block.text or "")
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif isinstance(block.get("text"), str):
                    parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts)
    return str(c)


# ============================================================================
# 核心 Pipeline 编排（自定义流式生成器）
# ============================================================================

async def run_rogers_pipeline(msgs: list, user_id: int | None = None) -> AsyncGenerator:
    """
    Master → Fanout → Master 完整流水线.

    流程:
      Phase 1: Master 分析复杂度（流式输出）
      Phase 2: 判断是否需要 Fanout
      Phase 3: DietAnalyst → TrainingAnalyst 顺序分析（各自流式输出）
      Phase 4: Master 汇总两个 SubAgent 结果，流式输出最终回复
    """
    # ---- 创建所有 Agent（传递 user_id 以获取 API Key） ----
    def _create_pipeline_agent(name: str, sys_prompt: str, model_name: str = "qwen-turbo") -> ReActAgent:
        return ReActAgent(
            name=name,
            model=_build_model(model_name, user_id=user_id),
            sys_prompt=sys_prompt,
            toolkit=Toolkit(),
            memory=InMemoryMemory(),
            formatter=DashScopeChatFormatter(),
        )

    master = _create_pipeline_agent("Rogers-Master", MASTER_SYS_PROMPT, model_name="qwen-max")
    diet = _create_pipeline_agent("DietAnalyst", DIET_SYS_PROMPT)
    training = _create_pipeline_agent("TrainingAnalyst", TRAINING_SYS_PROMPT)

    for a in (master, diet, training):
        a.set_console_output_enabled(False)

    # 将 msgs 转为列表，避免迭代器被消耗后 master() 收到空输入
    raw_msgs = list(msgs)

    # ========================================================================
    # Phase 1: Master Agent 分析复杂度（流式）
    # ========================================================================
    master_text = ""

    async for output in stream_printing_messages(
        agents=[master],
        coroutine_task=master(raw_msgs),  # 使用 raw_msgs，避免 msgs 已被消耗
    ):
        # 处理可能有 2 或 3 个元素的 tuple
        if len(output) >= 2:
            msg, last = output[0], output[1]
            # 标注来源，保留原 role 不变
            msg.metadata = dict(getattr(msg, "metadata", {}) or {},
                                source="[Master] Rogers")
            yield msg, last
            master_text += _content_text(msg)

    # ========================================================================
    # Phase 2: 判断是否需要 Fanout
    # ========================================================================
    need_fanout = "【需要专项分析】" in master_text

    if not need_fanout:
        # 简单问题，Master 已回答完毕
        return

    user_question = _content_text(raw_msgs[-1]) if raw_msgs else ""

    # ========================================================================
    # Phase 3: Fanout — SubAgent 顺序分析（各自流式输出）
    # ========================================================================

    # --- SubAgent 1: DietAnalyst ---
    diet_input = [
        Msg(name="User",
            content=f"用户问题：{user_question}\n\n请从饮食营养角度做专业分析，给出具体建议。",
            role="user")
    ]
    diet_output = ""
    async for output in stream_printing_messages(
        agents=[diet],
        coroutine_task=diet(diet_input),
    ):
        if len(output) >= 2:
            msg, last = output[0], output[1]
            msg.metadata = dict(getattr(msg, "metadata", {}) or {},
                                source="[SubAgent] DietAnalyst")
            yield msg, last
            text = _content_text(msg)
            diet_output += text

    logger.info("DietAnalyst output length: %d chars", len(diet_output))

    # --- SubAgent 2: TrainingAnalyst ---
    training_input = [
        Msg(name="User",
            content=f"用户问题：{user_question}\n\n请从运动训练角度做专业分析，给出具体建议。",
            role="user")
    ]
    training_output = ""
    async for output in stream_printing_messages(
        agents=[training],
        coroutine_task=training(training_input),
    ):
        if len(output) >= 2:
            msg, last = output[0], output[1]
            msg.metadata = dict(getattr(msg, "metadata", {}) or {},
                                source="[SubAgent] TrainingAnalyst")
            yield msg, last
            text = _content_text(msg)
            training_output += text

    logger.info("TrainingAnalyst output length: %d chars", len(training_output))

    # ========================================================================
    # Phase 4: Master Agent 汇总分析（流式）
    # ========================================================================
    if not diet_output.strip() and not training_output.strip():
        # SubAgent 未产生有效输出，跳过汇总
        logger.warning("Both SubAgents produced empty output, skipping aggregation")
        return

    if not diet_output.strip():
        logger.warning("DietAnalyst produced empty output")
    if not training_output.strip():
        logger.warning("TrainingAnalyst produced empty output")

    agg_input = Msg(
        name="User",
        content=(
            f"用户原始问题：{user_question}\n\n"
            f"=== DietAnalyst 饮食分析 ===\n{diet_output.strip() or '（无输出）'}\n\n"
            f"=== TrainingAnalyst 训练分析 ===\n{training_output.strip() or '（无输出）'}\n\n"
            "请综合以上两项分析，用中文输出最终健身建议。要求：精简有力，控制在 40 行以内，只输出结论要点，勿重复子分析细节。"
        ),
        role="user",
    )

    async for output in stream_printing_messages(
        agents=[master],
        coroutine_task=master([agg_input]),
    ):
        if len(output) >= 2:
            msg, last = output[0], output[1]
            msg.metadata = dict(getattr(msg, "metadata", {}) or {},
                                source="[Master] Rogers")
            yield msg, last
    # ── 调用成功后刷新 API Key TTL ──
    if user_id:
        api_key_cache.touch(user_id)