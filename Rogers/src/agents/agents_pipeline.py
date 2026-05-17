"""
Rogers Agent - Pipeline 多智能体编排

基于 AgentScope 的多智能体管道工作流：
- Master Agent: 判断问题复杂度 → 输出思考过程 → 简单回答 or 触发 Fanout
- Fanout: SubAgent DietAnalyst + SubAgent TrainingAnalyst 依次分析
- Master Agent: 汇总 SubAgent 输出 → 流式输出最终回复

所有输出均为 SSE 流式，并标注 [Master] / [SubAgent:xxx] 标识。
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine

from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.formatter import DashScopeChatFormatter
from agentscope.token import CharTokenCounter
from agentscope.pipeline import stream_printing_messages
from pydantic import BaseModel, Field, model_validator

from src.agents.harness.memory.fit_memory import FitAsyncSQLAlchemyMemory
from src.agents.harness.tools.approval import set_session_context, clear_session_context


from src.agents.utils.api_key_cache import api_key_cache

logger = logging.getLogger(__name__)

# ============================================================================
# Agent 工厂 & System Prompts
# ============================================================================

def _load_sys_prompt(name: str) -> str:
    path = Path(__file__).resolve().parent / "harness" / "templates" / "sys_prompt" / f"{name}.md"
    return path.read_text(encoding="utf-8").strip()

MASTER_SYS_PROMPT = _load_sys_prompt("master")
DIET_SYS_PROMPT = _load_sys_prompt("diet_analyst")
TRAINING_SYS_PROMPT = _load_sys_prompt("training_analyst")


class UserFact(BaseModel):
    category: str = Field(description="分类: food/exercise/health/goal/achievement/personality/note")
    key: str = Field(description="属性名，如 favorite_foods")
    value: str = Field(description="具体内容")
    confidence: float = Field(default=1.0, description="置信度 0.0~1.0")
    source: str = Field(default="extracted", description="explicit/inferred/extracted")


class FitSummary(BaseModel):
    user_profile: str = Field(
        max_length=200,
        description="用户基本身体状况和目标（体重、体脂、健身目标）",
    )
    recent_activities: str = Field(
        max_length=400,
        description="近期的训练完成情况和饮食记录要点",
    )
    pending_recommendations: str = Field(
        max_length=200,
        description="待执行的建议或未完成的计划",
    )
    user_preferences: str = Field(
        max_length=200,
        description="用户的偏好、禁忌和特殊要求",
    )
    user_facts_changed: list[UserFact] = Field(
        default_factory=list,
        description="本次对话中新发现或更新的用户画像事实",
    )
    user_facts_json: str = Field(
        default="[]",
        description="user_facts_changed 的 JSON 序列化，由 validator 自动填充",
    )

    @model_validator(mode="after")
    def sync_facts_json(self):
        if self.user_facts_changed:
            self.user_facts_json = json.dumps(
                [f.model_dump() for f in self.user_facts_changed],
                ensure_ascii=False,
            )
        return self


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

async def run_rogers_pipeline(
    msgs,
    user_id: int | None = None,
    session_id: str = "",
    db_engine: AsyncEngine | None = None,
    auth_token: str | None = None,
    auto_approve_enabled: bool = False,
) -> AsyncGenerator:
    """
    Master → Fanout → Master 完整流水线.

    流程:
      Phase 1: Master 分析复杂度（流式输出）
      Phase 2: 判断是否需要 Fanout
      Phase 3: DietAnalyst → TrainingAnalyst 顺序分析（各自流式输出）
      Phase 4: Master 汇总两个 SubAgent 结果，流式输出最终回复
      Phase 5: 保存记录到 fituser.db
    """
    uid = str(user_id) if user_id else "default"
    sid = session_id or "default"

    def _build_model(model_name: str = "qwen-turbo", user_id: int | None = None, enable_thinking = True) -> DashScopeChatModel:
            api_key = api_key_cache.get(user_id) if user_id else ""
            return DashScopeChatModel(
                model_name=model_name,
                api_key=api_key or "dummy",  # user_id 为 None 时用占位 key，不影响运行
                stream=True,
                enable_thinking=enable_thinking
            )
    # ---- 创建所有 Agent（传递 user_id 以获取 API Key）----
    def _create_pipeline_agent(name: str, sys_prompt: str, model_name: str = "qwen-turbo", enable_thinking: bool = False) -> ReActAgent:
        if db_engine:
            memory = FitAsyncSQLAlchemyMemory(
                engine_or_session=db_engine,
                user_id=uid,
                session_id=sid,
            )
        else:
            from agentscope.memory import InMemoryMemory
            memory = InMemoryMemory()

        user_api_key = api_key_cache.get(user_id) if user_id else ""
        from src.agents.harness.tools.tools_for_agent import (
            build_master_toolkit,
            build_diet_toolkit,
            build_training_toolkit,
        )
        if "Master" in name:
            toolkit = build_master_toolkit(api_key=user_api_key or "", auth_token=auth_token)
        elif "Diet" in name:
            toolkit = build_diet_toolkit(api_key=user_api_key or "", auth_token=auth_token)
        elif "Training" in name:
            toolkit = build_training_toolkit(api_key=user_api_key or "", auth_token=auth_token)
        else:
            toolkit = build_master_toolkit(api_key=user_api_key or "", auth_token=auth_token)

        kwargs = dict(
            name=name,
            model=_build_model(model_name, user_id=user_id, enable_thinking=enable_thinking),
            sys_prompt=sys_prompt,
            toolkit=toolkit,
            memory=memory,
            formatter=DashScopeChatFormatter(),
        )

        if "Master" in name:
            kwargs["compression_config"] = ReActAgent.CompressionConfig(
                enable=True,
                agent_token_counter=CharTokenCounter(),
                trigger_threshold=50000,
                keep_recent=4,
                summary_schema=FitSummary,
                compression_prompt=(
                    "<system-hint>请用中文总结以上健身助手的对话历史，提取关键信息。"
                    "重点关注：用户的身体数据变化、训练进度、饮食状况和偏好。"
                    "忽略技术性调试信息。"
                    "同时，从对话中提取新发现的用户画像事实（user_facts_changed），包括："
                    "饮食偏好(food)、运动偏好(exercise)、健身目标(goal)、"
                    "已达成成就(achievement)、性格特质(personality)、伤病(health)。"
                    "每条事实需包含 category/key/value，置信度默认 1.0。</system-hint>"
                ),
                summary_template=(
                    "<system-info>对话摘要：\n"
                    "用户信息：{user_profile}\n"
                    "近期活动：{recent_activities}\n"
                    "待办建议：{pending_recommendations}\n"
                    "用户偏好：{user_preferences}\n"
                    "__USER_FACTS__{user_facts_json}__END_USER_FACTS__"
                    "</system-info>"
                ),
            )

        return ReActAgent(**kwargs)
    master = _create_pipeline_agent("Rogers-Master", sys_prompt=MASTER_SYS_PROMPT, enable_thinking=True)
    diet = _create_pipeline_agent("DietAnalyst", sys_prompt = DIET_SYS_PROMPT,model_name="deepseek-v4-flash")
    training = _create_pipeline_agent("TrainingAnalyst", sys_prompt = TRAINING_SYS_PROMPT,model_name="deepseek-v4-flash")

    for a in (master, diet, training):
        a.set_console_output_enabled(False)

    # 将 msgs 转为列表，避免迭代器被消耗后 master() 收到空输入
    raw_msgs = list(msgs)

    # 提前提取用户问题，用于后续保存
    user_question = _content_text(raw_msgs[-1]) if raw_msgs else ""
    logger.info("run_rogers_pipeline: user_id=%s session_id=%s, user_question[:50]=%s",
                user_id, session_id, user_question[:50] if user_question else "")

    # ---- 上下文注入（仅新会话）----
    if user_id and raw_msgs:
        mem = master.memory
        is_new_session = True
        if isinstance(mem, FitAsyncSQLAlchemyMemory):
            existing = await mem.get_memory()
            is_new_session = not existing
        if is_new_session:
            from src.agents.harness.context.user_context_builder import build_user_context
            ctx = build_user_context(user_id)
            if ctx:
                context_msg = Msg(
                    name="System",
                    content=f"【用户近况】{ctx}",
                    role="system",
                )
                raw_msgs.insert(0, context_msg)
                logger.info("Injected user context for new session: user_id=%s session_id=%s",
                            user_id, session_id)

    # ---- 审批系统上下文注入 ----
    approval_queue: asyncio.Queue = asyncio.Queue()
    set_session_context(
        session_id=sid,
        user_id=user_id,
        auto_approve=auto_approve_enabled,
        queue=approval_queue,
    )

    # ========================================================================
    # Phase 1: Master Agent 分析复杂度（流式）
    # ========================================================================
    master_text = ""

    counter = CharTokenCounter()
    n1 = await counter.count([m.to_dict() for m in raw_msgs])
    logger.info("Phase 1 input tokens: %d (session=%s)", n1, session_id)

    # 简单包装生成器，在每一步检查审批队列
    async def stream_with_approvals(agent, agent_name, msgs_for_agent):
        """包装 stream_printing_messages，在每一步检查审批队列"""
        # 两个队列：一个给主输出，一个给审批
        main_queue = asyncio.Queue()
        approval_queue_local = asyncio.Queue()

        # 标记
        main_done = False
        yielded_approval_ids = set()

        # 任务1：运行主生成器，把结果放到 main_queue
        async def run_main():
            nonlocal main_done
            try:
                main_gen = stream_printing_messages(
                    agents=[agent],
                    coroutine_task=agent(msgs_for_agent),
                )
                async for output in main_gen:
                    await main_queue.put(output)
            finally:
                main_done = True
                await main_queue.put(None)  # 哨兵

        # 任务2：把全局 approval_queue 的东西搬到 approval_queue_local
        async def poll_approvals():
            while not main_done:
                try:
                    while not approval_queue.empty():
                        item = approval_queue.get_nowait()
                        await approval_queue_local.put(item)
                except Exception:
                    pass
                if not main_done:
                    await asyncio.sleep(0.01)

        # 启动任务
        main_task = asyncio.create_task(run_main())
        poll_task = asyncio.create_task(poll_approvals())

        try:
            while True:
                # 优先检查审批队列
                try:
                    approval_msg = approval_queue_local.get_nowait()
                    approval_meta = getattr(approval_msg, "metadata", {}).get("tool_approval", {})
                    approval_id = approval_meta.get("approval_id")
                    if approval_id and approval_id not in yielded_approval_ids:
                        logger.info(f"Yielding approval message: {approval_msg}")
                        yielded_approval_ids.add(approval_id)
                        yield (approval_msg, False)
                    continue
                except asyncio.QueueEmpty:
                    pass

                # 等待主输出（带超时，让我们可以继续检查审批）
                try:
                    output = await asyncio.wait_for(main_queue.get(), timeout=0.02)
                except asyncio.TimeoutError:
                    continue

                if output is None:
                    break  # 主输出结束

                if len(output) >= 2:
                    msg, last = output[0], output[1]
                    msg.metadata = dict(getattr(msg, "metadata", {}) or {},
                                        source=agent_name)
                    yield (msg, last)
                    if last:
                        nonlocal master_text
                        if agent_name.startswith("[Master]"):
                            master_text = _content_text(msg)

            # 最后清理
            try:
                while not approval_queue_local.empty():
                    approval_msg = approval_queue_local.get_nowait()
                    approval_meta = getattr(approval_msg, "metadata", {}).get("tool_approval", {})
                    approval_id = approval_meta.get("approval_id")
                    if approval_id and approval_id not in yielded_approval_ids:
                        logger.info(f"Final yield approval message: {approval_msg}")
                        yield (approval_msg, False)
            except Exception:
                pass
        finally:
            for task in [main_task, poll_task]:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    try:
        async for output in stream_with_approvals(master, "[Master] Rogers", raw_msgs):
            yield output
    except Exception as e:
        logger.exception(f"Error in Phase 1: {e}")
        raise

    # ========================================================================
    # Phase 2: 判断是否需要 Fanout
    # ========================================================================
    need_fanout = "【需要专项分析】" in master_text
    logger.info("run_rogers_pipeline: need_fanout=%s", need_fanout)

    diet_output = ""
    training_output = ""

    if need_fanout:

        # ========================================================================
        # Phase 3: Fanout — SubAgent 顺序分析（各自流式输出）
        # ========================================================================

        # --- SubAgent 1: DietAnalyst ---
        diet_input = [
            Msg(name="User",
                content=f"用户问题：{user_question}\n\n请从饮食营养角度做专业分析，给出具体建议。",
                role="user")
        ]

        try:
            async for output in stream_with_approvals(diet, "[SubAgent] DietAnalyst", diet_input):
                msg, last = output
                yield msg, last
                if last:
                    diet_output = _content_text(msg)
        except Exception as e:
            logger.exception(f"Error in DietAnalyst phase: {e}")

        logger.info("DietAnalyst output length: %d chars", len(diet_output))

        # --- SubAgent 2: TrainingAnalyst ---
        training_input = [
            Msg(name="User",
                content=f"用户问题：{user_question}\n\n请从运动训练角度做专业分析，给出具体建议。",
                role="user")
        ]

        try:
            async for output in stream_with_approvals(training, "[SubAgent] TrainingAnalyst", training_input):
                msg, last = output
                yield msg, last
                if last:
                    training_output = _content_text(msg)
        except Exception as e:
            logger.exception(f"Error in TrainingAnalyst phase: {e}")

        logger.info("TrainingAnalyst output length: %d chars", len(training_output))

        # ========================================================================
        # Phase 4: Master Agent 汇总分析（流式）
        # ========================================================================
        if not diet_output.strip() and not training_output.strip():
            # SubAgent 未产生有效输出，跳过汇总
            logger.warning("Both SubAgents produced empty output, skipping aggregation")
        else:
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

            counter4 = CharTokenCounter()
            n4 = await counter4.count([agg_input.to_dict()])
            logger.info("Phase 4 input tokens: %d (session=%s)", n4, session_id)

            try:
                async for output in stream_with_approvals(master, "[Master] Rogers", [agg_input]):
                    yield output
            except Exception as e:
                logger.exception(f"Error in aggregation phase: {e}")

    # ---- 清理审批上下文 ----
    clear_session_context()

    # ========================================================================
    # Phase 5: 持久化存储到 fituser.db（所有 yield 完成后）
    # ========================================================================
    if user_id and session_id:
        logger.info("Phase 5: Saving pipeline exchange... user_id=%s, session_id=%s",
                    user_id, session_id)
        try:
            from src.agents.harness.memory import save_pipeline_exchange
            record_id = save_pipeline_exchange(
                user_id=user_id,
                session_id=session_id,
                user_message=user_question,
                master_phase1_output=master_text,
                need_fanout=need_fanout,
                diet_analyst_output=diet_output if need_fanout else "",
                training_analyst_output=training_output if need_fanout else "",
                master_phase4_output="",  # Phase 4 输出由前端从 SSE 获取；此处暂不冗余存储
            )
            logger.info("Phase 5: Saved pipeline exchange, record_id=%s", record_id)
        except Exception:
            logger.exception("Failed to save pipeline exchange to DB")
    else:
        logger.warning("Phase 5: Skip save, user_id=%s, session_id=%s",
                       user_id, session_id)

    # ── 调用成功后刷新 API Key TTL ──
    if user_id:
        api_key_cache.touch(user_id)
