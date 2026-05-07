"""长期记忆管理 API 路由。"""
import json
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


# ---------------------------------------------------------------------------
# Memory update config (nightly schedule + custom prompt)
# ---------------------------------------------------------------------------


class ActiveHoursModel(BaseModel):
    start: str = "08:00"
    end: str = "22:00"


class HeartbeatConfigModel(BaseModel):
    enabled: bool = False
    every: str = "6h"
    target: str = "main"
    active_hours: ActiveHoursModel | None = None


class MemoryConfigResponse(BaseModel):
    heartbeat: HeartbeatConfigModel = HeartbeatConfigModel()


class MemoryConfigRequest(BaseModel):
    heartbeat: HeartbeatConfigModel | None = None


def _merge_heartbeat_to_agent_json(
    user_id: int,
    hb: HeartbeatConfigModel,
) -> None:
    """将心跳配置同步写入 agent.json，供 load_agent_config() 加载。"""
    try:
        from src.agents.harness.workspace.user_workspace import get_user_workspace
        user_dir = get_user_workspace(user_id)
        agent_config_path = user_dir / "agent.json"
        import json

        agent_config = {}
        if agent_config_path.exists():
            with open(agent_config_path, encoding="utf-8") as f:
                agent_config = json.load(f)

        agent_config["heartbeat"] = {
            "enabled": hb.enabled,
            "every": hb.every,
            "target": hb.target,
        }
        if hb.active_hours:
            agent_config["heartbeat"]["active_hours"] = {
                "start": hb.active_hours.start,
                "end": hb.active_hours.end,
            }

        with open(agent_config_path, "w", encoding="utf-8") as f:
            json.dump(agent_config, f, indent=2, ensure_ascii=False)
    except Exception:
        logger.exception("Failed to sync heartbeat config to agent.json")


@router.get("/config", response_model=MemoryConfigResponse)
async def get_memory_config(
    authorization: str | None = Header(default=None),
):
    """获取记忆自动更新 + 心跳配置。"""
    ltm, _ = _get_long_term_memory(authorization)
    cfg = ltm.load_config()
    return MemoryConfigResponse(**cfg)


@router.put("/config")
async def update_memory_config(
    body: MemoryConfigRequest,
    authorization: str | None = Header(default=None),
):
    """更新心跳配置。"""
    ltm, user_id = _get_long_term_memory(authorization)
    current = ltm.load_config()
    if body.heartbeat is not None:
        current["heartbeat"] = body.heartbeat.model_dump()
        # 同步到 agent.json 供运行时加载
        _merge_heartbeat_to_agent_json(user_id, body.heartbeat)
    ltm.save_config(current)
    return {"status": "ok"}


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
