"""Session management API router.

Moved from app/routers/agent.py to keep chat-related endpoints co-located
with their models and CRUD under the agents module.
"""
import json
import logging
import re
import datetime

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from src.fitme.utils.database import UserSessionLocal
from src.agents.harness.context import get_user_id_from_token, NotAuthenticatedError
from .crud import (
    get_sessions,
    get_session as get_session_crud,
    create_session,
    update_session_name,
    delete_session,
    get_messages,
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
    name: str = "新对话"


class UpdateSessionRequest(BaseModel):
    name: str


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


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    authorization: str | None = Header(default=None),
):
    """获取当前用户的所有会话列表。"""
    user_id = _get_user_id(authorization)
    db = UserSessionLocal()
    try:
        sessions = get_sessions(db, user_id)
        return [
            SessionResponse(id=s.id, name=s.name, messages=[], generating=False)
            for s in sessions
        ]
    finally:
        db.close()


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_detail(
    session_id: str,
    authorization: str | None = Header(default=None),
):
    """获取会话详情（含消息列表）。"""
    _validate_session_id(session_id)
    user_id = _get_user_id(authorization)
    db = UserSessionLocal()
    try:
        session = get_session_crud(db, user_id, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        messages_raw = get_messages(db, session_id)
        messages = []
        for m in messages_raw:
            try:
                msg_data = json.loads(m.content)
                messages.append(msg_data)
            except (json.JSONDecodeError, TypeError):
                messages.append({
                    "id": str(m.id),
                    "role": m.role,
                    "cards": [{"code": "markdown", "data": m.content}],
                    "msgStatus": "finished",
                })

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
    """创建新会话。"""
    user_id = _get_user_id(authorization)
    session_id = str(int(datetime.datetime.now().timestamp() * 1000))
    db = UserSessionLocal()
    try:
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
        updated = update_session_name(db, user_id, session_id, body.name)
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
    """删除会话（级联删除所有消息）。"""
    _validate_session_id(session_id)
    user_id = _get_user_id(authorization)
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
