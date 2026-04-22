from __future__ import annotations

from app.repositories.agent_compression_event_repository import AgentCompressionEventRepository
from app.repositories.agent_offload_repository import AgentOffloadRepository
from app.repositories.agent_repository import AgentRepository


class AutoContextStorage:
    """
    统一封装 AutoContextMemory 的四层存储中与数据库相关的三层：
    - original messages（agent_messages）
    - offloads（agent_offloads）
    - compression events（agent_compression_events）
    """

    def __init__(
        self,
        *,
        message_repo: AgentRepository,
        offload_repo: AgentOffloadRepository,
        compression_repo: AgentCompressionEventRepository,
    ) -> None:
        self.messages = message_repo
        self.offloads = offload_repo
        self.events = compression_repo

