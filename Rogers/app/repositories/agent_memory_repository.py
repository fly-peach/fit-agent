from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.agent_memory import AgentMemory


class AgentMemoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: int,
        memory_type: str,
        content: str,
        tags: list[str] | None = None,
        source: str = "chat",
        source_ref: str | None = None,
        importance: int = 3,
    ) -> AgentMemory:
        obj = AgentMemory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            tags=tags or [],
            source=source,
            source_ref=source_ref,
            importance=max(1, min(5, importance)),
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def find_exact(self, *, user_id: int, content: str) -> AgentMemory | None:
        stmt = select(AgentMemory).where(AgentMemory.user_id == user_id, AgentMemory.content == content).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def search(self, *, user_id: int, query: str, limit: int = 5) -> list[AgentMemory]:
        q = (query or "").strip()
        if not q:
            stmt = (
                select(AgentMemory)
                .where(AgentMemory.user_id == user_id)
                .order_by(desc(AgentMemory.importance), desc(AgentMemory.updated_at))
                .limit(limit)
            )
            return list(self.db.execute(stmt).scalars().all())

        stmt = (
            select(AgentMemory)
            .where(AgentMemory.user_id == user_id, AgentMemory.content.ilike(f"%{q}%"))
            .order_by(desc(AgentMemory.importance), desc(AgentMemory.updated_at))
            .limit(limit)
        )
        rows = list(self.db.execute(stmt).scalars().all())
        if rows:
            return rows
        return self.search(user_id=user_id, query="", limit=limit)
