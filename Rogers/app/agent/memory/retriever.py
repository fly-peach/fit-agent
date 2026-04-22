from __future__ import annotations

from app.repositories.agent_memory_repository import AgentMemoryRepository


class MemoryRetriever:
    def __init__(self, repo: AgentMemoryRepository) -> None:
        self.repo = repo

    def search(self, *, user_id: int, query: str, top_k: int = 5) -> list[str]:
        rows = self.repo.search(user_id=user_id, query=query, limit=top_k)
        return [r.content for r in rows]

    def build_context(self, *, user_id: int, query: str, top_k: int = 5) -> str:
        items = self.search(user_id=user_id, query=query, top_k=top_k)
        if not items:
            return ""
        return "\n".join([f"- {x}" for x in items])
