"""聊天会话 SQLAlchemy 模型。

模型定义在 agents 模块中，但继承 fitme 的 UserDBBase，
确保 main.py 中的 create_all 能自动建表。

注意：消息存储已迁移到 FitAgentSQLMemory（agent_memory.db），
ChatMessage 模型已废弃不再使用。
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.fitme.models.user_db import Base


class ChatSession(Base):
    """聊天会话表 - User DB

    存储用户的对话会话元信息（名称、置顶状态等）。
    消息内容存储在 agent_memory.db（FitAgentSQLMemory 自动管理）。
    """
    __tablename__ = "chat_sessions"

    id = Column(String(50), primary_key=True)  # session_id
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String(100), default="新对话")
    pinned = Column(Integer, default=0)  # 0=未置顶, 1=置顶
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User")
