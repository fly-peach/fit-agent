"""
Rogers Agent - Pipeline 多智能体编排

基于 AgentScope Runtime 的多智能体管道工作流。
实际 Pipeline 逻辑在 src.agents.pipeline 中。
"""
import asyncio
import logging
from contextvars import ContextVar

from agentscope_runtime.engine import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest, AgentResponse

from src.agents.agents_pipeline import run_rogers_pipeline

logger = logging.getLogger(__name__)

# 用于 main.py 的 set_auth_token 中间件
_auth_token: ContextVar[str | None] = ContextVar("auth_token", default=None)

# 异步引擎（由 main.py lifespan 初始化，agent.py query_func 使用）
_memory_engine = None


def set_memory_engine(engine) -> None:
    """由 main.py lifespan 调用，设置共享的异步引擎"""
    global _memory_engine
    _memory_engine = engine


# ============================================================================
# 1. 创建 AgentApp（使用 main.py 的 lifespan）
# ============================================================================

agent_app = AgentApp(
    app_name="rogers-agent",
    app_description="Multi-Agent Pipeline: Master → Fanout(DietAnalyst, TrainingAnalyst) → Master",
)


# ============================================================================
# 2. 查询端点（Pipeline SSE 流式输出）
# ============================================================================

@agent_app.query(framework="agentscope")
async def query_func(
    self,
    request: AgentRequest,
    response: "AgentResponse" = None,  # type: ignore[assignment]
    **kwargs,
):
    """Pipeline 多智能体编排 HTTP SSE 端点。

    注意: self 参数是必须的。Runner._build_runner() 通过
    types.MethodType 将 query_func 绑定到 Runner 实例，实际调用为
    query_func(runner_instance, request=..., response=..., msgs=..., ...)。
    缺少 self 会导致 request 参数收到 runner 实例，与关键字参数冲突。
    """
    msgs = kwargs.pop("msgs", [])
    session_id = request.session_id or ""

    # 从 JWT token 中提取真实的 user_id
    # 注意: Runner.stream_query() 会将 request.user_id 覆盖为 session_id
    # （当 user_id 为空时），所以不能直接依赖 request.user_id
    user_id = None
    token = _auth_token.get()
    if token:
        from src.fitme.services.auth_service import AuthService
        uid = AuthService.get_user_id_from_token(token)
        if uid is not None:
            user_id = uid

    logger.info(
        "query_func: session_id=%s user_id=%s (token=%s...)",
        session_id, user_id, token[:8] if token else None,
    )

    db_engine = _memory_engine

    try:
        async for output in run_rogers_pipeline(
            msgs, user_id=user_id, session_id=session_id, db_engine=db_engine, auth_token=token,
        ):
            if len(output) >= 2:
                msg, last = output[0], output[1]
                yield msg, last

    except asyncio.CancelledError:
        logger.info(f"Task {session_id} was manually interrupted.")
        raise


# ============================================================================
# 3. 中断触发路由
# ============================================================================

@agent_app.post("/stop")
async def stop_task(request: AgentRequest):
    user_id = request.user_id or ""
    session_id = request.session_id or ""
    await agent_app.stop_chat(
        user_id=user_id,
        session_id=session_id,
    )
    return {
        "status": "success",
        "message": "Interrupt signal broadcasted.",
    }


# ============================================================================
# 4. Pipeline 历史查询端点（非流式，标准 REST）
# ============================================================================

from fastapi import Query
from pydantic import BaseModel
from typing import Optional


@agent_app.get("/api/agent/pipeline/history")
def get_pipeline_history(
    user_id: int = Query(..., description="用户 ID"),
    session_id: Optional[str] = Query(None, description="会话 ID（可选）"),
    limit: int = Query(20, ge=1, le=100, description="返回条数上限"),
    offset: int = Query(0, ge=0, description="分页偏移"),
):
    """查询 Pipeline 历史交互记录。

    - 必传 user_id
    - 可选 session_id，不传返回该用户所有会话记录
    - 按创建时间降序排列
    """
    from src.agents.harness.memory import list_pipeline_exchanges
    records = list_pipeline_exchanges(
        user_id=user_id,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
    return {
        "data": records,
        "total": len(records),
    }


# ============================================================================
# 5. 删除会话（清除 Pipeline 记录 + AgentScope 内部消息）
# ============================================================================




@agent_app.delete("/api/agent/pipeline/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user_id: int = Query(..., description="用户 ID"),
):
    """删除指定会话的所有数据。

    清除:
    - agent_pipeline_exchanges 表中的交互记录
    - AsyncSQLAlchemyMemory 内部的 message / message_mark 表
    """
    from src.agents.harness.memory import PipelineExchange
    from src.fitme.utils.database import UserSessionLocal
    from src.core.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from agentscope.memory import AsyncSQLAlchemyMemory

    # 1. 删除 Pipeline 交互记录
    db = UserSessionLocal()
    try:
        deleted = (
            db.query(PipelineExchange)
            .filter(
                PipelineExchange.user_id == user_id,
                PipelineExchange.session_id == session_id,
            )
            .delete()
        )
        db.commit()
        logger.info(
            "Deleted %d pipeline exchanges for user=%s session=%s",
            deleted, user_id, session_id,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    # 2. 清除 AgentScope 内部记忆（message + message_mark 表）
    try:
        _async_db_url = settings.USER_DB_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
        engine = create_async_engine(_async_db_url)
        async with AsyncSQLAlchemyMemory(
            engine_or_session=engine,
            user_id=str(user_id),
            session_id=session_id,
        ) as memory:
            await memory.clear()
        await engine.dispose()
        logger.info(
            "Cleared AgentScope memory for user=%s session=%s",
            user_id, session_id,
        )
    except Exception:
        logger.exception("Failed to clear AgentScope memory for session=%s", session_id)

    return {
        "status": "success",
        "message": f"Session {session_id} 数据已清除",
        "pipeline_exchanges_deleted": deleted,
    }
