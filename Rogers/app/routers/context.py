"""上下文管理 API 路由。"""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from src.agents.harness.context import get_user_id_from_token, NotAuthenticatedError
from src.agents.harness.workspace.user_workspace import get_user_workspace
from src.agents.harness.context.tool_result_cache import ToolResultCache, CacheEntry

logger = logging.getLogger("fitagent")

router = APIRouter(prefix="/api/agent/context", tags=["context"])


class ContextStats(BaseModel):
    current_tokens: int = 0
    max_tokens: int = 131072
    compaction_count_today: int = 0
    compaction_count_total: int = 0
    cache_file_count: int = 0
    cache_total_size_bytes: int = 0
    avg_response_tokens: int = 0


class CompactResponse(BaseModel):
    success: bool
    reason: str = ""


def _get_tool_result_cache(authorization: str | None) -> tuple[ToolResultCache, int]:
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")
    user_dir = get_user_workspace(user_id)
    return ToolResultCache(user_dir), user_id


@router.get("/stats", response_model=ContextStats)
async def get_context_stats(authorization: str | None = Header(default=None)):
    cache, _ = _get_tool_result_cache(authorization)
    cache_entries = cache.list_cache()
    total_size = sum(e.size_bytes for e in cache_entries)

    return ContextStats(
        cache_file_count=len(cache_entries),
        cache_total_size_bytes=total_size,
    )


@router.get("/cache", response_model=List[CacheEntry])
async def list_cache(authorization: str | None = Header(default=None)):
    cache, _ = _get_tool_result_cache(authorization)
    return cache.list_cache()


@router.get("/cache/{cache_id:path}")
async def get_cache(cache_id: str, authorization: str | None = Header(default=None)):
    cache, _ = _get_tool_result_cache(authorization)
    content = cache.get_cached_result(cache_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Cache entry not found")
    return {"content": content, "id": cache_id}


@router.delete("/cache")
async def clear_cache(authorization: str | None = Header(default=None)):
    cache, _ = _get_tool_result_cache(authorization)
    count = cache.clear_all()
    return {"status": "ok", "cleared": count}


@router.post("/compact", response_model=CompactResponse)
async def trigger_compact(authorization: str | None = Header(default=None)):
    from src.agents.agent import agent_cache

    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")

    agent = await agent_cache.get_or_create(user_id)
    memory_manager = getattr(agent, "_memory_manager", None)

    if not memory_manager:
        return CompactResponse(success=False, reason="Memory manager not available")

    try:
        memory = agent.memory
        messages = await memory.get_memory(prepend_summary=False)
        previous_summary = memory.get_compressed_summary()

        compact_result = await memory_manager.compact_memory(
            messages=messages,
            previous_summary=previous_summary,
        )

        if compact_result:
            await memory.update_compressed_summary(compact_result)
            return CompactResponse(success=True)
        else:
            return CompactResponse(success=False, reason="Compaction returned empty result")

    except Exception as e:
        return CompactResponse(success=False, reason=str(e))
