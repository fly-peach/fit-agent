"""FitAgent — 统一智能体入口，六层 Harness 通过构造参数注入。"""
import asyncio
import threading
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional

from agentscope.agent import ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.message import Msg, TextBlock, ImageBlock
from agentscope.model import OpenAIChatModel
from agentscope.tool import Toolkit, ToolResponse

from app.agent.schemas.harness import (
    ModelConfig, ToolRegistry, GuardConfig,
    ApprovalConfig, MemoryConfig, RecoveryConfig, EvalConfig,
)
from app.agent.schemas.agent import (
    AgentChatRequest, AgentChatData, PendingActionItem,
    ToolEventItem, ChatMessage, Attachment,
)
from app.agent.runtime.stream_tracker import StreamTracker
from app.agent.runtime.stream_parser import format_sse_event
from app.agent.runtime.react_agent import RogersReActRuntime
from app.agent.guard.tool_guard import ToolGuard
from app.agent.memory.memory_manager import MemoryManager
from app.agent.guard.approval_service import ApprovalService
from app.repositories.agent_repository import AgentRepository
from app.repositories.agent_memory_repository import AgentMemoryRepository
from app.repositories.agent_compression_event_repository import AgentCompressionEventRepository
from app.repositories.agent_offload_repository import AgentOffloadRepository
from app.repositories.daily_metrics_repository import DailyMetricsRepository
from app.repositories.daily_nutrition_repository import DailyNutritionRepository
from app.repositories.daily_workout_plan_repository import DailyWorkoutPlanRepository
from app.repositories.user_repository import UserRepository
from app.services.dashboard_service import DashboardService
from app.core.config import settings
from app.models.user import User


_STREAM_TRACKER = StreamTracker()


def _format_iso(dt: datetime) -> str:
    return dt.astimezone(datetime.now().astimezone().tzinfo).isoformat()


class FitAgent:
    """统一智能体入口。六层 Harness 能力通过构造参数注入。

    使用方式：
        agent = FitAgent(
            db=db,
            model=ModelConfig(...),
            tools=ToolRegistry(...),
            guard=GuardConfig(...),
            approval=ApprovalConfig(...),
            memory=MemoryConfig(...),
            recovery=RecoveryConfig(...),
        )
        result = agent.chat(current_user=user, payload=request)
    """

    def __init__(
        self,
        *,
        db,
        model: ModelConfig,
        tools: ToolRegistry,
        guard: GuardConfig,
        approval: ApprovalConfig,
        memory: MemoryConfig,
        recovery: RecoveryConfig,
        eval: Optional[EvalConfig] = None,
        system_prompt: Optional[str] = None,
    ):
        # 依赖注入
        self.db = db
        self.model_config = model
        self.tool_registry = tools
        self.guard_config = guard
        self.approval_config = approval
        self.memory_config = memory
        self.recovery_config = recovery
        self.eval_config = eval

        # 仓储层
        self.repo = AgentRepository(db)
        self.user_repo = UserRepository(db)
        self.daily_metrics_repo = DailyMetricsRepository(db)
        self.daily_workout_repo = DailyWorkoutPlanRepository(db)
        self.daily_nutrition_repo = DailyNutritionRepository(db)
        self.memory_repo = AgentMemoryRepository(db)
        self.offload_repo = AgentOffloadRepository(db)
        self.compression_event_repo = AgentCompressionEventRepository(db)

        # Layer 1: 运行时
        self.runtime = RogersReActRuntime()

        # Layer 3: 护栏 & 审批
        self.tool_guard = ToolGuard(
            deny_patterns=guard.deny_patterns,
            guard_patterns=guard.guard_patterns,
        )
        self.approval_service = ApprovalService(
            repo=self.repo,
            daily_metrics_repo=self.daily_metrics_repo,
            daily_workout_repo=self.daily_workout_repo,
            daily_nutrition_repo=self.daily_nutrition_repo,
            memory_repo=self.memory_repo,
        )

        # Layer 4: 记忆管理
        from app.agent.memory import AutoContextConfig, AutoContextMemory, AutoContextStorage, CompressionDispatcher, TokenCounter
        self.memory_manager = MemoryManager(self.memory_repo)
        self.auto_context_memory = None  # 延迟初始化

        # Layer 5: 流式追踪
        self.stream_tracker = _STREAM_TRACKER
        self.dashboard_service = DashboardService(db)

        # 系统提示词
        self.system_prompt = system_prompt or self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        return (
            "你是 Rogers 健身平台 AI 教练。优先根据用户数据与长期偏好给出简洁建议。"
            "涉及数据写入时，调用对应的 update 工具。"
            "所有写入工具都有 approved 参数，默认值为 false。"
            "你不得主动将 approved 设为 true。"
        )

    # ===== Layer 1 + 2: Agent Loop + Tool Mediation =====

    def _build_agentscope_agent(self, *, user: User, session_id: str) -> ReActAgent:
        """基于模型配置和工具注册表构建 ReActAgent"""
        model_kwargs: dict = {
            "model_name": self.model_config.model_name,
            "api_key": self.model_config.api_key,
        }
        if self.model_config.enable_thinking:
            model_kwargs["generate_kwargs"] = {"extra_body": {"enable_thinking": True}}
        if self.model_config.base_url:
            model_kwargs["client_kwargs"] = {"base_url": self.model_config.base_url}

        toolkit = Toolkit()

        # 注册读取工具
        for name, func in self.tool_registry.tools.items():
            toolkit.register_tool_function(func)

        # 注册写入工具（带审批拦截）
        for tool_name in self.tool_registry.write_tools:
            if tool_name not in self.tool_registry.tools:
                toolkit.register_tool_function(
                    self._make_pending_handler(tool_name, user, session_id),
                )

        return ReActAgent(
            name="FitAgent",
            sys_prompt=self.system_prompt,
            model=OpenAIChatModel(**model_kwargs),
            formatter=OpenAIChatFormatter(promote_tool_result_images=True),
            toolkit=toolkit,
        )

    def _make_pending_handler(self, tool_name: str, user: User, session_id: str):
        """为写入工具创建 pending-action 处理器"""
        type_map = self.approval_config.tool_type_map
        prefix = self.approval_config.pending_prefix
        id_len = self.approval_config.pending_id_length

        def handler(**kwargs):
            if kwargs.get("approved") is True:
                return ToolResponse(
                    content=[TextBlock(type="text", text="⚠️ approved=true 应由系统设置")]
                )
            action = self.repo.create_pending_action(
                action_id=f"{prefix}{uuid4().hex[:id_len]}",
                session_id=session_id,
                user_id=user.id,
                tool_name=tool_name,
                summary=f"更新 {kwargs.get('record_date', '未知日期')} 的 {type_map.get(tool_name, '数据')}",
                payload=kwargs,
            )
            return ToolResponse(
                content=[TextBlock(type="text", text=f"⏸️ 操作已挂起：等待审批（{action.summary}）")]
            )
        return handler

    # ===== Layer 3: Guard & Approval =====

    def approve(self, *, current_user: User, payload) -> dict:
        """审批决策"""
        return self.approval_service.approve(current_user=current_user, payload=payload)

    def list_pending(self, *, current_user: User) -> list[PendingActionItem]:
        """列出待审批操作"""
        rows = self.repo.list_pending_actions(user_id=current_user.id, limit=50)
        return [
            PendingActionItem(
                action_id=r.id, tool_name=r.tool_name, summary=r.summary,
                status=r.status, payload=r.payload, created_at=r.created_at,
            )
            for r in rows
        ]

    # ===== Layer 4: Context Governance =====

    def _compress_if_needed(self, messages, session_id: str, user_id: int, run_id: str):
        """上下文压缩"""
        if not self.memory_config.enable_auto_compress:
            return messages
        compressed, _ = self.auto_context_memory.compress_messages(
            messages=messages, session_id=session_id, user_id=user_id, run_id=run_id,
        )
        return compressed

    def _search_memory(self, user_id: int, query: str) -> list:
        """记忆检索"""
        return self.memory_manager.search(
            user_id=user_id, query=query, top_k=self.memory_config.memory_top_k,
        )

    # ===== Internal helpers =====

    def _ensure_session(self, *, user_id: int, session_id: str | None) -> str:
        if session_id:
            existing = self.repo.get_session(session_id=session_id, user_id=user_id)
            if existing:
                return existing.id
        new_id = f"sess_{uuid4().hex[:16]}"
        self.repo.create_session(session_id=new_id, user_id=user_id)
        return new_id

    @staticmethod
    def _extract_history(messages: list[ChatMessage]) -> tuple[list[ChatMessage], str]:
        if not messages:
            return [], ""
        latest_user = ""
        for msg in reversed(messages):
            if msg.role == "user" and msg.content.strip():
                latest_user = msg.content.strip()
                break
        if not latest_user:
            return messages, ""
        history = messages[:-1] if messages[-1].role == "user" and messages[-1].content.strip() == latest_user else messages
        return history, latest_user

    def _yield_tracked(self, *, run_id: str, last_seq: int):
        """追踪式流式输出回放"""
        cursor = last_seq
        while True:
            batch = self.stream_tracker.replay_from(run_id=run_id, last_seq=cursor)
            for item in batch:
                cursor = max(cursor, item.sequence_number)
                yield format_sse_event(item.event, item.data)
            if self.stream_tracker.is_done(run_id=run_id):
                if not batch:
                    break
                continue
            if not batch:
                waited = self.stream_tracker.wait_next(
                    run_id=run_id, last_seq=cursor,
                    timeout_seconds=self.recovery_config.stream_timeout_seconds,
                )
                for item in waited:
                    cursor = max(cursor, item.sequence_number)
                    yield format_sse_event(item.event, item.data)

    # ===== Public API =====

    def chat(self, *, current_user: User, payload: AgentChatRequest) -> AgentChatData:
        """同步对话入口"""
        session_id = self._ensure_session(user_id=current_user.id, session_id=payload.session_id)
        history, msg = self._extract_history(payload.messages)
        msg = msg.strip()

        # Layer 3: Guard
        guard_result = self.tool_guard.inspect_user_message(msg)
        if guard_result.decision == "deny":
            self.repo.create_message(session_id=session_id, user_id=current_user.id, role="user", content=msg or "[空消息]")
            self.repo.create_message(session_id=session_id, user_id=current_user.id, role="assistant", content=f"检测到高风险请求：{guard_result.reason}。")
            return AgentChatData(
                session_id=session_id,
                response=f"检测到高风险请求：{guard_result.reason}。",
                pending_actions=[], tool_events=[], memory_hits=[],
            )

        # Layer 4: Memory
        memory_saved = self.memory_manager.maybe_store_user_memory(user_id=current_user.id, message=msg)
        memory_hits = self._search_memory(user_id=current_user.id, query=msg)
        memory_context = self.memory_manager.build_context(
            user_id=current_user.id, query=msg, top_k=self.memory_config.memory_top_k,
        )

        self.repo.create_message(session_id=session_id, user_id=current_user.id, role="user", content=msg or "[空消息]")

        # Layer 1: Build & run agent
        agent = self._build_agentscope_agent(user=current_user, session_id=session_id)
        agent.set_msg_queue_enabled(True)

        user_msg = Msg("user", msg, "user")
        full_reply = ""
        pending_items: list[PendingActionItem] = []
        tool_events: list[ToolEventItem] = []
        sent_tool_uses: set[str] = set()

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            task = loop.create_task(agent(user_msg))

            while True:
                if task.done() and (agent.msg_queue is None or agent.msg_queue.empty()):
                    break
                if agent.msg_queue is None:
                    continue
                try:
                    queue_item = loop.run_until_complete(asyncio.wait_for(agent.msg_queue.get(), timeout=0.2))
                except asyncio.TimeoutError:
                    continue

                msg_obj, _last, _speech = queue_item
                blocks = msg_obj.get_content_blocks() or []

                full_text = "".join(
                    b.get("text", "") for b in blocks if isinstance(b.get("text"), str) and b.get("text")
                )
                if full_text:
                    full_reply = full_text

                for block in msg_obj.get_content_blocks("tool_use") or []:
                    tool_name = block.get("name")
                    tool_input = block.get("input", {})
                    tool_output = block.get("output")
                    key = f"{tool_name}::{tool_input}"
                    if key in sent_tool_uses:
                        continue
                    sent_tool_uses.add(key)

                    if str(tool_name) in self.tool_registry.write_tools:
                        action_id = f"act_{uuid4().hex[:12]}"
                        type_map = self.approval_config.tool_type_map
                        action = self.repo.create_pending_action(
                            action_id=action_id,
                            session_id=session_id,
                            user_id=current_user.id,
                            tool_name=str(tool_name),
                            summary=f"更新 {tool_input.get('record_date', '未知日期')} 的 {type_map.get(str(tool_name), '数据')}",
                            payload=tool_input,
                        )
                        pending = PendingActionItem(
                            action_id=action.id, tool_name=action.tool_name,
                            summary=action.summary, status=action.status,
                            payload=action.payload, created_at=action.created_at,
                        )
                        pending_items.append(pending)

                    tool_events.append(ToolEventItem(
                        event_id=f"evt_{uuid4().hex[:12]}",
                        tool_name=str(tool_name or "tool"),
                        phase="completed",
                        summary="工具调用完成",
                        payload_preview={"input": tool_input, "output": tool_output},
                        created_at=datetime.now(datetime.now().astimezone().tzinfo),
                    ))

            loop.run_until_complete(task)
        finally:
            agent.set_msg_queue_enabled(False)
            loop.close()

        if memory_saved:
            full_reply += "\n\n我已记住你刚才提供的长期偏好/事实，后续建议会参考它。"

        self.repo.create_message(session_id=session_id, user_id=current_user.id, role="assistant", content=full_reply)

        return AgentChatData(
            session_id=session_id,
            response=full_reply,
            pending_actions=pending_items,
            tool_events=tool_events,
            memory_hits=memory_hits,
        )

    def chat_stream(self, *, current_user: User, payload: AgentChatRequest, reconnect: bool = False, run_id: str = None, last_seq: int = 0):
        """流式对话入口"""
        session_id = self._ensure_session(user_id=current_user.id, session_id=payload.session_id)

        if reconnect:
            yield from self._yield_tracked(run_id=run_id, last_seq=last_seq)
            return

        next_run_id = self.stream_tracker.create_run(session_id=session_id, user_id=current_user.id)
        payload_data = payload.model_dump()

        thread = threading.Thread(
            target=self._produce_stream,
            kwargs={
                "current_user": current_user,
                "payload_data": payload_data,
                "session_id": session_id,
                "run_id": next_run_id,
            },
            daemon=True,
        )
        thread.start()
        yield from self._yield_tracked(run_id=next_run_id, last_seq=last_seq)

    def _produce_stream(self, *, current_user: User, payload_data: dict, session_id: str, run_id: str):
        """流式输出核心逻辑 — 暂委托给 AgentService._produce_stream 实现"""
        # 后续阶段将此逻辑完全迁移到 FitAgent
        from app.agent.service.agent_service import AgentService, _stream_worker
        service = AgentService(self.db)
        yield from service.chat_stream(
            current_user=current_user,
            payload=AgentChatRequest.model_validate(payload_data),
            reconnect=False,
            run_id=run_id,
            last_seq=0,
        )

    # ===== Session / History Management =====

    def list_sessions(self, *, current_user: User) -> list[dict]:
        rows = self.repo.list_sessions(user_id=current_user.id, limit=100)
        return [{"session_id": r.id, "title": r.title, "updated_at": r.updated_at} for r in rows]

    def list_history(self, *, current_user: User, session_id: str, format: str = "plain") -> list[dict]:
        session = self.repo.get_session(session_id=session_id, user_id=current_user.id)
        if session is None:
            return []
        if format == "runtime":
            rows = self.repo.list_events(session_id=session_id, user_id=current_user.id, limit=500)
            return [r.payload for r in rows]
        rows = self.repo.list_messages(session_id=session_id, user_id=current_user.id, limit=200)
        return [
            {"role": r.role, "content": r.content, "reasoning": r.reasoning,
             "tool_uses": r.tool_uses, "created_at": r.created_at}
            for r in rows
        ]

    def delete_session(self, *, current_user: User, session_id: str) -> bool:
        return self.repo.delete_session(session_id=session_id, user_id=current_user.id)
