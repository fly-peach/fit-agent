from __future__ import annotations

from app.agent.memory.retriever import MemoryRetriever
from app.repositories.agent_memory_repository import AgentMemoryRepository


class MemoryManager:
    def __init__(self, repo: AgentMemoryRepository) -> None:
        self.repo = repo
        self.retriever = MemoryRetriever(repo)

    def maybe_store_user_memory(self, *, user_id: int, message: str) -> bool:
        text = (message or "").strip()
        if not text:
            return False
        triggers = ["记住", "记下来", "以后按这个", "偏好是", "我的目标是"]
        if not any(t in text for t in triggers):
            return False

        content = (
            text.replace("请", "")
            .replace("帮我", "")
            .replace("记住", "")
            .replace("记下来", "")
            .strip("：: ")
        )
        if not content:
            return False
        existing = self.repo.find_exact(user_id=user_id, content=content)
        if existing:
            return False
        self.repo.create(user_id=user_id, memory_type="preference", content=content, tags=["user-explicit"], importance=5)
        return True

    def search(self, *, user_id: int, query: str, top_k: int = 5) -> list[str]:
        return self.retriever.search(user_id=user_id, query=query, top_k=top_k)

    def build_context(self, *, user_id: int, query: str, top_k: int = 5) -> str:
        return self.retriever.build_context(user_id=user_id, query=query, top_k=top_k)
