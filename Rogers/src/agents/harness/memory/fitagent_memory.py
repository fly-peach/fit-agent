"""FitAgent SQL Memory — 继承 AsyncSQLAlchemyMemory，补齐压缩摘要相关方法。

AsyncSQLAlchemyMemory 来自 AgentScope，拥有完整的 DB 持久化能力。
本适配器通过继承 + 组合补全缺失方法。
"""
from __future__ import annotations

import logging
from typing import Any

from agentscope.message import Msg
from agentscope.memory._working_memory._sqlalchemy_memory import AsyncSQLAlchemyMemory
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

logger = logging.getLogger(__name__)


class FitAgentSQLMemory(AsyncSQLAlchemyMemory):
    """适配 AsyncSQLAlchemyMemory，补齐压缩摘要和标记方法。

    相比 AsyncSQLAlchemyMemory 额外提供：
    - ``_compressed_summary`` 属性
    - ``get_compressed_summary()`` — 返回当前压缩摘要
    - ``mark_messages_compressed()`` — 标记旧消息为已压缩
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # AsyncSQLAlchemyMemory 内部已有 _compressed_summary 属性，
        # 但 get_compressed_summary() 作为独立方法不存在。
        # 我们显式确保它已初始化。
        if not hasattr(self, "_compressed_summary"):
            object.__setattr__(self, "_compressed_summary", "")

    # ------------------------------------------------------------------
    # 补齐：get_compressed_summary
    # ------------------------------------------------------------------

    def get_compressed_summary(self) -> str:
        """获取当前压缩摘要。"""
        summary = getattr(self, "_compressed_summary", None)
        return summary if summary is not None else ""

    # ------------------------------------------------------------------
    # 补齐：mark_messages_compressed
    # ------------------------------------------------------------------

    async def mark_messages_compressed(
        self,
        messages: list[Msg],
        **kwargs: Any,
    ) -> None:
        """将消息标记为已压缩（通过 update_messages_mark 实现）。

        update_messages_mark 内部会调用 _make_message_id 将简单 ID
        转换为复合 ID，因此直接传入 Msg.id 即可。
        """
        if not messages:
            return

        msg_ids = [msg.id for msg in messages if msg.id]
        if not msg_ids:
            return

        await self.update_messages_mark(new_mark="_compressed", msg_ids=msg_ids)
        logger.info("Marked %d messages as compressed", len(msg_ids))
