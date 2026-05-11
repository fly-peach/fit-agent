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


# === New schemas for API Key and Prompt Templates ===

class SetApiKeyRequest(BaseModel):
    """设置 API Key 请求"""
    api_key: str = Field(..., description="API Key")


class ApiKeyStatusResponse(BaseModel):
    """API Key 状态响应"""
    has_api_key: bool = Field(..., description="是否已设置 API Key")


class PromptTemplatesResponse(BaseModel):
    """提示词模板响应"""
    agents_md: str = Field(default="", description="agents.md 内容")
    soul_md: str = Field(default="", description="soul.md 内容")
    updated_at: datetime | None = Field(default=None, description="更新时间")


class UpdatePromptsRequest(BaseModel):
    """更新提示词模板请求"""
    agents_md: str | None = Field(default=None, description="agents.md 内容")
    soul_md: str | None = Field(default=None, description="soul.md 内容")


class AgentConfigStatusV2(BaseModel):
    """新配置状态响应"""
    has_api_key: bool = Field(default=False, description="是否已设置 API Key")
    has_prompts: bool = Field(default=False, description="是否已配置提示词模板")
