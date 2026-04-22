from __future__ import annotations

from app.agent.schemas.agent import ChatMessage


class TokenCounter:
    """
    轻量 token 估算器：
    - 中英文混合场景下用字符长度/4 近似 token。
    - 为防止极短文本被估算为 0，至少记为 1。
    """

    @staticmethod
    def count_text(text: str) -> int:
        raw = len(text or "")
        return max(1, raw // 4)

    @classmethod
    def count_messages(cls, messages: list[ChatMessage]) -> int:
        return sum(cls.count_text(m.content) for m in messages)

