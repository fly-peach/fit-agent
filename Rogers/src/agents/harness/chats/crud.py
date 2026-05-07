"""CRUD operations for chat sessions and messages.

Moved from fitme/crud/chat.py to agents/harness/chats/crud.py.
"""
import json
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from .models import ChatSession, ChatMessage

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


def update_session_name(
    db: Session, user_id: int, session_id: str, name: str
) -> ChatSession | None:
    """更新会话名称。"""
    session = get_session(db, user_id, session_id)
    if session is None:
        return None
    session.name = name
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


# ==================== Message CRUD ====================


def add_message(
    db: Session,
    session_id: str,
    role: str,
    content_json: str,
    msg_status: str = "finished",
) -> ChatMessage:
    """添加消息到会话。"""
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content_json,
        msg_status=msg_status,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages(db: Session, session_id: str) -> list[ChatMessage]:
    """获取会话的所有消息，按创建时间升序。"""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
