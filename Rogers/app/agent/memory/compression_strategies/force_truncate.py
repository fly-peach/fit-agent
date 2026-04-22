from __future__ import annotations

from app.agent.memory.auto_context_types import CompressionResult
from app.agent.memory.compression_strategies.base import CompressionStrategy


class ForceTruncateStrategy(CompressionStrategy):
    level = 6
    name = "force_truncate"

    def compress(self, *, messages, config, storage, token_counter, context_window) -> CompressionResult:
        before_tokens = token_counter.count_messages(messages)
        if not messages:
            return CompressionResult(
                success=False,
                strategy_level=self.level,
                strategy_name=self.name,
                compressed_messages=messages,
                messages_before=0,
                messages_after=0,
                tokens_before=0,
                tokens_after=0,
                reason="empty",
            )
        keep = max(1, config.last_keep)
        compressed = messages[-keep:]
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
            affected_indices=list(range(0, max(0, len(messages) - len(compressed)))),
        )

