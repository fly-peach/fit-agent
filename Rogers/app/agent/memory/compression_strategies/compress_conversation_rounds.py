from __future__ import annotations

from app.agent.memory.auto_context_types import CompressionResult
from app.agent.memory.compression_strategies.base import CompressionStrategy
from app.agent.schemas.agent import ChatMessage


class CompressConversationRoundsStrategy(CompressionStrategy):
    level = 3
    name = "compress_conversation_rounds"

    def compress(self, *, messages, config, storage, token_counter, context_window) -> CompressionResult:
        before_tokens = token_counter.count_messages(messages)
        if len(messages) <= config.last_keep + config.min_consecutive_rounds:
            return CompressionResult(
                success=False,
                strategy_level=self.level,
                strategy_name=self.name,
                compressed_messages=messages,
                messages_before=len(messages),
                messages_after=len(messages),
                tokens_before=before_tokens,
                tokens_after=before_tokens,
                reason="rounds_below_threshold",
            )

        head = messages[: len(messages) - config.last_keep]
        tail = messages[len(messages) - config.last_keep :]
        merged = " ".join(m.content for m in head if m.content.strip())
        summary = merged[:260] + "..." if len(merged) > 260 else merged
        summary_msg = ChatMessage(role="assistant", content=f"[历史对话摘要] {summary}" if summary else "[历史对话摘要]（空）")
        compressed = [summary_msg, *tail]

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
            affected_indices=list(range(0, len(messages) - config.last_keep)),
        )

