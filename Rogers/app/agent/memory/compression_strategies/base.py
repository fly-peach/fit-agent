from __future__ import annotations

from abc import ABC, abstractmethod

from app.agent.memory.auto_context_storage import AutoContextStorage
from app.agent.memory.auto_context_types import AutoContextConfig, CompressionResult
from app.agent.schemas.agent import ChatMessage


class CompressionStrategy(ABC):
    level: int = 0
    name: str = "base"

    @abstractmethod
    def compress(
        self,
        *,
        messages: list[ChatMessage],
        config: AutoContextConfig,
        storage: AutoContextStorage,
        token_counter,
        context_window: int,
    ) -> CompressionResult:
        ...

