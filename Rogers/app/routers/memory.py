"""长期记忆管理 API 路由。"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from src.agents.harness.context import get_user_id_from_token, NotAuthenticatedError
from src.agents.harness.workspace.user_workspace import get_user_workspace
from src.agents.harness.memory.long_term_memory import LongTermMemory
from src.agents.harness.memory.memory_optimizer import MemoryOptimizer

logger = logging.getLogger("fitagent")

router = APIRouter(prefix="/api/agent/memory", tags=["memory"])


class MemoryResponse(BaseModel):
    content: str
    last_updated: str


class MemoryUpdateRequest(BaseModel):
    content: str


class DailyLogResponse(BaseModel):
    date: str
    content: str


class OptimizationResponse(BaseModel):
    success: bool
    reason: str = ""
    date: str = ""
    backup_path: str | None = None


def _get_long_term_memory(authorization: str | None) -> tuple[LongTermMemory, int]:
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")
    user_dir = get_user_workspace(user_id)
    ltm = LongTermMemory(user_dir)
    ltm.init_memory_file()
    return ltm, user_id


@router.get("", response_model=MemoryResponse)
async def get_memory(authorization: str | None = Header(default=None)):
    ltm, _ = _get_long_term_memory(authorization)
    content = ltm.load_memory()
    import os
    mtime = ""
    if ltm.memory_file.exists():
        mtime = str(datetime.fromtimestamp(os.path.getmtime(ltm.memory_file)))
    return MemoryResponse(content=content, last_updated=mtime)


@router.put("")
async def update_memory(
    body: MemoryUpdateRequest,
    authorization: str | None = Header(default=None),
):
    ltm, _ = _get_long_term_memory(authorization)
    ltm.save_memory(body.content)
    return {"status": "ok"}


@router.get("/logs", response_model=List[str])
async def list_logs(authorization: str | None = Header(default=None)):
    ltm, _ = _get_long_term_memory(authorization)
    return ltm.list_log_dates()


@router.get("/logs/{date}", response_model=DailyLogResponse)
async def get_log(date: str, authorization: str | None = Header(default=None)):
    ltm, _ = _get_long_term_memory(authorization)
    content = ltm.get_daily_log(date)
    if content is None:
        raise HTTPException(status_code=404, detail="Log not found")
    return DailyLogResponse(date=date, content=content)


@router.delete("/logs/{date}")
async def delete_log(date: str, authorization: str | None = Header(default=None)):
    ltm, _ = _get_long_term_memory(authorization)
    if not ltm.delete_daily_log(date):
        raise HTTPException(status_code=404, detail="Log not found")
    return {"status": "ok", "date": date}


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_memory(authorization: str | None = Header(default=None)):
    from src.agents.agent import create_user_agent

    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")

    user_dir = get_user_workspace(user_id)
    ltm = LongTermMemory(user_dir)
    ltm.init_memory_file()

    agent = create_user_agent(user_id)
    model = getattr(agent, "model", None)

    optimizer = MemoryOptimizer(ltm, model)
    result = await optimizer.optimize()

    return OptimizationResponse(**result)


# 心跳配置已统一到 agent.json，不再使用 memory_config.json 独立存储
# GET/PUT /api/agent/memory/config 端点已在清理中移除

# ---------------------------------------------------------------------------
# HEARTBEAT.md 读写
# ---------------------------------------------------------------------------


class HeartbeatDocResponse(BaseModel):
    content: str


class HeartbeatDocUpdateRequest(BaseModel):
    content: str


@router.get("/heartbeat-doc", response_model=HeartbeatDocResponse)
async def get_heartbeat_doc(
    authorization: str | None = Header(default=None),
):
    """读取 HEARTBEAT.md 内容。"""
    _, user_id = _get_long_term_memory(authorization)
    user_dir = get_user_workspace(user_id)
    hb_path = user_dir / "HEARTBEAT.md"
    content = hb_path.read_text(encoding="utf-8") if hb_path.exists() else ""
    return HeartbeatDocResponse(content=content)


@router.put("/heartbeat-doc")
async def update_heartbeat_doc(
    body: HeartbeatDocUpdateRequest,
    authorization: str | None = Header(default=None),
):
    """写入 HEARTBEAT.md。"""
    _, user_id = _get_long_term_memory(authorization)
    user_dir = get_user_workspace(user_id)
    hb_path = user_dir / "HEARTBEAT.md"
    hb_path.write_text(body.content, encoding="utf-8")
    return {"status": "ok"}


from datetime import datetime
