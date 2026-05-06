"""Agent Config Router - User's local Agent directory configuration"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from src.fitme.utils.database import get_user_db
from src.fitme.crud import agent_config as crud
from src.fitme.schemas.agent import (
    UserAgentConfigCreate,
    UserAgentConfigUpdate,
    UserAgentConfigResponse,
    AgentConfigStatus,
)
from src.fitme.schemas.common import BaseResponse
from src.fitme.utils.agent_directory import (
    validate_and_create_agent_directory,
    initialize_agent_directory,
    is_directory_structure_complete,
    get_default_agent_directory,
)
from src.fitme.services.auth_service import AuthService

router = APIRouter(prefix="/api/agent/workspace", tags=["Agent Config"])


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


@router.get("/status", response_model=AgentConfigStatus)
def get_agent_config_status(
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """获取用户的 Agent 配置状态"""
    config = crud.get_user_agent_config(user_db, current_user.user_id)
    if config and config.local_working_dir:
        return AgentConfigStatus(
            is_configured=True,
            local_working_dir=config.local_working_dir
        )
    return AgentConfigStatus(
        is_configured=False,
        local_working_dir=None
    )


@router.post("", response_model=UserAgentConfigResponse)
def create_or_update_agent_config(
    config_data: UserAgentConfigCreate,
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """创建或更新用户的 Agent 配置"""
    local_dir = config_data.local_working_dir

    # 如果没有指定目录，使用默认目录
    if not local_dir:
        local_dir = get_default_agent_directory()

    # 验证路径的有效性并创建目录
    if not validate_and_create_agent_directory(local_dir):
        raise HTTPException(
            status_code=400,
            detail="路径无效或无法创建目录，请检查路径权限"
        )

    # 初始化 Agent 目录结构
    try:
        initialize_agent_directory(local_dir)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"初始化目录失败: {str(e)}"
        )

    # 保存配置
    config = crud.update_user_agent_config(
        user_db, current_user.user_id, local_dir
    )

    return config


@router.put("", response_model=UserAgentConfigResponse)
def update_agent_config(
    config_data: UserAgentConfigUpdate,
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """更新用户的 Agent 配置（修改存储路径）"""
    local_dir = config_data.local_working_dir

    if not local_dir:
        raise HTTPException(
            status_code=400,
            detail="存储路径不能为空"
        )

    # 验证新路径
    if not validate_and_create_agent_directory(local_dir):
        raise HTTPException(
            status_code=400,
            detail="新路径无效或无法创建目录"
        )

    # 初始化新目录
    try:
        initialize_agent_directory(local_dir)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"初始化新目录失败: {str(e)}"
        )

    # 更新配置
    config = crud.update_user_agent_config(
        user_db, current_user.user_id, local_dir
    )

    return config


@router.delete("", response_model=BaseResponse)
def delete_agent_config(
    current_user = Depends(get_current_user),
    user_db: Session = Depends(get_user_db)
):
    """删除用户的 Agent 配置（不删除本地文件）"""
    success = crud.delete_user_agent_config(user_db, current_user.user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent 配置不存在")
    return BaseResponse(message="配置已删除")
