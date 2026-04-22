from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator, field_serializer, field_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(default="", max_length=4000)


class Attachment(BaseModel):
    type: Literal["image"] = "image"
    base64: str = Field(min_length=1)
    filename: str | None = None
    mime_type: str | None = None


class AgentChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    thinking: bool = Field(default=True)
    session_id: str | None = Field(default=None, max_length=64)
    attachments: list[Attachment] = Field(default_factory=list)

    @field_validator("thinking", mode="before")
    @classmethod
    def default_thinking(cls, v):
        # 如果未提供或为空，默认启用深度思考
        if v is None or v == "":
            return True
        return bool(v)

    @model_validator(mode="after")
    def validate_payload(self):
        has_user_text = any((m.role == "user" and m.content.strip()) for m in self.messages)
        has_attachments = len(self.attachments) > 0
        if not has_user_text and not has_attachments:
            raise ValueError("messages 中至少需要一条有效 user 消息，或提供 attachments")
        return self


class PendingActionItem(BaseModel):
    action_id: str
    tool_name: str
    summary: str
    status: str
    payload: dict
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime) -> str:
        return dt.isoformat()


class AgentMessageItem(BaseModel):
    role: str
    content: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime) -> str:
        return dt.isoformat()


class AgentChatData(BaseModel):
    session_id: str
    response: str
    pending_actions: list[PendingActionItem]
    tool_events: list["ToolEventItem"] = Field(default_factory=list)
    memory_hits: list[str] = Field(default_factory=list)


class ToolEventItem(BaseModel):
    event_id: str
    tool_name: str
    phase: Literal["started", "completed", "failed"]
    summary: str
    payload_preview: dict | None = None
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime) -> str:
        return dt.isoformat()


class AgentApproveRequest(BaseModel):
    action_id: str
    decision: Literal["approve", "edit", "reject"]
    edited_data: dict | None = None


class AgentApproveData(BaseModel):
    action_id: str
    status: str
    result: str
