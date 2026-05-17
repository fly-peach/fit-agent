"""Agent Config Router — API Key 管理

API Key 不再从环境变量读取，通过此路由由用户自行设置，
使用 fakeredis 缓存（有效期为 7 天）。
"""
import logging
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional

from src.fitme.services.auth_service import AuthService
from src.agents.utils.api_key_cache import api_key_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["Agent Config"])


# ── Schemas ─────────────────────────────────────────────────────────────────

class SetApiKeyRequest(BaseModel):
    """设置 API Key 请求"""
    api_key: str = Field(..., min_length=1, description="API Key")


class ApiKeyStatusResponse(BaseModel):
    """API Key 状态响应"""
    has_api_key: bool = Field(..., description="是否已设置 API Key")


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str


# ── 辅助函数 ──────────────────────────────────────────────────────────────

def _get_user_id(authorization: Optional[str] = Header(None)) -> int:
    """从 JWT token 中提取 user_id"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user_id = AuthService.get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的 Token")
    return user_id


# ── API Key 端点 ───────────────────────────────────────────────────────────

@router.get("/api-key/status", response_model=ApiKeyStatusResponse)
def get_api_key_status(
    authorization: Optional[str] = Header(None),
):
    """获取 API Key 配置状态"""
    user_id = _get_user_id(authorization)
    has_key = api_key_cache.has_api_key(user_id)
    logger.info(f"API Key status check for user_id {user_id}: {has_key}")
    return ApiKeyStatusResponse(
        has_api_key=has_key,
    )


@router.post("/api-key", response_model=MessageResponse)
@router.put("/api-key", response_model=MessageResponse)
def set_api_key(
    body: SetApiKeyRequest,
    authorization: Optional[str] = Header(None),
):
    """设置 API Key（缓存 7 天）"""
    user_id = _get_user_id(authorization)
    logger.info(f"Setting API Key for user_id: {user_id}")
    api_key_cache.set(user_id, body.api_key)
    return MessageResponse(message="API Key 设置成功")


@router.delete("/api-key", response_model=MessageResponse)
def delete_api_key(
    authorization: Optional[str] = Header(None),
):
    """删除 API Key"""
    user_id = _get_user_id(authorization)
    logger.info(f"Deleting API Key for user_id: {user_id}")
    api_key_cache.delete(user_id)
    return MessageResponse(message="API Key 已删除")
