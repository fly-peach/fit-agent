"""Session management API router.

Moved from app/routers/agent.py to keep chat-related endpoints co-located
with their models and CRUD under the agents module.

会话消息现在通过 ``FitAgentSQLMemory``（基于 AsyncSQLAlchemyMemory）
从 ``agent_memory.db`` 读取，取代了旧的 ``chat_messages`` 表手动 CRUD。
"""
import json
import logging
import re
import datetime

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from agentscope.message import Msg

from src.fitme.utils.database import UserSessionLocal, async_agent_memory_engine
from src.agents.harness.memory.fitagent_memory import FitAgentSQLMemory
from src.agents.harness.context import get_user_id_from_token, NotAuthenticatedError
from .crud import (
    get_sessions,
    get_session as get_session_crud,
    create_session,
    update_session as update_session_crud,
    delete_session,
)

logger = logging.getLogger("fitagent")

router = APIRouter(tags=["chat"])  # 无 prefix，由父 router 提供 /api/agent


# ---------------------------------------------------------------------------
# Pydantic models for API responses
# ---------------------------------------------------------------------------


class SessionResponse(BaseModel):
    id: str
    name: str
    messages: list[dict] = []
    generating: bool = False


class CreateSessionRequest(BaseModel):
    id: str | None = None
    name: str = "新对话"


class UpdateSessionRequest(BaseModel):
    name: str | None = None
    pinned: bool | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_user_id(authorization: str | None) -> int:
    """从 Authorization header 提取并验证用户 ID。"""
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    try:
        return get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")


def _validate_session_id(session_id: str) -> None:
    if not re.match(r'^[a-zA-Z0-9_\-]+$', session_id):
        raise HTTPException(
            status_code=400,
            detail="session_id 仅支持字母、数字、下划线、短横线",
        )


async def _msg_to_ui_dict(msg: Msg) -> dict:
    """将 Msg 对象转换为前端 UI 格式。"""
    # 提取文本内容
    content = msg.content
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif block.get("type") == "image":
                    texts.append("[图片]")
        text = "\n".join(texts)
    else:
        text = str(content) if content else ""

    return {
        "id": msg.id or "",
        "role": msg.role or "assistant",
        "cards": [{"code": "markdown", "data": text}],
        "msgStatus": "finished",
    }


async def _load_messages_from_memory(user_id: int, session_id: str) -> list[dict]:
    """从 FitAgentSQLMemory 加载会话消息，转为 UI 格式。"""
    memory = FitAgentSQLMemory(
        engine_or_session=async_agent_memory_engine,
        user_id=str(user_id),
        session_id=session_id,
    )
    try:
        msgs = await memory.get_memory(prepend_summary=False)
        return [await _msg_to_ui_dict(m) for m in msgs]
    finally:
        await memory.close()


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    authorization: str | None = Header(default=None),
):
    """获取当前用户的所有会话列表（合并 chat_sessions + agent_memory.db）。"""
    user_id = _get_user_id(authorization)

    # 从 chat_sessions 读元信息
    db = UserSessionLocal()
    try:
        sessions = get_sessions(db, user_id)
        seen = {s.id for s in sessions}
        result = [
            SessionResponse(id=s.id, name=s.name, messages=[], generating=False)
            for s in sessions
        ]
    finally:
        db.close()

    # 自愈：扫描 agent_memory.db，补上 chat_sessions 中遗漏的 session
    memory = FitAgentSQLMemory(
        engine_or_session=async_agent_memory_engine,
        user_id=str(user_id),
        session_id="_list",  # 使用 dummy session_id，仅用于建表
    )
    try:
        await memory._create_table()
        # 直接查 AsyncSQLAlchemyMemory 内部的 session 表
        from sqlalchemy import select as sa_select
        session_table = memory.SessionTable
        stmt = sa_select(session_table.id).where(
            session_table.user_id == str(user_id)
        )
        res = await memory.session.execute(stmt)
        rows = res.scalars().all()
        for sid in rows:
            if sid not in seen:
                # 自动补建 chat_sessions 行
                db2 = UserSessionLocal()
                try:
                    create_session(db2, user_id, sid, name="新对话")
                finally:
                    db2.close()
                result.append(
                    SessionResponse(id=sid, name="新对话", messages=[], generating=False)
                )
    finally:
        await memory.close()

    return result


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_detail(
    session_id: str,
    authorization: str | None = Header(default=None),
):
    """获取会话详情（含消息列表，从 FitAgentSQLMemory 读取）。

    若 chat_sessions 中不存在但 agent_memory.db 中有消息记录，
    自动补建 chat_sessions 行，实现自愈。"""
    _validate_session_id(session_id)
    user_id = _get_user_id(authorization)

    # 先从 agent_memory.db 读取消息（优先，消息更准确）
    messages = await _load_messages_from_memory(user_id, session_id)

    # 再查 chat_sessions 获取元信息
    db = UserSessionLocal()
    try:
        session = get_session_crud(db, user_id, session_id)
        if session is None:
            # 自愈：如果 agent_memory.db 有消息但 chat_sessions 没有记录，自动补建
            if messages:
                session = create_session(db, user_id, session_id, name="新对话")
            else:
                raise HTTPException(status_code=404, detail="Session not found")

        return SessionResponse(
            id=session.id,
            name=session.name,
            messages=messages,
            generating=False,
        )
    finally:
        db.close()


@router.post("/sessions", response_model=list[SessionResponse])
async def create_new_session(
    body: CreateSessionRequest,
    authorization: str | None = Header(default=None),
):
    """创建新会话。优先使用前端传入的 id，否则生成时间戳 id。"""
    user_id = _get_user_id(authorization)
    session_id = body.id or str(int(datetime.datetime.now().timestamp() * 1000))
    _validate_session_id(session_id)
    db = UserSessionLocal()
    try:
        # 幂等：如果 session 已存在则返回已有数据
        existing = get_session_crud(db, user_id, session_id)
        if existing is None:
            create_session(db, user_id, session_id, body.name)
        sessions = get_sessions(db, user_id)
        return [
            SessionResponse(id=s.id, name=s.name, messages=[], generating=False)
            for s in sessions
        ]
    finally:
        db.close()


@router.put("/sessions/{session_id}", response_model=list[SessionResponse])
async def update_session(
    session_id: str,
    body: UpdateSessionRequest,
    authorization: str | None = Header(default=None),
):
    """更新会话名称。"""
    _validate_session_id(session_id)
    user_id = _get_user_id(authorization)
    db = UserSessionLocal()
    try:
        updated = update_session_crud(db, user_id, session_id, 
                                       name=body.name, pinned=body.pinned)
        if updated is None:
            raise HTTPException(status_code=404, detail="Session not found")
        sessions = get_sessions(db, user_id)
        return [
            SessionResponse(id=s.id, name=s.name, messages=[], generating=False)
            for s in sessions
        ]
    finally:
        db.close()


@router.delete("/sessions/{session_id}", response_model=list[SessionResponse])
async def delete_session_endpoint(
    session_id: str,
    authorization: str | None = Header(default=None),
):
    """删除会话（从 chat_sessions 和 agent_memory.db 中删除）。"""
    _validate_session_id(session_id)
    user_id = _get_user_id(authorization)

    # 1. 清理 agent_memory.db 中的消息
    memory = FitAgentSQLMemory(
        engine_or_session=async_agent_memory_engine,
        user_id=str(user_id),
        session_id=session_id,
    )
    try:
        await memory.delete()
    finally:
        await memory.close()

    # 2. 清理 chat_sessions 表
    db = UserSessionLocal()
    try:
        deleted = delete_session(db, user_id, session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")
        sessions = get_sessions(db, user_id)
        return [
            SessionResponse(id=s.id, name=s.name, messages=[], generating=False)
            for s in sessions
        ]
    finally:
        db.close()
