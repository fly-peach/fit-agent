"""User Profile Tool

Direct read-only tool for fetching user profile data via HTTP API.
Bypasses the approval system since it's a pure read operation.
"""
import json
import os
import logging

import httpx

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("FITME_API_URL", "http://localhost:8000")


def _resolve_token(token: str | None) -> str | None:
    if not token:
        return None
    t = token.strip()
    if t.lower().startswith("bearer "):
        t = t[7:].strip()
    return t or None


async def get_user_profile(
    auth_token: str | None = None,
) -> ToolResponse:
    """获取用户个人信息（只读）。

    Args:
        auth_token: 用户认证 token（由工具系统自动注入）
    """
    token = _resolve_token(auth_token)
    if not token:
        return ToolResponse(content=[TextBlock(type="text", text="错误: 缺少认证 token，请先登录")])

    url = f"{API_BASE_URL}/api/user/profile"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            return ToolResponse(content=[TextBlock(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))])
    except Exception as e:
        return ToolResponse(content=[TextBlock(type="text", text=f"获取用户信息失败: {e}")])
