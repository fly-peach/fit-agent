"""Context 管理模块 — 工具结果缓存、请求上下文。"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from src.agents.harness.context.tool_result_cache import ToolResultCache, CacheEntry


class NotAuthenticatedError(Exception):
    """JWT 无效或用户不存在时抛出。"""


def get_user_id_from_token(token: str) -> int:
    """从 JWT token 解析 user_id，失败抛出 NotAuthenticatedError。"""
    from src.fitme.services.auth_service import AuthService

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
            async for msg, last in stream_printing_messages(...):
                yield msg, last
    """
    from src.fitme.utils.database import SessionLocal
    from src.agents.harness.tools.basic.read_data import _current_user_id, _current_db

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


__all__ = ["ToolResultCache", "CacheEntry",
           "agent_context", "NotAuthenticatedError", "get_user_id_from_token"]
