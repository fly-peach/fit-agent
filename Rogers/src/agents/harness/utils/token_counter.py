"""Token 计数器 — 支持 HuggingFace 精确计数和字节估算回退。

根据 AgentScope 官方文档，DashScope 模型建议使用 HuggingFace token 计数器。
通过 ``ContextCompactConfig.token_counter_model`` 配置模型名即可启用。
当 HuggingFace Hub 不可达或未配置时，自动使用字节长度估算。
"""
from __future__ import annotations

import json
import logging
from typing import Any

from agentscope.token import TokenCounterBase

try:
    from agentscope.token import HuggingFaceTokenCounter as _HF

    _HAS_HF = True
except ImportError:
    _HAS_HF = False

logger = logging.getLogger(__name__)


class EstimateTokenCounter(TokenCounterBase):
    """基于字节长度的轻量级 token 估算（默认方案，无需网络）。"""

    def __init__(self, divisor: float = 3.75):
        self.divisor = divisor

    async def count(
        self,
        messages: list[dict] | None = None,
        tools: list[dict] | None = None,
        text: str | None = None,
        **_kwargs: Any,
    ) -> int:
        if text:
            return self.estimate_tokens(text)

        parts: list[str] = []
        for msg in messages or []:
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


class CompatTokenCounter(TokenCounterBase):
    """统一封装的 Token 计数器。

    优先使用 HuggingFace 精确计数（需配置 ``token_counter_model``），
    当 HF Hub 不可达或未配置时，自动回退到估算模式。
    """

    def __init__(
        self,
        pretrained_model_name_or_path: str = "",
        use_mirror: bool = True,
        **kwargs: Any,
    ):
        self._inner: TokenCounterBase
        self._label: str

        if _HAS_HF and pretrained_model_name_or_path:
            try:
                self._inner = _HF(
                    pretrained_model_name_or_path=pretrained_model_name_or_path,
                    use_mirror=use_mirror,
                    **kwargs,
                )
                self._label = (
                    f"huggingface({pretrained_model_name_or_path})"
                )
                logger.info(
                    "Token counter: %s",
                    self._label,
                )
                return
            except Exception as e:
                logger.warning(
                    "HuggingFaceTokenCounter init failed: %s. "
                    "Falling back to estimate mode.",
                    e,
                )

        divisor = kwargs.get("divisor", 3.75)
        self._inner = EstimateTokenCounter(divisor=divisor)
        self._label = "estimate(bytes/3.75)"

    async def count(
        self,
        messages: list[dict] | None = None,
        tools: list[dict] | None = None,
        text: str | None = None,
        **_kwargs: Any,
    ) -> int:
        return await self._inner.count(
            messages=messages,
            tools=tools,
            text=text,
        )


def get_token_counter(agent_config: Any) -> TokenCounterBase:
    """根据配置创建最合适的 token 计数器。

    策略：
    1. 配置了 ``token_counter_model`` → HuggingFace 精确计数
    2. 否则 → 字节长度估算（默认 divisor=3.75）
    """
    cc = agent_config.running.context_compact
    model_name = getattr(cc, "token_counter_model", "") or ""
    divisor = getattr(cc, "token_count_estimate_divisor", 3.75)

    return CompatTokenCounter(
        pretrained_model_name_or_path=model_name,
        divisor=divisor,
    )


