"""基于字符估算的轻量级 token 计数器。

完全跳过加载分词器 — 适用于压缩阈值检查等不需要高精度的场景。
"""
import json

from agentscope.token import TokenCounterBase


class EstimateTokenCounter(TokenCounterBase):
    """Token counter using byte-length / divisor estimation."""

    def __init__(self, divisor: float = 3.75):
        self.divisor = divisor

    async def count(
        self,
        messages: list[dict] | None = None,
        tools: list[dict] | None = None,
        text: str | None = None,
        **_kwargs,
    ) -> int:
        if text:
            return self.estimate_tokens(text)

        parts: list[str] = []
        for msg in (messages or []):
            content = msg.get("content", "")
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        parts.append(block.get("text", ""))
                    else:
                        parts.append(str(block))
            else:
                parts.append(str(content))

        if tools:
            parts.append(json.dumps(tools, ensure_ascii=False))

        return self.estimate_tokens(" ".join(parts))

    def estimate_tokens(self, text: str) -> int:
        return int(len(text.encode("utf-8")) / self.divisor + 0.5)


def get_token_counter(agent_config) -> EstimateTokenCounter:
    """Return an EstimateTokenCounter for the given agent config."""
    return EstimateTokenCounter(
        divisor=agent_config.running.context_compact.token_count_estimate_divisor,
    )
