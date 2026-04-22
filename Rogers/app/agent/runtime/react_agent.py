from __future__ import annotations

from collections.abc import Generator

from app.agent.runtime.model_factory import build_text_model_adapter


class RogersReActRuntime:
    """
    Phase-11 runtime entry.

    This class provides a stable runtime API for AgentService, so we can
    migrate implementation details to native AgentScope incrementally without
    changing upper-layer business logic.
    """

    def __init__(self) -> None:
        self._adapter = build_text_model_adapter()

    def invoke_general_reply(self, *, user_message: str, memory_context: str, system_prompt: str) -> str | None:
        prompt = self._build_prompt(user_message=user_message, memory_context=memory_context, system_prompt=system_prompt)
        return self._adapter.invoke(prompt)

    def stream_general_reply(
        self, *, user_message: str, memory_context: str, system_prompt: str
    ) -> Generator[str, None, None]:
        prompt = self._build_prompt(user_message=user_message, memory_context=memory_context, system_prompt=system_prompt)
        yield from self._adapter.stream(prompt)

    @staticmethod
    def _build_prompt(*, user_message: str, memory_context: str, system_prompt: str) -> str:
        prompt = system_prompt
        if memory_context:
            prompt += f"\n以下是用户可用记忆，请在回答时适度参考：\n{memory_context}"
        prompt += f"\n\n用户消息：{user_message}"
        return prompt
