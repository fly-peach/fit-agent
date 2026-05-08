"""CRUD operations for chat sessions.

Moved from fitme/crud/chat.py to agents/harness/chats/crud.py.
"""
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from .models import ChatSession

logger = logging.getLogger("fitagent")


# ==================== Session CRUD ====================


def get_sessions(db: Session, user_id: int) -> list[ChatSession]:
    """获取用户的所有会话，按更新时间倒序。"""
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


def get_session(db: Session, user_id: int, session_id: str) -> ChatSession | None:
    """获取指定会话（含消息）。"""
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        .first()
    )


def create_session(
    db: Session, user_id: int, session_id: str, name: str = "新对话"
) -> ChatSession:
    """创建新会话。"""
    session = ChatSession(
        id=session_id,
        user_id=user_id,
        name=name,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    logger.info(f"Created chat session: {session_id} for user {user_id}")
    return session


def update_session(
    db: Session, user_id: int, session_id: str, 
    name: str | None = None, pinned: bool | None = None,
) -> ChatSession | None:
    """更新会话名称或置顶状态。"""
    session = get_session(db, user_id, session_id)
    if session is None:
        return None
    if name is not None:
        session.name = name
    if pinned is not None:
        session.pinned = 1 if pinned else 0
    session.updated_at = datetime.now()
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, user_id: int, session_id: str) -> bool:
    """删除会话（级联删除所有消息）。"""
    session = get_session(db, user_id, session_id)
    if session is None:
        return False
    db.delete(session)
    db.commit()
    logger.info(f"Deleted chat session: {session_id} for user {user_id}")
    return True

