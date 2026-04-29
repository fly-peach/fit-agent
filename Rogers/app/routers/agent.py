import os
import logging

from agentscope.pipeline import stream_printing_messages
from src.agents.agent import agent_cache
from agentscope_runtime.engine.app import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from src.agents.harness.context import agent_context, NotAuthenticatedError, get_user_id_from_token
from src.agents.user_workspace import get_user_workspace, ensure_user_workspace

logger = logging.getLogger("fitagent")

# 创建 AgentApp
agent_app = AgentApp(
    app_name="MyAssistant",
    app_description="A helpful assistant agent",
)

@agent_app.query(framework="agentscope")
async def query_func(
    self,
    msgs,
    request: AgentRequest | None = None,
    **kwargs,
):
    """处理用户查询。"""
    assert request is not None, "request is required"
    session_id = request.session_id or "default"

    # 从 Header 获取 JWT token，不信任请求体
    auth_header = kwargs.get("auth_header") or ""
    try:
        user_id = get_user_id_from_token(auth_header)
    except NotAuthenticatedError:
        yield "请先登录后再使用助手。", True
        return

    agent = await agent_cache.get_or_create(user_id)
    agent.set_console_output_enabled(False)

    async with agent_context(user_id):
        await agent_app.state.session.load_session_state(
            session_id=session_id,
            user_id=str(user_id),
            agent=agent,
        )

        async for msg, last, *_ in stream_printing_messages(
            agents=[agent],
            coroutine_task=agent(msgs),
        ):
            yield msg, last

        await agent_app.state.session.save_session_state(
            session_id=session_id,
            user_id=str(user_id),
            agent=agent,
        )


router = APIRouter(prefix="/api/agent", tags=["agent"])

@router.post("/chat")
async def agent_chat(
    request: AgentRequest,
    authorization: str | None = Header(default=None),
):
    """发送消息到 agent，通过 Header 认证。"""
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")

    session_id = request.session_id or f"user-{user_id}"

    agent = await agent_cache.get_or_create(user_id)
    agent.set_console_output_enabled(False)

    async with agent_context(user_id):
        await agent_app.state.session.load_session_state(
            session_id=session_id,
            user_id=str(user_id),
            agent=agent,
        )

        full_response = ""
        async for msg, last, *_ in stream_printing_messages(
            agents=[agent],
            coroutine_task=agent(request.input),
        ):
            if msg and hasattr(msg, "content"):
                full_response += str(msg.content)

        await agent_app.state.session.save_session_state(
            session_id=session_id,
            user_id=str(user_id),
            agent=agent,
        )

    return {"response": full_response}


# ---------------------------------------------------------------------------
# Per-user agent configuration management
# ---------------------------------------------------------------------------

class AgentConfigUpdate(BaseModel):
    agents_md: str | None = None
    soul_md: str | None = None


class AgentConfigResponse(BaseModel):
    agents_md: str
    soul_md: str


@router.get("/config", response_model=AgentConfigResponse)
async def get_agent_config(
    authorization: str | None = Header(default=None),
):
    """获取当前用户的 agent 配置。"""
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")

    user_dir = get_user_workspace(user_id)
    agents_md = (user_dir / "agents.md").read_text(encoding="utf-8") if (user_dir / "agents.md").exists() else ""
    soul_md = (user_dir / "soul.md").read_text(encoding="utf-8") if (user_dir / "soul.md").exists() else ""

    return AgentConfigResponse(agents_md=agents_md, soul_md=soul_md)


@router.put("/config")
async def update_agent_config(
    body: AgentConfigUpdate,
    authorization: str | None = Header(default=None),
):
    """更新当前用户的 agent 配置。"""
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")

    user_dir = ensure_user_workspace(user_id)

    if body.agents_md is not None:
        (user_dir / "agents.md").write_text(body.agents_md, encoding="utf-8")
    if body.soul_md is not None:
        (user_dir / "soul.md").write_text(body.soul_md, encoding="utf-8")

    # Evict cached agent so next request picks up new prompt
    await agent_cache.evict(user_id)

    return {"status": "ok"}


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    authorization: str | None = Header(default=None),
):
    """删除指定 session 文件。"""
    token = ""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]

    try:
        user_id = get_user_id_from_token(token)
    except NotAuthenticatedError:
        raise HTTPException(status_code=401, detail="请先登录")

    user_dir = get_user_workspace(user_id)
    session_file = user_dir / "sessions" / f"{session_id}.json"

    if session_file.exists():
        session_file.unlink()
        return {"status": "ok"}

    raise HTTPException(status_code=404, detail="Session not found")
