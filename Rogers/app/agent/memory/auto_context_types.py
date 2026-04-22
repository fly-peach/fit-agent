from __future__ import annotations

from dataclasses import dataclass, field

from app.agent.schemas.agent import ChatMessage


@dataclass
class AutoContextConfig:
    msg_threshold: int = 30
    token_threshold: int = 100000
    token_ratio: float = 0.3
    last_keep: int = 10
    min_consecutive_tool_messages: int = 6
    min_consecutive_rounds: int = 5
    large_payload_threshold: int = 5000


@dataclass
class CompressionResult:
    success: bool
    strategy_level: int
    strategy_name: str
    compressed_messages: list[ChatMessage]
    messages_before: int
    messages_after: int
    tokens_before: int
    tokens_after: int
    affected_indices: list[int] = field(default_factory=list)
    reason: str = ""

    @property
    def compression_ratio(self) -> float:
        if self.tokens_before <= 0:
            return 1.0
        return float(self.tokens_after) / float(self.tokens_before)

