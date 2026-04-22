from __future__ import annotations

import asyncio
from collections.abc import Generator
from typing import Protocol

from app.core.config import settings


class TextModelAdapter(Protocol):
    def invoke(self, prompt: str) -> str | None:
        ...

    def stream(self, prompt: str) -> Generator[str, None, None]:
        ...


class AgentScopeTextModelAdapter:
    def __init__(self) -> None:
        self._api_key = settings.dashscope_coding_api_key

    def invoke(self, prompt: str) -> str | None:
        if not self._api_key:
            return None
        try:
            from agentscope.formatter import DashScopeChatFormatter
            from agentscope.message import Msg
            from agentscope.model import DashScopeChatModel
        except Exception:
            return None

        async def _run() -> str | None:
            formatter = DashScopeChatFormatter()
            model = DashScopeChatModel(
                model_name=settings.model,
                api_key=self._api_key,
                stream=False,
                enable_thinking=False,
            )
            formatted = await formatter.format([Msg(name="user", content=prompt, role="user")])
            resp = await model(formatted)
            content = getattr(resp, "content", None)
            if isinstance(content, str):
                return content.strip()
            if content is None:
                return None
            return str(content).strip()

        try:
            return asyncio.run(_run())
        except RuntimeError:
            try:
                loop = asyncio.new_event_loop()
                try:
                    return loop.run_until_complete(_run())
                finally:
                    loop.close()
            except Exception:
                return None
        except Exception:
            return None

    def stream(self, prompt: str) -> Generator[str, None, None]:
        content = self.invoke(prompt)
        if content:
            yield content


def build_text_model_adapter() -> TextModelAdapter:
    return AgentScopeTextModelAdapter()