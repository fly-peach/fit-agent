"""Agent configuration schemas"""
from datetime import datetime
from pydantic import BaseModel, Field


class UserAgentConfigBase(BaseModel):
    """Base schema for agent config"""
    local_working_dir: str = Field(default="", description="用户本地 Agent 工作目录路径")


class UserAgentConfigCreate(UserAgentConfigBase):
    """Schema for creating agent config"""
    pass


class UserAgentConfigUpdate(BaseModel):
    """Schema for updating agent config"""
    local_working_dir: str = Field(default="", description="用户本地 Agent 工作目录路径")


class UserAgentConfigResponse(BaseModel):
    """Schema for agent config response"""
    id: int
    user_id: int
    local_working_dir: str
    last_used_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentConfigStatus(BaseModel):
    """Schema for checking if user has agent configured"""
    is_configured: bool = Field(default=False, description="是否已配置 Agent")
    local_working_dir: str | None = Field(default=None, description="配置的本地目录")
