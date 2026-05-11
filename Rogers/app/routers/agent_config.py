"""Agent Config Router - New DB-only Configuration

Deprecated the old local directory approach. Now:
- API Key stored in in-memory cache (5-day TTL)
- Prompt templates (agents.md, soul.md) stored in DB
- Model names fixed internally (qwen-vl-max, qwen-max)
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from src.fitme.utils.database import get_user_db
from src.fitme.services.auth_service import AuthService
from src.fitme.schemas.agent import (
    SetApiKeyRequest,
    ApiKeyStatusResponse,
    PromptTemplatesResponse,
    UpdatePromptsRequest,
    AgentConfigStatusV2,
)
from src.fitme.schemas.common import BaseResponse
from src.agents.utils.api_key_cache import api_key_cache
from src.agents.harness.workspace.prompt_templates import (
    get_user_prompt_templates,
    update_user_prompt_templates,
    get_or_create_prompt_templates,
)
from src.agents.harness.templates.templates import get_template_path


router = APIRouter(prefix="/api/agent/config", tags=["Agent Config"])


def get_current_user(
    authorization: Optional[str] = Header(None),
    user_db: Session = Depends(get_user_db)
):
    """获取当前用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未授权")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    user = AuthService.get_user_from_token(user_db, token)
    if not user:
        raise HTTPException(status_code=401, detail="登录过期")
    return user


# ---------------------------------------------------------------------------
# API Key Endpoints
# ---------------------------------------------------------------------------

@router.post("/api-key", response_model=BaseResponse)
def set_api_key(
    body: SetApiKeyRequest,
    current_user=Depends(get_current_user),
):
    """设置用户 API Key（存入缓存，TTL 5天）"""
    api_key = body.api_key.strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key 不能为空")

    api_key_cache.set(current_user.user_id, api_key)
    return BaseResponse(message="API Key 已设置")


@router.delete("/api-key", response_model=BaseResponse)
def delete_api_key(
    current_user=Depends(get_current_user),
):
    """清除用户 API Key"""
    api_key_cache.delete(current_user.user_id)
    return BaseResponse(message="API Key 已清除")


@router.get("/api-key/status", response_model=ApiKeyStatusResponse)
def get_api_key_status(
    current_user=Depends(get_current_user),
):
    """检查用户是否已设置 API Key"""
    has_key = api_key_cache.has_api_key(current_user.user_id)
    return ApiKeyStatusResponse(has_api_key=has_key)


# ---------------------------------------------------------------------------
# Prompt Templates Endpoints
# ---------------------------------------------------------------------------

@router.get("/prompts", response_model=PromptTemplatesResponse)
def get_prompts(
    current_user=Depends(get_current_user),
    user_db: Session = Depends(get_user_db),
):
    """获取用户提示词模板"""
    templates = get_or_create_prompt_templates(user_db, current_user.user_id)
    return PromptTemplatesResponse(
        agents_md=templates.agents_md,
        soul_md=templates.soul_md,
        updated_at=templates.updated_at,
    )


@router.put("/prompts", response_model=PromptTemplatesResponse)
def update_prompts(
    body: UpdatePromptsRequest,
    current_user=Depends(get_current_user),
    user_db: Session = Depends(get_user_db),
):
    """更新用户提示词模板"""
    templates = update_user_prompt_templates(
        user_db,
        current_user.user_id,
        agents_md=body.agents_md,
        soul_md=body.soul_md,
    )
    return PromptTemplatesResponse(
        agents_md=templates.agents_md,
        soul_md=templates.soul_md,
        updated_at=templates.updated_at,
    )


# ---------------------------------------------------------------------------
# Combined Status Endpoint
# ---------------------------------------------------------------------------

@router.get("/status", response_model=AgentConfigStatusV2)
def get_config_status(
    current_user=Depends(get_current_user),
    user_db: Session = Depends(get_user_db),
):
    """获取用户 Agent 配置状态"""
    has_api_key = api_key_cache.has_api_key(current_user.user_id)
    templates = get_user_prompt_templates(user_db, current_user.user_id)
    has_prompts = templates is not None and (bool(templates.agents_md) or bool(templates.soul_md))
    return AgentConfigStatusV2(
        has_api_key=has_api_key,
        has_prompts=has_prompts,
    )


# ---------------------------------------------------------------------------
# Deprecated Endpoints (keep for backwards compatibility)
# ---------------------------------------------------------------------------

@router.get("/workspace/status", tags=["Deprecated"])
def deprecated_workspace_status():
    """Deprecated: Use /api/agent/config/status instead"""
    raise HTTPException(status_code=410, detail="此端点已废弃，请使用新的配置接口")


@router.post("/workspace", tags=["Deprecated"])
def deprecated_create_workspace():
    """Deprecated: Local workspace no longer used"""
    raise HTTPException(status_code=410, detail="此端点已废弃，不再使用本地工作目录")


@router.put("/workspace", tags=["Deprecated"])
def deprecated_update_workspace():
    """Deprecated: Local workspace no longer used"""
    raise HTTPException(status_code=410, detail="此端点已废弃，不再使用本地工作目录")


@router.delete("/workspace", tags=["Deprecated"])
def deprecated_delete_workspace():
    """Deprecated: Local workspace no longer used"""
    raise HTTPException(status_code=410, detail="此端点已废弃，不再使用本地工作目录")
