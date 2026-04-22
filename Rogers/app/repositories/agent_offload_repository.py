from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.agent_offload import AgentOffload


class AgentOffloadRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        offload_id: str,
        session_id: str,
        user_id: int,
        message_id: int | None,
        content_type: str,
        content: str,
        compressed_summary: str | None = None,
    ) -> AgentOffload:
        obj = AgentOffload(
            id=offload_id,
            session_id=session_id,
            user_id=user_id,
            message_id=message_id,
            content_type=content_type,
            content=content,
            compressed_summary=compressed_summary,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, *, offload_id: str, user_id: int) -> AgentOffload | None:
        stmt = select(AgentOffload).where(AgentOffload.id == offload_id, AgentOffload.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def mark_loaded(self, obj: AgentOffload) -> AgentOffload:
        obj.loaded_at = datetime.now(timezone.utc)
        obj.load_count = int(obj.load_count or 0) + 1
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_by_session(self, *, session_id: str, user_id: int, limit: int = 100) -> list[AgentOffload]:
        stmt = (
            select(AgentOffload)
            .where(AgentOffload.session_id == session_id, AgentOffload.user_id == user_id)
            .order_by(desc(AgentOffload.created_at))
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
