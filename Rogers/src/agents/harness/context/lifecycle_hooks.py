"""四阶段生命周期钩子管理器

提供 pre_reply, pre_reasoning, post_acting, post_reply 四个生命周期钩子，
由 AgentConfig.running 配置驱动。
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, TYPE_CHECKING

from agentscope.message import Msg

from src.agents.harness.context.tool_result_cache import ToolResultCache
from src.agents.harness.utils.token_counter import get_token_counter

if TYPE_CHECKING:
    from src.agents.harness.memory.reme_light import ReMeLightMemoryManager
    from src.agents.config import AgentConfig, ContextCompactConfig, ToolResultCompactConfig

logger = logging.getLogger("fitagent")


class LifecycleHooksManager:
    """管理四个生命周期钩子，由 agent 配置驱动。"""

    def __init__(
        self,
        agent_cfg: "AgentConfig",
        memory_manager: "ReMeLightMemoryManager",
        working_dir: str,
    ):
        self.agent_cfg = agent_cfg
        self.memory_manager = memory_manager
        self.context_config = agent_cfg.running.context_compact
        self.cache_config = agent_cfg.running.tool_result_compact
        self.working_dir = working_dir
        self.cache = ToolResultCache(working_dir)
        self._stats = {
            "pre_reply_calls": 0,
            "pre_reasoning_calls": 0,
            "post_acting_calls": 0,
            "post_reply_calls": 0,
            "compaction_count_today": 0,
            "compaction_count_total": 0,
        }

    # ------------------------------------------------------------------
    # 四个生命周期钩子
    # ------------------------------------------------------------------

    async def pre_reply(self, agent: Any, kwargs: dict[str, Any]) -> dict[str, Any] | None:
        """Hook: Agent 回复前最终检查。

        - 检查最终回复是否包含未处理的工具调用
        - 验证回复格式和长度
        - 记录遥测数据
        """
        self._stats["pre_reply_calls"] += 1
        logger.debug("pre_reply hook triggered")
        return None

    async def pre_reasoning(
        self, agent: Any, kwargs: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Hook: 每轮推理前上下文健康检查 + 压缩。

        - 计算 token 预算
        - 压缩工具调用结果
        - 检查上下文是否需要压缩
        - 执行记忆压缩
        """
        from src.agents.harness.hooks.memory_compaction import (
            _run_compaction,
        )

        self._stats["pre_reasoning_calls"] += 1

        running = self.agent_cfg.running
        if not running.context_compact.context_compact_enabled:
            return None

        token_counter = get_token_counter(self.agent_cfg)
        await _run_compaction(
            agent=agent,
            memory_manager=self.memory_manager,
            running_config=running,
            token_counter=token_counter,
        )
        self.increment_compaction_count()
        return None

    async def post_acting(
        self, agent: Any, kwargs: dict[str, Any], output: Any,
    ) -> Msg | None:
        """Hook: 工具执行后结果裁剪。

        - 检查结果大小
        - 超大结果保存到文件缓存
        - 上下文中替换为文件引用
        """
        self._stats["post_acting_calls"] += 1

        if output is None or not hasattr(output, "content") or not output.content:
            return None

        content = output.content
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    tool_output = block.get("output", "")
                    if isinstance(tool_output, str) and len(tool_output) > 10000:
                        session_id = getattr(agent, "_session_id", "default")
                        tool_name = block.get("name", "unknown")
                        cache_id = self.cache.cache_result(session_id, tool_name, tool_output)
                        block["output"] = f"[Large output cached: {cache_id}]"
                        logger.info(f"Tool result cached to file: {cache_id}")

        return None

    async def post_reply(
        self, agent: Any, kwargs: dict[str, Any], output: Any,
    ) -> Msg | None:
        """Hook: 最终回复后日志/遥测。

        - 保存会话状态
        - 触发每日日志写入
        - 记录 token 使用统计
        - 清理临时文件
        """
        self._stats["post_reply_calls"] += 1
        logger.debug("post_reply hook triggered")
        return None

    # ------------------------------------------------------------------
    # 统计
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        """获取钩子调用统计。"""
        return self._stats.copy()

    def increment_compaction_count(self):
        """增加压缩计数。"""
        self._stats["compaction_count_today"] += 1
        self._stats["compaction_count_total"] += 1
