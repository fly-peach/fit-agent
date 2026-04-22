from __future__ import annotations

import json
from uuid import uuid4

from app.agent.memory.auto_context_storage import AutoContextStorage
from app.agent.memory.auto_context_types import AutoContextConfig, CompressionResult
from app.agent.memory.compression_dispatcher import CompressionDispatcher
from app.agent.memory.token_counter import TokenCounter
from app.agent.schemas.agent import ChatMessage


class AutoContextMemory:
    def __init__(
        self,
        *,
        config: AutoContextConfig,
        storage: AutoContextStorage,
        dispatcher: CompressionDispatcher | None = None,
        token_counter: TokenCounter | None = None,
        context_window: int = 120000,
    ) -> None:
        self.config = config
        self.storage = storage
        self.dispatcher = dispatcher or CompressionDispatcher()
        self.token_counter = token_counter or TokenCounter()
        self.context_window = context_window

    def should_compress(self, messages: list[ChatMessage]) -> bool:
        if len(messages) >= self.config.msg_threshold:
            return True
        token_count = self.token_counter.count_messages(messages)
        if token_count >= self.config.token_threshold:
            return True
        return token_count / max(1, self.context_window) >= self.config.token_ratio

    def compress_messages(
        self,
        *,
        messages: list[ChatMessage],
        session_id: str,
        user_id: int,
        run_id: str,
    ) -> tuple[list[ChatMessage], list[CompressionResult]]:
        current = list(messages)
        results: list[CompressionResult] = []
        if not self.should_compress(current):
            return current, results

        for level in self.dispatcher.levels():
            strategy = self.dispatcher.get_strategy(level)
            result = strategy.compress(
                messages=current,
                config=self.config,
                storage=self.storage,
                token_counter=self.token_counter,
                context_window=self.context_window,
            )
            if not result.success:
                continue

            results.append(result)
            self.storage.events.create(
                session_id=session_id,
                user_id=user_id,
                run_id=run_id,
                strategy_level=result.strategy_level,
                strategy_name=result.strategy_name,
                messages_before=result.messages_before,
                messages_after=result.messages_after,
                tokens_before=result.tokens_before,
                tokens_after=result.tokens_after,
                compression_ratio=result.compression_ratio,
                affected_message_ids=json.dumps(result.affected_indices, ensure_ascii=False),
            )

            # 卸载策略记录大内容到 offload 存储
            if result.strategy_name == "offload_large_messages":
                for idx in result.affected_indices:
                    if idx >= len(current):
                        continue
                    source = current[idx]
                    self.storage.offloads.create(
                        offload_id=f"off_{uuid4().hex[:20]}",
                        session_id=session_id,
                        user_id=user_id,
                        message_id=None,
                        content_type="large_text",
                        content=source.content,
                        compressed_summary=source.content[:180] + ("..." if len(source.content) > 180 else ""),
                    )

            current = result.compressed_messages
            if not self.should_compress(current):
                break

        return current, results

    def status(self, *, session_id: str, user_id: int, current_messages: list[ChatMessage]) -> dict:
        latest = self.storage.events.latest_by_session(session_id=session_id, user_id=user_id)
        current_tokens = self.token_counter.count_messages(current_messages)
        return {
            "session_id": session_id,
            "current_tokens": current_tokens,
            "token_threshold": self.config.token_threshold,
            "msg_threshold": self.config.msg_threshold,
            "compression_needed": self.should_compress(current_messages),
            "last_event": None
            if not latest
            else {
                "strategy_level": latest.strategy_level,
                "strategy_name": latest.strategy_name,
                "messages_before": latest.messages_before,
                "messages_after": latest.messages_after,
                "tokens_before": latest.tokens_before,
                "tokens_after": latest.tokens_after,
                "compression_ratio": latest.compression_ratio,
                "created_at": latest.created_at.isoformat() if latest.created_at else None,
            },
        }

