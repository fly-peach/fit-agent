from __future__ import annotations

from app.agent.memory.auto_context_types import CompressionResult
from app.agent.memory.compression_strategies.base import CompressionStrategy
from app.agent.schemas.agent import ChatMessage


class CompressToolCallsStrategy(CompressionStrategy):
    level = 1
    name = "compress_tool_calls"

    def compress(self, *, messages, config, storage, token_counter, context_window) -> CompressionResult:
        before_tokens = token_counter.count_messages(messages)
        if len(messages) <= config.last_keep:
            return CompressionResult(
                success=False,
                strategy_level=self.level,
                strategy_name=self.name,
                compressed_messages=messages,
                messages_before=len(messages),
                messages_after=len(messages),
                tokens_before=before_tokens,
                tokens_after=before_tokens,
                reason="messages_below_threshold",
            )

        keep_start = max(0, len(messages) - config.last_keep)
        affected: list[int] = []
        compressed: list[ChatMessage] = []
        for idx, item in enumerate(messages):
            if idx < keep_start and item.role == "assistant" and any(
                k in item.content.lower() for k in ["tool", "工具", "调用", "input", "output"]
            ):
                affected.append(idx)
                compressed.append(
                    ChatMessage(
                        role="assistant",
                        content=f"[工具调用摘要] {item.content[:120]}..." if len(item.content) > 120 else item.content,
                    )
                )
            else:
                compressed.append(item)

        if len(affected) < config.min_consecutive_tool_messages:
            return CompressionResult(
                success=False,
                strategy_level=self.level,
                strategy_name=self.name,
                compressed_messages=messages,
                messages_before=len(messages),
                messages_after=len(messages),
                tokens_before=before_tokens,
                tokens_after=before_tokens,
                reason="tool_messages_below_threshold",
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

