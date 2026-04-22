from __future__ import annotations

from app.agent.memory.auto_context_types import CompressionResult
from app.agent.memory.compression_strategies.base import CompressionStrategy
from app.agent.schemas.agent import ChatMessage


class CompressPlanMessagesStrategy(CompressionStrategy):
    level = 4
    name = "compress_plan_messages"

    def compress(self, *, messages, config, storage, token_counter, context_window) -> CompressionResult:
        before_tokens = token_counter.count_messages(messages)
        keep_start = max(0, len(messages) - config.last_keep)
        affected: list[int] = []
        compressed: list[ChatMessage] = []

        keywords = ("计划", "phase", "任务", "todo", "方案", "里程碑")
        for idx, item in enumerate(messages):
            if idx < keep_start and any(k in item.content.lower() for k in keywords):
                affected.append(idx)
                compressed.append(ChatMessage(role=item.role, content="[计划信息摘要] 已压缩保留"))
            else:
                compressed.append(item)

        if not affected:
            return CompressionResult(
                success=False,
                strategy_level=self.level,
                strategy_name=self.name,
                compressed_messages=messages,
                messages_before=len(messages),
                messages_after=len(messages),
                tokens_before=before_tokens,
                tokens_after=before_tokens,
                reason="no_plan_messages",
            )

        after_tokens = token_counter.count_messages(compressed)
        return CompressionResult(
            success=True,
            strategy_level=self.level,
            strategy_name=self.name,
            compressed_messages=compressed,
            messages_before=len(messages),
            messages_after=len(compressed),
            tokens_before=before_tokens,
            tokens_after=after_tokens,
            affected_indices=affected,
        )

