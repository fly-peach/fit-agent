"""Tool Approval System

Provides approval workflow for database write tool calls:
- ApprovalManager: manages pending approvals with asyncio.Event
- ContextVars: session/user/queue propagation via contextvars
- create_approval_wrapper: wraps write tools to intercept and await approval

Rejection rules:
- Pure reject → "用户拒绝该工具继续调用，请检查工具使用是否使用合理"
- 2nd consecutive reject of same tool → "用户拒绝该工具继续调用，不得使用该工具"
- Reject with user input → "用户拒绝该工具继续调用，请检查工具使用是否使用合理，用户提示：{input}"
- Approval resets the consecutive rejection counter for that tool
"""
import asyncio
import uuid
import logging
import functools
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Optional

from agentscope.tool import ToolResponse
from agentscope.message import Msg, TextBlock

logger = logging.getLogger(__name__)

# ── Write tool identifiers ────────────────────────────────────────────────

WRITE_TOOL_NAMES = {"execute_fitme_command", "record_user_fact", "delete_user_fact_tool"}

WRITE_FITME_COMMANDS = {
    "create-health-metric", "create-training-plan", "create-diet-meal",
    "create-custom-food", "delete-custom-food",
    "create-custom-exercise", "update-custom-exercise", "delete-custom-exercise",
}


# ── Approval Request ──────────────────────────────────────────────────────

@dataclass
class ApprovalRequest:
    approval_id: str
    session_id: str
    tool_name: str
    tool_args_display: str
    event: asyncio.Event = field(default_factory=asyncio.Event)
    approved: bool = False
    rejection_input: str = ""


# ── Approval Manager (singleton via module-level instance) ────────────────

class ToolApprovalManager:
    def __init__(self):
        self._pending: dict[str, ApprovalRequest] = {}
        # (session_id, tool_name) → consecutive rejection count
        self._tool_rejection_count: dict[tuple[str, str], int] = {}

    def create_approval(self, session_id: str, tool_name: str, tool_args_display: str) -> str:
        approval_id = str(uuid.uuid4())
        req = ApprovalRequest(
            approval_id=approval_id,
            session_id=session_id,
            tool_name=tool_name,
            tool_args_display=tool_args_display,
        )
        self._pending[approval_id] = req
        logger.info("Approval created: id=%s tool=%s session=%s", approval_id, tool_name, session_id)
        return approval_id

    def approve(self, approval_id: str) -> bool:
        req = self._pending.pop(approval_id, None)
        if req is None:
            logger.warning("Approval not found: %s", approval_id)
            return False
        req.approved = True
        req.event.set()
        # Reset consecutive rejection count
        key = (req.session_id, req.tool_name)
        self._tool_rejection_count.pop(key, None)
        logger.info("Approval approved: id=%s tool=%s", approval_id, req.tool_name)
        return True

    def reject(self, approval_id: str, input_text: str = "") -> bool:
        req = self._pending.pop(approval_id, None)
        if req is None:
            logger.warning("Rejection not found: %s", approval_id)
            return False
        req.approved = False
        req.rejection_input = input_text
        req.event.set()
        # Track consecutive rejections
        key = (req.session_id, req.tool_name)
        count = self._tool_rejection_count.get(key, 0) + 1
        self._tool_rejection_count[key] = count
        logger.info("Approval rejected: id=%s tool=%s (consecutive=%d)",
                     approval_id, req.tool_name, count)
        return True

    async def wait_for_decision(self, approval_id: str, timeout: float = 120) -> tuple[bool, str]:
        req = self._pending.get(approval_id)
        if req is None:
            return False, ""
        try:
            await asyncio.wait_for(req.event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("Approval timed out: id=%s", approval_id)
            self._pending.pop(approval_id, None)
            return False, ""
        return req.approved, req.rejection_input

    def get_pending(self) -> dict[str, ApprovalRequest]:
        return self._pending


# Module-level singleton
_manager: ToolApprovalManager | None = None


def get_approval_manager() -> ToolApprovalManager:
    global _manager
    if _manager is None:
        _manager = ToolApprovalManager()
    return _manager


# ── Session Context (ContextVars) ─────────────────────────────────────────

_current_session_id: ContextVar[str] = ContextVar("_current_session_id", default="")
_current_user_id: ContextVar[int | None] = ContextVar("_current_user_id", default=None)
_auto_approve_enabled: ContextVar[bool] = ContextVar("_auto_approve_enabled", default=False)
_approval_queue: ContextVar[asyncio.Queue | None] = ContextVar("_approval_queue", default=None)


def set_session_context(
    session_id: str,
    user_id: int | None = None,
    auto_approve: bool = False,
    queue: asyncio.Queue | None = None,
):
    _current_session_id.set(session_id)
    _current_user_id.set(user_id)
    _auto_approve_enabled.set(auto_approve)
    _approval_queue.set(queue)


def clear_session_context():
    _current_session_id.set("")
    _current_user_id.set(None)
    _auto_approve_enabled.set(False)
    _approval_queue.set(None)


# ── Helpers ───────────────────────────────────────────────────────────────

def _is_write_fitme_command(command: str) -> bool:
    cmd = command.strip().split()[0] if command.strip() else ""
    return cmd in WRITE_FITME_COMMANDS


def _format_args_for_display(tool_name: str, args: tuple, kwargs: dict) -> str:
    parts = []
    for a in args:
        if isinstance(a, str) and len(a) > 100:
            parts.append(a[:100] + "...")
        else:
            parts.append(str(a))
    for k, v in kwargs.items():
        if k in ("auth_token", "api_key"):
            continue
        v_str = str(v)
        if len(v_str) > 100:
            v_str = v_str[:100] + "..."
        parts.append(f"{k}={v_str}")
    return ", ".join(parts)


def _build_rejection_msg(tool_name: str, rejection_input: str, reject_count: int) -> str:
    if reject_count >= 2:
        return "用户拒绝该工具继续调用，不得使用该工具"
    if rejection_input:
        return f"用户拒绝该工具继续调用，请检查工具使用是否使用合理，用户提示：{rejection_input}"
    return "用户拒绝该工具继续调用，请检查工具使用是否使用合理"


def _build_approval_msg(approval_id: str, tool_name: str, tool_args_display: str) -> Msg:
    return Msg(
        name="System",
        content=f"工具 {tool_name} 请求编辑数据库，等待您的审批...",
        role="system",
        metadata={
            "tool_approval": {
                "approval_id": approval_id,
                "tool_name": tool_name,
                "tool_args_display": tool_args_display,
                "status": "pending",
            }
        },
    )


# ── Tool Wrapper ──────────────────────────────────────────────────────────

def create_approval_wrapper(tool_fn, tool_name: str):
    """Wrap a write tool function with approval logic.

    For execute_fitme_command, only write sub-commands (POST/PUT/DELETE)
    trigger approval; GET sub-commands pass through directly.
    """
    manager = get_approval_manager()

    @functools.wraps(tool_fn)
    async def wrapper(*args, **kwargs):
        session_id = _current_session_id.get()
        auto_approve = _auto_approve_enabled.get(False)
        queue = _approval_queue.get(None)

        if tool_name == "execute_fitme_command":
            command = kwargs.get("command") or (args[0] if args else "")
            if not _is_write_fitme_command(command):
                return await tool_fn(*args, **kwargs)

        logger.info(f"=== Tool call intercepted: {tool_name}, auto_approve={auto_approve} ===")
        if auto_approve:
            logger.info(f"Auto-approve enabled, skipping approval for {tool_name}")
            return await tool_fn(*args, **kwargs)

        tool_args_display = _format_args_for_display(tool_name, args, kwargs)
        approval_id = manager.create_approval(session_id, tool_name, tool_args_display)
        logger.info(f"Created approval request: {approval_id} for {tool_name}")

        if queue is not None:
            approval_msg = _build_approval_msg(approval_id, tool_name, tool_args_display)
            logger.info(f"Putting approval message to queue: {approval_msg}")
            await queue.put(approval_msg)
            logger.info(f"Approval message enqueued successfully")
            # 关键：给事件循环一个机会，让审批消息可以被 yield 出去
            await asyncio.sleep(0.1)

        logger.info(f"Waiting for user decision on approval: {approval_id}")
        approved, rejection_input = await manager.wait_for_decision(approval_id, timeout=120)
        logger.info(f"Approval decision received: approved={approved}, id={approval_id}")

        if approved:
            key = (session_id, tool_name)
            manager._tool_rejection_count.pop(key, None)
            return await tool_fn(*args, **kwargs)
        else:
            key = (session_id, tool_name)
            reject_count = manager._tool_rejection_count.get(key, 0)
            msg = _build_rejection_msg(tool_name, rejection_input, reject_count)
            return ToolResponse(content=[TextBlock(type="text", text=msg)])

    wrapper.__name__ = f"wrapped_{tool_name}"
    wrapper.__qualname__ = f"wrapped_{tool_name}"
    return wrapper
