from datetime import datetime, timezone

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from app.models.agent_event import AgentEvent
from app.models.agent_message import AgentMessage
from app.models.agent_session import AgentSession
from app.models.pending_action import PendingAction


class AgentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_session(self, *, session_id: str, user_id: int) -> AgentSession | None:
        stmt = select(AgentSession).where(AgentSession.id == session_id, AgentSession.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_session(self, *, session_id: str, user_id: int, title: str = "AI 教练会话") -> AgentSession:
        obj = AgentSession(id=session_id, user_id=user_id, title=title)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def touch_session(self, *, session: AgentSession) -> None:
        session.updated_at = datetime.now(timezone.utc)
        self.db.add(session)
        self.db.commit()

    def list_sessions(self, *, user_id: int, limit: int = 50) -> list[AgentSession]:
        stmt = (
            select(AgentSession)
            .where(AgentSession.user_id == user_id)
            .order_by(desc(AgentSession.updated_at))
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_message(
        self,
        *,
        session_id: str,
        user_id: int,
        role: str,
        content: str,
        reasoning: str | None = None,
        tool_uses: list[dict] | None = None,
        is_compressed: bool = False,
        compression_strategy: str | None = None,
        offload_id: str | None = None,
        compressed_summary: str | None = None,
    ) -> AgentMessage:
        obj = AgentMessage(
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            reasoning=reasoning,
            tool_uses=tool_uses,
            is_compressed=is_compressed,
            compression_strategy=compression_strategy,
            offload_id=offload_id,
            compressed_summary=compressed_summary,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def create_event(
        self,
        *,
        event_id: str,
        session_id: str,
        user_id: int,
        run_id: str,
        event_type: str,
        sequence_number: int,
        payload: dict,
    ) -> AgentEvent:
        obj = AgentEvent(
            id=event_id,
            session_id=session_id,
            user_id=user_id,
            run_id=run_id,
            event_type=event_type,
            sequence_number=sequence_number,
            payload=payload,
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def list_events(self, *, session_id: str, user_id: int, limit: int = 500) -> list[AgentEvent]:
        stmt = (
            select(AgentEvent)
            .where(AgentEvent.session_id == session_id, AgentEvent.user_id == user_id)
            .order_by(AgentEvent.sequence_number.asc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_messages(self, *, session_id: str, user_id: int, limit: int = 100) -> list[AgentMessage]:
        stmt = (
            select(AgentMessage)
            .where(AgentMessage.session_id == session_id, AgentMessage.user_id == user_id)
            .order_by(AgentMessage.id.asc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_pending_action(
        self, *, action_id: str, session_id: str, user_id: int, tool_name: str, summary: str, payload: dict
    ) -> PendingAction:
        obj = PendingAction(
            id=action_id,
            session_id=session_id,
            user_id=user_id,
            tool_name=tool_name,
            summary=summary,
            payload=payload,
            status="pending",
        )
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_pending_action(self, *, action_id: str, user_id: int) -> PendingAction | None:
        stmt = select(PendingAction).where(PendingAction.id == action_id, PendingAction.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_pending_actions(self, *, user_id: int, limit: int = 50) -> list[PendingAction]:
        stmt = (
            select(PendingAction)
            .where(PendingAction.user_id == user_id, PendingAction.status == "pending")
            .order_by(desc(PendingAction.created_at))
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def save_pending_action(self, obj: PendingAction) -> PendingAction:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete_session(self, *, session_id: str, user_id: int) -> bool:
        session = self.get_session(session_id=session_id, user_id=user_id)
        if session is None:
            return False
        self.db.execute(
            delete(PendingAction).where(PendingAction.session_id == session_id, PendingAction.user_id == user_id)
        )
        self.db.execute(delete(AgentEvent).where(AgentEvent.session_id == session_id, AgentEvent.user_id == user_id))
        self.db.execute(
            delete(AgentMessage).where(AgentMessage.session_id == session_id, AgentMessage.user_id == user_id)
        )
        self.db.delete(session)
        self.db.commit()
        return True
