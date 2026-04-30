"""AgentContext — 为每个请求隔离 agent 工具的数据访问。

agent 工具函数通过 contextvars 获取当前用户和 DB session，
这个模块负责在每次请求前后正确设置和清理它们。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from src.fitme.services.auth_service import AuthService
from src.fitme.utils.database import SessionLocal
from src.agents.harness.tools.basic.read_data import (
    _current_user_id,
    _current_db,
)


class NotAuthenticatedError(Exception):
    """JWT 无效或用户不存在时抛出。"""


def get_user_id_from_token(token: str) -> int:
    """从 JWT token 解析 user_id，失败抛出 NotAuthenticatedError。"""
    if not token:
        raise NotAuthenticatedError("missing token")
    payload = AuthService.decode_token(token)
    if payload is None or "user_id" not in payload:
        raise NotAuthenticatedError("invalid token")
    return payload["user_id"]


@asynccontextmanager
async def agent_context(user_id: int) -> AsyncGenerator[int, None]:
    """设置当前请求的 user_id 和 DB session 到 contextvars。

    用法:
        async with agent_context(user_id):
            await agent_app.state.session.load_session_state(
                session_id=session_id, user_id=user_id, agent=agent)
            async for msg, last in stream_printing_messages(...):
                yield msg, last
            await agent_app.state.session.save_session_state(
                session_id=session_id, user_id=user_id, agent=agent)
    """
    db = SessionLocal()
    user_token = _current_user_id.set(user_id)
    db_token = _current_db.set(db)

    try:
        yield user_id
    finally:
        _current_user_id.reset(user_token)
        _current_db.reset(db_token)
        try:
            db.rollback()
        finally:
            db.close()
