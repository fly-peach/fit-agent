"""
Rogers Agent - Pipeline 多智能体编排

基于 AgentScope Runtime 的多智能体管道工作流。
实际 Pipeline 逻辑在 src.agents.pipeline 中。
"""
import asyncio
import logging
from contextvars import ContextVar

from agentscope_runtime.engine import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest

from src.agents.agents_pipeline import run_rogers_pipeline

logger = logging.getLogger(__name__)

# 用于 main.py 的 set_auth_token 中间件
_auth_token: ContextVar[str | None] = ContextVar("auth_token", default=None)


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
    msgs,
    request: AgentRequest,
):
    """Pipeline 多智能体编排 HTTP SSE 端点。"""
    session_id = request.session_id or ""
    user_id = request.user_id or None

    try:
        async for output in run_rogers_pipeline(msgs, user_id=user_id):
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
