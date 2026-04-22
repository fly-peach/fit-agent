"""工具护栏：拦截用户消息中的高风险指令，标记需审批的工具调用。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


GuardDecision = Literal["allow", "guard", "deny"]


@dataclass
class GuardResult:
    decision: GuardDecision
    reason: str


class ToolGuard:
    """工具护栏 — 可配置 deny/guard 模式匹配。

    Args:
        deny_patterns: 命中则直接拒绝（如 SQL 注入、危险命令）
        guard_patterns: 命中则进入审批流程（如写入、越权）
    """

    _DENY_PATTERNS = ("drop table", "truncate table", "delete from", "rm -rf", "管理员密码")
    _WRITE_TOOLS = {"update_daily_metrics", "update_workout_plan", "update_nutrition"}

    def __init__(
        self,
        deny_patterns: tuple[str, ...] | None = None,
        guard_patterns: tuple[str, ...] | None = None,
    ):
        self.deny_patterns = deny_patterns or self._DENY_PATTERNS
        self.guard_patterns = guard_patterns or ()

    def inspect_user_message(self, message: str) -> GuardResult:
        lower = (message or "").lower()
        if any(x in lower for x in self.deny_patterns):
            return GuardResult(decision="deny", reason="命中高风险指令，已阻止执行")
        return GuardResult(decision="allow", reason="通过")

    def inspect_tool_call(self, tool_name: str) -> GuardResult:
        if tool_name in self._WRITE_TOOLS:
            return GuardResult(decision="guard", reason="写操作必须审批")
        return GuardResult(decision="allow", reason="通过")
