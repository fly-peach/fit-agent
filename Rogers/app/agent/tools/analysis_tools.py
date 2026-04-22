# -*- coding: utf-8 -*-
"""AI 教练分析工具。"""

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


async def summarize_text(text: str, max_len: int = 200) -> ToolResponse:
    """Summarize a long text into a shorter version.

    Args:
        text (`str`):
            Text to summarize.
        max_len (`int`, optional):
            Maximum length of the summary. Defaults to 200.

    Returns:
        `ToolResponse`:
            Summarized text.
    """
    t = (text or "").strip()
    if len(t) <= max_len:
        return ToolResponse(
            content=[
                TextBlock(type="text", text=t),
            ],
        )
    summary = t[:max_len].rstrip() + "..."
    return ToolResponse(
        content=[
            TextBlock(type="text", text=summary),
        ],
    )