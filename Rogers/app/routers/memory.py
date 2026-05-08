"""长期记忆管理 API 路由。"""
import json
import logging
from typing import List, Optional

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


# ---------------------------------------------------------------------------
# 记忆配置 + 心跳配置
# 存储到 agent.json（由 load_agent_config() 自动读取）
# ---------------------------------------------------------------------------


class HeartbeatConfigRequest(BaseModel):
    """心跳配置请求。"""
    enabled: bool = False
    every: str = "6h"
    target: str = "main"
    active_hours: Optional[dict] = None


class MemoryConfigResponse(BaseModel):
    """记忆配置 + 心跳配置响应。"""
    heartbeat: HeartbeatConfigRequest = HeartbeatConfigRequest()


class MemoryConfigUpdate(BaseModel):
    """记忆配置 + 心跳配置更新。"""
    heartbeat: Optional[HeartbeatConfigRequest] = None


@router.get("/config", response_model=MemoryConfigResponse)
async def get_memory_config(
    authorization: str | None = Header(default=None),
):
    """读取记忆配置（含心跳配置）。

    从 agent.json 读取心跳设置，返回给前端 MemoryManager 页面。
    """
    _, user_id = _get_long_term_memory(authorization)
    user_dir = get_user_workspace(user_id)

    # 从 agent.json 读取心跳配置
    agent_json = user_dir / "agent.json"
    heartbeat = HeartbeatConfigRequest()
    if agent_json.exists():
        try:
            data = json.loads(agent_json.read_text(encoding="utf-8"))
            hb = data.get("heartbeat", {})
            if hb:
                heartbeat = HeartbeatConfigRequest(
                    enabled=hb.get("enabled", False),
                    every=hb.get("every", "6h"),
                    target=hb.get("target", "main"),
                    active_hours=hb.get("active_hours"),
                )
        except Exception:
            pass

    return MemoryConfigResponse(heartbeat=heartbeat)


@router.put("/config")
async def update_memory_config(
    body: MemoryConfigUpdate,
    authorization: str | None = Header(default=None),
):
    """保存记忆配置（含心跳配置）。

    将心跳配置写入 agent.json，供 create_user_agent() 读取。
    """
    _, user_id = _get_long_term_memory(authorization)
    user_dir = get_user_workspace(user_id)

    agent_json = user_dir / "agent.json"
    try:
        if agent_json.exists():
            data = json.loads(agent_json.read_text(encoding="utf-8"))
        else:
            data = {}

        if body.heartbeat is not None:
            hb = {
                "enabled": body.heartbeat.enabled,
                "every": body.heartbeat.every,
                "target": body.heartbeat.target,
            }
            if body.heartbeat.active_hours:
                hb["active_hours"] = body.heartbeat.active_hours
            data["heartbeat"] = hb

        agent_json.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Saved heartbeat config to agent.json for user %s", user_id)
        return {"status": "ok"}
    except Exception as e:
        logger.error("Failed to save heartbeat config: %s", e)
        raise HTTPException(status_code=500, detail=f"保存配置失败: {e}")


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
