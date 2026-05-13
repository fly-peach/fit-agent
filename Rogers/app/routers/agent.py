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
from src.fitme.services.auth_service import AuthService

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
    self,
    msgs,
    request: AgentRequest = None,  # type: ignore
    **kwargs,
):
    """Pipeline 多智能体编排 HTTP SSE 端点。"""
    session_id = request.session_id or "" if request else ""

    # 从 JWT token 中解析用户 ID（优先使用中间件存的 token）
    parsed_user_id: int | None = None
    token = _auth_token.get()
    if token:
        parsed_user_id = AuthService.get_user_id_from_token(token)
        if parsed_user_id:
            logger.info(f"Parsed user_id from JWT: {parsed_user_id}")

    if not parsed_user_id:
        # 尝试从 request.user_id 解析（fallback）
        user_id_str = request.user_id or None if request else None
        if user_id_str:
            try:
                parsed_user_id = int(user_id_str)
            except ValueError:
                logger.warning(f"Invalid user_id format: {user_id_str}, converting to None")

    if not parsed_user_id:
        raise ValueError("No valid user_id found in request or JWT token")

    try:
        async for output in run_rogers_pipeline(msgs, user_id=parsed_user_id):
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
