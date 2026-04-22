from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.agent_compression_event import AgentCompressionEvent


class AgentCompressionEventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        session_id: str,
        user_id: int,
        run_id: str,
        strategy_level: int,
        strategy_name: str,
        messages_before: int,
        messages_after: int,
        tokens_before: int,
        tokens_after: int,
        compression_ratio: float,
        affected_message_ids: str | None = None,
    ) -> AgentCompressionEvent:
        obj = AgentCompressionEvent(
            session_id=session_id,
            user_id=user_id,
            run_id=run_id,
            strategy_level=strategy_level,
            strategy_name=strategy_name,
            messages_before=messages_before,
            messages_after=messages_after,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            compression_ratio=compression_ratio,
            affected_message_ids=affected_message_ids,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_by_session(self, *, session_id: str, user_id: int, limit: int = 100) -> list[AgentCompressionEvent]:
        stmt = (
            select(AgentCompressionEvent)
            .where(AgentCompressionEvent.session_id == session_id, AgentCompressionEvent.user_id == user_id)
            .order_by(desc(AgentCompressionEvent.created_at))
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def latest_by_session(self, *, session_id: str, user_id: int) -> AgentCompressionEvent | None:
        stmt = (
            select(AgentCompressionEvent)
            .where(AgentCompressionEvent.session_id == session_id, AgentCompressionEvent.user_id == user_id)
            .order_by(desc(AgentCompressionEvent.created_at))
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

