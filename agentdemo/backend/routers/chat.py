# Chat endpoint with SSE streaming for AgentScopeRuntimeWebUI
from typing import Optional
from fastapi import APIRouter, HTTPException
from starlette.responses import StreamingResponse

import agent

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/approve")
async def approve_tool(request: dict):
    """Submit approval for a tool execution."""
    approval_id = request.get("approval_id")
    approved = request.get("approved", False)

    if not approval_id:
        raise HTTPException(400, "No approval_id provided")

    success = agent.submit_approval(approval_id, approved)
    if not success:
        raise HTTPException(404, "Approval request not found or already processed")

    return {"success": True, "approval_id": approval_id, "approved": approved}


def extract_user_text(input_messages: list) -> str:
    """Extract text from user input messages."""
    texts = []
    for msg in input_messages:
        if msg.get("role") == "user":
            content = msg.get("content", [])
            if isinstance(content, str):
                texts.append(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        texts.append(part.get("text", ""))
    return " ".join(texts)


@router.post("")
async def chat(request: dict) -> StreamingResponse:
    """Stream agent response in SSE format with optional reasoning and tool support."""
    input_messages = request.get("input", [])
    if not input_messages:
        raise HTTPException(400, "No input")

    user_text = extract_user_text(input_messages)
    if not user_text.strip():
        raise HTTPException(400, "Empty message")

    session_id = request.get("session_id")
    # Support optional reasoning and tool modes
    enable_reasoning = request.get("enable_reasoning", False)
    enable_tools = request.get("enable_tools", False)
    # 获取需要审批的工具列表
    tools_require_approval = request.get("tools_require_approval", ["execute_python", "execute_shell_command"])

    ag = agent.get_agent(
        session_id,
        enable_reasoning=enable_reasoning,
        enable_tools=enable_tools,
        tools_require_approval=tools_require_approval
    )

    # chat_stream is an async generator, iterate directly
    async def generate():
        async for event in ag.chat_stream(user_text, session_id):
            yield event

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/clear")
async def clear_chat(request: dict):
    """Clear session memory."""
    session_id = request.get("session_id")
    agent.clear_session(session_id)
    return {"cleared": True}


@router.get("/sessions")
async def get_sessions():
    """Get all active session IDs."""
    return {"sessions": agent.get_session_ids()}


@router.post("/system-prompt")
async def set_system_prompt(request: dict):
    """Update system prompt for a session."""
    session_id = request.get("session_id")
    prompt = request.get("prompt", "")

    ag = agent.get_agent(session_id)
    ag.set_system_prompt(prompt)

    return {"success": True, "system_prompt": prompt}