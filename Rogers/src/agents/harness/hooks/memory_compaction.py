"""记忆压缩逻辑 — 可被 LifecycleHooksManager 或直接调用。"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agentscope.agent import ReActAgent

from src.agents.harness.utils.token_counter import get_token_counter

if TYPE_CHECKING:
    from src.agents.harness.memory.reme_light import ReMeLightMemoryManager
    from src.agents.harness.utils.token_counter import EstimateTokenCounter
    from src.agents.config import RunningConfig

logger = logging.getLogger(__name__)


async def _run_compaction(
    agent: ReActAgent,
    memory_manager: "ReMeLightMemoryManager",
    running_config: "RunningConfig",
    token_counter: "EstimateTokenCounter",
) -> None:
    """执行完整的上下文压缩流程。

    - 计算 token 预算
    - 压缩工具调用结果
    - 检查上下文是否需要压缩
    - 执行记忆压缩并更新摘要
    """
    cc = running_config.context_compact
    if not cc.context_compact_enabled:
        return

    memory = agent.memory
    system_prompt = agent.sys_prompt
    compressed_summary = memory.get_compressed_summary()

    # 计算 token 预算
    str_token_count = await token_counter.count(
        messages=[],
        text=(system_prompt or "") + (compressed_summary or ""),
    )
    left = running_config.memory_compact_threshold - str_token_count

    if left <= 0:
        logger.warning(
            "memory_compact_threshold is too low; "
            "system_prompt + compressed_summary already exceeds it",
        )
        return

    messages = await memory.get_memory(prepend_summary=False)

    # 压缩工具调用结果
    trc = running_config.tool_result_compact
    if trc.enabled:
        await memory_manager.compact_tool_result(
            messages=messages,
            recent_n=trc.recent_n,
            old_max_bytes=trc.old_max_bytes,
            recent_max_bytes=trc.recent_max_bytes,
            retention_days=trc.retention_days,
        )

    # 检查上下文是否需要压缩
    result = await memory_manager.check_context(
        messages=messages,
        memory_compact_threshold=left,
        memory_compact_reserve=running_config.memory_compact_reserve,
        as_token_counter=token_counter,
    )
    if result is None:
        return

    messages_to_compact, _, is_valid = result

    if not messages_to_compact:
        return

    # 如果消息无效，压缩除最后几条外的所有内容
    if not is_valid:
        keep = 3
        ml = len(messages)
        messages_to_compact = messages[: max(ml - keep, 0)]

    if not messages_to_compact:
        return

    # 异步摘要
    if running_config.memory_summary.memory_summary_enabled:
        summary_fn = getattr(memory_manager, "add_async_summary_task", None)
        if summary_fn is not None:
            try:
                summary_fn(messages=messages_to_compact)
            except Exception:
                pass

    # 压缩上下文
    if cc.context_compact_enabled:
        compact_content = await memory_manager.compact_memory(
            messages=messages_to_compact,
            previous_summary=memory.get_compressed_summary(),
        )
        if compact_content:
            await memory.update_compressed_summary(compact_content)
            logger.info("Context compaction completed")
        else:
            logger.warning("Context compaction returned empty result")

    await memory.mark_messages_compressed(messages_to_compact)


# ---------------------------------------------------------------------------
# 向后兼容：create_memory_compaction_hook 仍可在旧代码中使用
# ---------------------------------------------------------------------------


def create_memory_compaction_hook(
    memory_manager: "ReMeLightMemoryManager",
):
    """创建推理前记忆压缩钩子（向后兼容）。"""
    _reentrancy = False

    async def memory_compaction_hook(
        agent: ReActAgent,
        kwargs: dict[str, Any],
    ) -> dict[str, Any] | None:
        nonlocal _reentrancy
        if _reentrancy:
            return None
        _reentrancy = True

        try:
            from src.agents.config import load_agent_config
            agent_config = load_agent_config(memory_manager.agent_id)
            token_counter = get_token_counter(agent_config)
            await _run_compaction(
                agent=agent,
                memory_manager=memory_manager,
                running_config=agent_config.running,
                token_counter=token_counter,
            )
        except Exception as e:
            logger.exception(f"Memory compaction hook failed: {e}")
        finally:
            _reentrancy = False

        return None

    return memory_compaction_hook
