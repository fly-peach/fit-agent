from __future__ import annotations

from app.agent.memory.compression_strategies import (
    CompressConversationRoundsStrategy,
    CompressPlanMessagesStrategy,
    CompressToolCallsStrategy,
    ForceTruncateStrategy,
    GlobalSummaryStrategy,
    OffloadLargeMessagesStrategy,
)


class CompressionDispatcher:
    def __init__(self) -> None:
        self._strategies = {
            1: CompressToolCallsStrategy(),
            2: OffloadLargeMessagesStrategy(),
            3: CompressConversationRoundsStrategy(),
            4: CompressPlanMessagesStrategy(),
            5: GlobalSummaryStrategy(),
            6: ForceTruncateStrategy(),
        }

    def get_strategy(self, level: int):
        return self._strategies[level]

    def levels(self) -> list[int]:
        return sorted(self._strategies.keys())

