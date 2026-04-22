from __future__ import annotations

from uuid import uuid4

from app.agent.memory.auto_context_types import CompressionResult
from app.agent.memory.compression_strategies.base import CompressionStrategy
from app.agent.schemas.agent import ChatMessage


class OffloadLargeMessagesStrategy(CompressionStrategy):
    level = 2
    name = "offload_large_messages"

    def compress(self, *, messages, config, storage, token_counter, context_window) -> CompressionResult:
        before_tokens = token_counter.count_messages(messages)
        keep_start = max(0, len(messages) - config.last_keep)
        affected: list[int] = []
        compressed: list[ChatMessage] = []

        for idx, item in enumerate(messages):
            if idx < keep_start and len(item.content) > config.large_payload_threshold:
                affected.append(idx)
                offload_id = f"off_{uuid4().hex[:20]}"
                compressed_summary = item.content[:180] + "..."
                compressed.append(
                    ChatMessage(
                        role=item.role,
                        content=f"[内容已卸载:{offload_id}] {compressed_summary}",
                    )
                )
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
                reason="no_large_messages",
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

