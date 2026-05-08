"""聊天会话与消息的 SQLAlchemy 模型。

模型定义在 agents 模块中，但继承 fitme 的 UserDBBase，
确保 main.py 中的 create_all 能自动建表。
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.fitme.models.user_db import Base


class ChatSession(Base):
    """聊天会话表 - User DB

    存储用户的对话会话元信息，消息详细内容存放在 chat_messages 表中。
    """
    __tablename__ = "chat_sessions"

    id = Column(String(50), primary_key=True)  # session_id
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String(100), default="新对话")
    pinned = Column(Integer, default=0)  # 0=未置顶, 1=置顶
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    user = relationship("User")


class ChatMessage(Base):
    """聊天消息表 - User DB

    存储对话中的每条消息，content 为 IAgentScopeRuntimeWebUIMessage 格式的 JSON。
    """
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("idx_chat_session_time", "session_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" / "assistant"
    content = Column(Text, nullable=False)  # JSON: IAgentScopeRuntimeWebUIMessage 格式
    msg_status = Column(String(20), default="finished")
    created_at = Column(DateTime, server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")
