"""统一的测试预期结构 — 所有 Task 的 ground_truth 通过此模型定义。"""
from pydantic import BaseModel, Field
from typing import Optional


class TaskGroundTruth(BaseModel):
    """统一的测试预期结构，所有字段均为可选，按场景组合使用"""

    # 工具调用场景
    expected_tools: list[str] = Field(default_factory=list)
    expected_params: dict = Field(default_factory=dict)
    expected_pending: bool = False

    # 安全场景
    blocked: bool = False
    no_tool_called: bool = False

    # 响应内容场景
    response_contains: list[str] = Field(default_factory=list)
    ai_should_not: list[str] = Field(default_factory=list)

    # 记忆场景
    memory_extracted: bool = False
    memory_content: Optional[str] = None
    memory_used: bool = False
    expected_memory_used: list[str] = Field(default_factory=list)

    # 多轮对话
    context_aware: bool = False

    def has_expectations(self) -> bool:
        """至少应有一个非默认值的预期字段"""
        return any([
            self.expected_tools, self.expected_params, self.expected_pending,
            self.blocked, self.no_tool_called, self.response_contains,
            self.ai_should_not, self.memory_extracted, self.memory_used,
            self.expected_memory_used, self.context_aware,
        ])
