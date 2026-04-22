from __future__ import annotations

from app.agent.memory.auto_context_types import CompressionResult
from app.agent.memory.compression_strategies.base import CompressionStrategy
from app.agent.schemas.agent import ChatMessage


class GlobalSummaryStrategy(CompressionStrategy):
    level = 5
    name = "global_summary"

    def compress(self, *, messages, config, storage, token_counter, context_window) -> CompressionResult:
        before_tokens = token_counter.count_messages(messages)
        if len(messages) <= config.last_keep + 1:
            return CompressionResult(
                success=False,
                strategy_level=self.level,
                strategy_name=self.name,
                compressed_messages=messages,
                messages_before=len(messages),
                messages_after=len(messages),
                tokens_before=before_tokens,
                tokens_after=before_tokens,
                reason="not_enough_messages",
            )

        tail = messages[-config.last_keep :] if config.last_keep > 0 else []
        head = messages[: len(messages) - len(tail)]
        merged = " ".join(m.content for m in head if m.content.strip())
        summary = merged[:360] + "..." if len(merged) > 360 else merged
        compressed = [ChatMessage(role="assistant", content=f"[全局摘要] {summary if summary else '无'}"), *tail]
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
            affected_indices=list(range(0, len(head))),
        )

